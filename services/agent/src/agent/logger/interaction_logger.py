"""Interaction logging store backed by SQLite (Phase 9).

Persists every session and turn verbatim — chat, casual talk, opinions, and
complaints alike. This is the raw Interaction Log; promotion into long-term
memory happens elsewhere.
"""

from __future__ import annotations

from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

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

_INSERT_PROMPT = """
INSERT INTO prompt_logs
  (id, turn_id, system_prompt, memory_context, recent_context, tool_context,
   final_prompt, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
"""

_INSERT_TOOL_CALL = """
INSERT INTO tool_call_logs
  (id, turn_id, tool_name, input_json, output_json, status, latency_ms, error,
   created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_INSERT_MEMORY_ACCESS = """
INSERT INTO memory_access_logs
  (id, turn_id, memory_id, access_type, relevance_score, recency_score,
   importance_score, final_score, reason, created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_INSERT_AVATAR_EVENT = """
INSERT INTO avatar_event_logs
  (id, turn_id, emotion, motion, tts_enabled, tts_text, started_at, ended_at,
   created_at)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

_INSERT_FEEDBACK = """
INSERT INTO explicit_feedback_logs
  (id, turn_id, rating, label, comment, created_at)
VALUES (?, ?, ?, ?, ?, ?)
"""

AccessType = Literal["read", "write", "update", "delete", "supersede"]

_RATING_MIN = 1
_RATING_MAX = 5


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


class PromptLog(BaseModel):
    """How a turn's prompt was assembled (system + memory + recent + tools)."""

    id: str
    turn_id: str
    system_prompt: str | None = None
    memory_context: str | None = None
    recent_context: str | None = None
    tool_context: str | None = None
    final_prompt: str | None = None
    created_at: str


class ToolCallLog(BaseModel):
    """A single tool invocation made while answering a turn."""

    id: str
    turn_id: str
    tool_name: str
    input_json: str | None = None
    output_json: str | None = None
    status: str = "ok"
    latency_ms: int | None = None
    error: str | None = None
    created_at: str


class MemoryAccessLog(BaseModel):
    """A memory read/write/update made while answering a turn."""

    id: str
    turn_id: str
    memory_id: str | None = None
    access_type: AccessType
    relevance_score: float | None = None
    recency_score: float | None = None
    importance_score: float | None = None
    final_score: float | None = None
    reason: str | None = None
    created_at: str


class AvatarEventLog(BaseModel):
    """An avatar expression / TTS event emitted for a turn."""

    id: str
    turn_id: str
    emotion: str | None = None
    motion: str | None = None
    tts_enabled: bool | None = None
    tts_text: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    created_at: str


class ExplicitFeedbackLog(BaseModel):
    """User-supplied feedback on a turn (👍/👎 plus optional label/comment)."""

    id: str
    turn_id: str
    rating: int | None = Field(default=None, ge=_RATING_MIN, le=_RATING_MAX)
    label: str | None = None
    comment: str | None = None
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

    # ── Phase 10: prompt / tool / memory-access / avatar logs ──────────────────

    def log_prompt(
        self,
        turn_id: str,
        *,
        system_prompt: str | None = None,
        memory_context: str | None = None,
        recent_context: str | None = None,
        tool_context: str | None = None,
        final_prompt: str | None = None,
    ) -> PromptLog:
        log = PromptLog(
            id=_new_id(),
            turn_id=turn_id,
            system_prompt=system_prompt,
            memory_context=memory_context,
            recent_context=recent_context,
            tool_context=tool_context,
            final_prompt=final_prompt,
            created_at=_now_iso(),
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_PROMPT,
                (
                    log.id,
                    log.turn_id,
                    log.system_prompt,
                    log.memory_context,
                    log.recent_context,
                    log.tool_context,
                    log.final_prompt,
                    log.created_at,
                ),
            )
        return log

    def log_tool_call(
        self,
        turn_id: str,
        tool_name: str,
        *,
        input_json: str | None = None,
        output_json: str | None = None,
        status: str = "ok",
        latency_ms: int | None = None,
        error: str | None = None,
    ) -> ToolCallLog:
        log = ToolCallLog(
            id=_new_id(),
            turn_id=turn_id,
            tool_name=tool_name,
            input_json=input_json,
            output_json=output_json,
            status=status,
            latency_ms=latency_ms,
            error=error,
            created_at=_now_iso(),
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_TOOL_CALL,
                (
                    log.id,
                    log.turn_id,
                    log.tool_name,
                    log.input_json,
                    log.output_json,
                    log.status,
                    log.latency_ms,
                    log.error,
                    log.created_at,
                ),
            )
        return log

    def log_memory_access(
        self,
        turn_id: str,
        access_type: AccessType,
        *,
        memory_id: str | None = None,
        relevance_score: float | None = None,
        recency_score: float | None = None,
        importance_score: float | None = None,
        final_score: float | None = None,
        reason: str | None = None,
    ) -> MemoryAccessLog:
        log = MemoryAccessLog(
            id=_new_id(),
            turn_id=turn_id,
            memory_id=memory_id,
            access_type=access_type,
            relevance_score=relevance_score,
            recency_score=recency_score,
            importance_score=importance_score,
            final_score=final_score,
            reason=reason,
            created_at=_now_iso(),
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_MEMORY_ACCESS,
                (
                    log.id,
                    log.turn_id,
                    log.memory_id,
                    log.access_type,
                    log.relevance_score,
                    log.recency_score,
                    log.importance_score,
                    log.final_score,
                    log.reason,
                    log.created_at,
                ),
            )
        return log

    def log_avatar_event(
        self,
        turn_id: str,
        *,
        emotion: str | None = None,
        motion: str | None = None,
        tts_enabled: bool | None = None,
        tts_text: str | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
    ) -> AvatarEventLog:
        log = AvatarEventLog(
            id=_new_id(),
            turn_id=turn_id,
            emotion=emotion,
            motion=motion,
            tts_enabled=tts_enabled,
            tts_text=tts_text,
            started_at=started_at,
            ended_at=ended_at,
            created_at=_now_iso(),
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_AVATAR_EVENT,
                (
                    log.id,
                    log.turn_id,
                    log.emotion,
                    log.motion,
                    None if log.tts_enabled is None else int(log.tts_enabled),
                    log.tts_text,
                    log.started_at,
                    log.ended_at,
                    log.created_at,
                ),
            )
        return log

    def get_prompts(self, turn_id: str) -> list[PromptLog]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM prompt_logs WHERE turn_id = ? ORDER BY created_at",
                (turn_id,),
            ).fetchall()
        return [PromptLog(**dict(row)) for row in rows]

    def get_tool_calls(self, turn_id: str) -> list[ToolCallLog]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM tool_call_logs WHERE turn_id = ? ORDER BY created_at",
                (turn_id,),
            ).fetchall()
        return [ToolCallLog(**dict(row)) for row in rows]

    def get_memory_accesses(self, turn_id: str) -> list[MemoryAccessLog]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM memory_access_logs WHERE turn_id = ? ORDER BY created_at",
                (turn_id,),
            ).fetchall()
        return [MemoryAccessLog(**dict(row)) for row in rows]

    def get_avatar_events(self, turn_id: str) -> list[AvatarEventLog]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM avatar_event_logs WHERE turn_id = ? ORDER BY created_at",
                (turn_id,),
            ).fetchall()
        return [AvatarEventLog(**dict(row)) for row in rows]

    # ── Phase 11: explicit feedback ────────────────────────────────────────────

    def log_explicit_feedback(
        self,
        turn_id: str,
        *,
        rating: int | None = None,
        label: str | None = None,
        comment: str | None = None,
    ) -> ExplicitFeedbackLog:
        feedback = ExplicitFeedbackLog(
            id=_new_id(),
            turn_id=turn_id,
            rating=rating,
            label=label,
            comment=comment,
            created_at=_now_iso(),
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_FEEDBACK,
                (
                    feedback.id,
                    feedback.turn_id,
                    feedback.rating,
                    feedback.label,
                    feedback.comment,
                    feedback.created_at,
                ),
            )
        return feedback

    def get_feedback(self, turn_id: str) -> list[ExplicitFeedbackLog]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM explicit_feedback_logs WHERE turn_id = ? ORDER BY created_at",
                (turn_id,),
            ).fetchall()
        return [ExplicitFeedbackLog(**dict(row)) for row in rows]
