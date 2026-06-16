"""Dashboard aggregation (Phase 16).

Read-only views over all logged data: session overviews, per-turn detail
(feedback / analytics / tool calls / memory accesses), full-text search across
turns, a dissatisfaction list, and overall stats. Pure SQLite aggregation.
"""

from __future__ import annotations

from contextlib import closing
from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.analytics.store import AnalyticsStore, InferredFeedbackLog
from agent.logger.db import connect
from agent.logger.interaction_logger import (
    ExplicitFeedbackLog,
    InteractionLogger,
    MemoryAccessLog,
    Session,
    ToolCallLog,
    TurnLog,
)

if TYPE_CHECKING:
    from pathlib import Path

_DISSATISFACTION_THRESHOLD = 0.5
_DEFAULT_SEARCH_LIMIT = 50
_DEFAULT_DISSATISFACTION_LIMIT = 50

_SESSION_OVERVIEWS = """
SELECT
  s.id, s.title, s.started_at, s.ended_at, s.model,
  COUNT(t.id) AS turn_count,
  AVG(t.latency_ms) AS avg_latency_ms,
  (SELECT AVG(i.predicted_satisfaction)
     FROM inferred_feedback_logs i
     JOIN turn_logs t2 ON i.turn_id = t2.id
    WHERE t2.session_id = s.id) AS avg_satisfaction
FROM sessions s
LEFT JOIN turn_logs t ON t.session_id = s.id
GROUP BY s.id
ORDER BY s.started_at DESC
"""

_SEARCH_TURNS = """
SELECT * FROM turn_logs
WHERE user_input LIKE ? OR assistant_output LIKE ?
ORDER BY timestamp DESC
LIMIT ?
"""

_DISSATISFACTION = """
SELECT t.id AS turn_id, t.session_id, t.user_input,
       i.predicted_satisfaction, i.issue_type, i.evidence
FROM turn_logs t
JOIN inferred_feedback_logs i ON i.turn_id = t.id
WHERE i.issue_type IS NOT NULL OR i.predicted_satisfaction < ?
ORDER BY i.created_at DESC
LIMIT ?
"""


class SessionOverview(BaseModel):
    """One row of the session list with rollup stats."""

    id: str
    title: str | None = None
    started_at: str
    ended_at: str | None = None
    model: str | None = None
    turn_count: int
    avg_latency_ms: float | None = None
    avg_satisfaction: float | None = None


class TurnDetail(BaseModel):
    """A turn with everything logged about it."""

    turn: TurnLog
    explicit_feedback: list[ExplicitFeedbackLog]
    inferred_feedback: list[InferredFeedbackLog]
    tool_calls: list[ToolCallLog]
    memory_accesses: list[MemoryAccessLog]


class SessionDetail(BaseModel):
    """A session and its fully-detailed turns."""

    session: Session
    turns: list[TurnDetail]


class DissatisfactionEntry(BaseModel):
    """A turn flagged as a likely dissatisfaction point."""

    turn_id: str
    session_id: str | None = None
    user_input: str | None = None
    predicted_satisfaction: float | None = None
    issue_type: str | None = None
    evidence: str | None = None


class DashboardStats(BaseModel):
    """Overall rollup across all sessions."""

    session_count: int
    turn_count: int
    avg_latency_ms: float | None = None
    avg_satisfaction: float | None = None
    issue_type_counts: dict[str, int]
    rating_counts: dict[str, int]
    tool_call_count: int
    tool_success_rate: float | None = None
    memory_access_count: int


class Dashboard:
    """Aggregated, read-only views over the logged data."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        # Ensure all referenced tables exist even if nothing has been logged yet.
        self._logger = InteractionLogger(db_path)
        self._analytics = AnalyticsStore(db_path)

    def list_sessions(self) -> list[SessionOverview]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(_SESSION_OVERVIEWS).fetchall()
        return [SessionOverview(**dict(row)) for row in rows]

    def session_detail(self, session_id: str) -> SessionDetail | None:
        session = self._logger.get_session(session_id)
        if session is None:
            return None
        turns = [
            TurnDetail(
                turn=turn,
                explicit_feedback=self._logger.get_feedback(turn.id),
                inferred_feedback=self._analytics.get_for_turn(turn.id),
                tool_calls=self._logger.get_tool_calls(turn.id),
                memory_accesses=self._logger.get_memory_accesses(turn.id),
            )
            for turn in self._logger.get_turns(session_id)
        ]
        return SessionDetail(session=session, turns=turns)

    def search_turns(self, query: str, *, limit: int = _DEFAULT_SEARCH_LIMIT) -> list[TurnLog]:
        like = f"%{query}%"
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(_SEARCH_TURNS, (like, like, limit)).fetchall()
        return [TurnLog(**dict(row)) for row in rows]

    def dissatisfaction(self, *, limit: int = _DEFAULT_DISSATISFACTION_LIMIT) -> list[DissatisfactionEntry]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(_DISSATISFACTION, (_DISSATISFACTION_THRESHOLD, limit)).fetchall()
        return [DissatisfactionEntry(**dict(row)) for row in rows]

    def stats(self) -> DashboardStats:
        with closing(connect(self._db_path)) as conn:
            session_count = conn.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()["n"]
            turn_row = conn.execute(
                "SELECT COUNT(*) AS n, AVG(latency_ms) AS lat FROM turn_logs",
            ).fetchone()
            avg_sat = conn.execute(
                "SELECT AVG(predicted_satisfaction) AS s FROM inferred_feedback_logs",
            ).fetchone()["s"]
            rating_rows = conn.execute(
                "SELECT rating, COUNT(*) AS n FROM explicit_feedback_logs WHERE rating IS NOT NULL GROUP BY rating",
            ).fetchall()
            tool_row = conn.execute(
                "SELECT COUNT(*) AS total, SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) AS ok FROM tool_call_logs",
            ).fetchone()
            mem_count = conn.execute("SELECT COUNT(*) AS n FROM memory_access_logs").fetchone()["n"]

        total_tools = tool_row["total"]
        return DashboardStats(
            session_count=session_count,
            turn_count=turn_row["n"],
            avg_latency_ms=turn_row["lat"],
            avg_satisfaction=avg_sat,
            issue_type_counts=self._analytics.issue_type_counts(),
            rating_counts={str(row["rating"]): row["n"] for row in rating_rows},
            tool_call_count=total_tools,
            tool_success_rate=(tool_row["ok"] / total_tools) if total_tools else None,
            memory_access_count=mem_count,
        )
