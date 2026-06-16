"""Interaction logging store backed by SQLite (Phase 9).

Persists every session and turn verbatim — chat, casual talk, opinions, and
complaints alike. This is the raw Interaction Log; promotion into long-term
memory happens elsewhere.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from pydantic import BaseModel

from agent.logger.db import connect, init_db

if TYPE_CHECKING:
    from pathlib import Path

_INSERT_SESSION = """
INSERT INTO sessions
  (id, title, started_at, ended_at, summary, model, app_version, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

_INSERT_TURN = """
INSERT INTO turn_logs
  (id, session_id, turn_index, timestamp, user_input, assistant_output,
   raw_assistant_output, model, prompt_tokens, completion_tokens, latency_ms,
   emotion, motion, status, error, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_NEXT_TURN_INDEX = "SELECT COALESCE(MAX(turn_index), -1) + 1 AS next FROM turn_logs WHERE session_id = ?"


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _new_id() -> str:
    return uuid4().hex


class Session(BaseModel):
    """A conversation session."""

    id: str
    title: str | None = None
    started_at: str
    ended_at: str | None = None
    summary: str | None = None
    model: str | None = None
    app_version: str | None = None
    created_at: str


class TurnLog(BaseModel):
    """A single user/assistant exchange within a session."""

    id: str
    session_id: str
    turn_index: int
    timestamp: str
    user_input: str | None = None
    assistant_output: str | None = None
    raw_assistant_output: str | None = None
    model: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int | None = None
    emotion: str | None = None
    motion: str | None = None
    status: str = "ok"
    error: str | None = None
    created_at: str


class InteractionLogger:
    """Append-only logger that persists sessions and turns to SQLite."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        with closing(connect(db_path)) as conn:
            init_db(conn)

    def start_session(
        self,
        model: str | None = None,
        title: str | None = None,
        app_version: str | None = None,
    ) -> Session:
        now = _now_iso()
        session = Session(
            id=_new_id(),
            title=title,
            started_at=now,
            model=model,
            app_version=app_version,
            created_at=now,
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_SESSION,
                (
                    session.id,
                    session.title,
                    session.started_at,
                    session.ended_at,
                    session.summary,
                    session.model,
                    session.app_version,
                    session.created_at,
                ),
            )
        return session

    def log_turn(
        self,
        session_id: str,
        *,
        user_input: str | None = None,
        assistant_output: str | None = None,
        raw_assistant_output: str | None = None,
        model: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        latency_ms: int | None = None,
        emotion: str | None = None,
        motion: str | None = None,
        status: str = "ok",
        error: str | None = None,
    ) -> TurnLog:
        now = _now_iso()
        with closing(connect(self._db_path)) as conn, conn:
            row = conn.execute(_NEXT_TURN_INDEX, (session_id,)).fetchone()
            turn = TurnLog(
                id=_new_id(),
                session_id=session_id,
                turn_index=int(row["next"]),
                timestamp=now,
                user_input=user_input,
                assistant_output=assistant_output,
                raw_assistant_output=raw_assistant_output,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
                emotion=emotion,
                motion=motion,
                status=status,
                error=error,
                created_at=now,
            )
            conn.execute(
                _INSERT_TURN,
                (
                    turn.id,
                    turn.session_id,
                    turn.turn_index,
                    turn.timestamp,
                    turn.user_input,
                    turn.assistant_output,
                    turn.raw_assistant_output,
                    turn.model,
                    turn.prompt_tokens,
                    turn.completion_tokens,
                    turn.latency_ms,
                    turn.emotion,
                    turn.motion,
                    turn.status,
                    turn.error,
                    turn.created_at,
                ),
            )
        return turn

    def end_session(self, session_id: str, summary: str | None = None) -> None:
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                "UPDATE sessions SET ended_at = ?, summary = COALESCE(?, summary) WHERE id = ?",
                (_now_iso(), summary, session_id),
            )

    def get_session(self, session_id: str) -> Session | None:
        with closing(connect(self._db_path)) as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return Session(**dict(row)) if row is not None else None

    def list_sessions(self) -> list[Session]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute("SELECT * FROM sessions ORDER BY started_at DESC").fetchall()
        return [Session(**dict(row)) for row in rows]

    def get_turns(self, session_id: str) -> list[TurnLog]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM turn_logs WHERE session_id = ? ORDER BY turn_index",
                (session_id,),
            ).fetchall()
        return [TurnLog(**dict(row)) for row in rows]
