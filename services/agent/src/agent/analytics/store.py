"""Persistence for inferred feedback (Phase 15)."""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel

from agent.analytics.db import init_analytics_db
from agent.logger.db import connect

if TYPE_CHECKING:
    from pathlib import Path

    from agent.analytics.analyzer import Analysis

_INSERT_INFERRED = """
INSERT INTO inferred_feedback_logs
  (id, turn_id, predicted_satisfaction, issue_type, issue_detail, evidence, confidence, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""


class InferredFeedbackLog(BaseModel):
    """A stored inference about a turn's satisfaction."""

    id: str
    turn_id: str
    predicted_satisfaction: float | None = None
    issue_type: str | None = None
    issue_detail: str | None = None
    evidence: str | None = None
    confidence: float | None = None
    created_at: str


class AnalyticsStore:
    """Stores and queries inferred feedback."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        with closing(connect(db_path)) as conn:
            init_analytics_db(conn)

    def record(self, turn_id: str, analysis: Analysis) -> InferredFeedbackLog:
        log = InferredFeedbackLog(
            id=uuid4().hex,
            turn_id=turn_id,
            predicted_satisfaction=analysis.predicted_satisfaction,
            issue_type=analysis.issue_type,
            issue_detail=analysis.issue_detail,
            evidence=analysis.evidence,
            confidence=analysis.confidence,
            created_at=datetime.now(tz=UTC).isoformat(),
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_INFERRED,
                (
                    log.id,
                    log.turn_id,
                    log.predicted_satisfaction,
                    log.issue_type,
                    log.issue_detail,
                    log.evidence,
                    log.confidence,
                    log.created_at,
                ),
            )
        return log

    def get_for_turn(self, turn_id: str) -> list[InferredFeedbackLog]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM inferred_feedback_logs WHERE turn_id = ? ORDER BY created_at",
                (turn_id,),
            ).fetchall()
        return [InferredFeedbackLog(**dict(row)) for row in rows]

    def issue_type_counts(self) -> dict[str, int]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT issue_type, COUNT(*) AS n FROM inferred_feedback_logs "
                "WHERE issue_type IS NOT NULL GROUP BY issue_type ORDER BY n DESC",
            ).fetchall()
        return {row["issue_type"]: row["n"] for row in rows}
