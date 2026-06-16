"""FastAPI entry point for the avatar-agent backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel

from agent.config import settings
from agent.logger.interaction_logger import (
    AvatarEventLog,
    InteractionLogger,
    MemoryAccessLog,
    PromptLog,
    Session,
    ToolCallLog,
    TurnLog,
)

app = FastAPI(title="avatar-agent", version="0.1.0")


@lru_cache
def get_logger() -> InteractionLogger:
    """Return the process-wide interaction logger (created on first use)."""
    return InteractionLogger(Path(settings.storage_dir) / "app.sqlite")


LoggerDep = Annotated[InteractionLogger, Depends(get_logger)]


class StartSessionRequest(BaseModel):
    model: str | None = None
    title: str | None = None
    app_version: str | None = None


class LogTurnRequest(BaseModel):
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


class EndSessionRequest(BaseModel):
    summary: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe. Returns the active model so the UI can display it."""
    return {"status": "ok", "model": settings.ollama_model}


@app.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(req: StartSessionRequest, logger: LoggerDep) -> Session:
    return logger.start_session(model=req.model, title=req.title, app_version=req.app_version)


@app.get("/sessions")
def list_sessions(logger: LoggerDep) -> list[Session]:
    return logger.list_sessions()


@app.get("/sessions/{session_id}")
def get_session(session_id: str, logger: LoggerDep) -> Session:
    session = logger.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return session


@app.post("/sessions/{session_id}/turns", status_code=status.HTTP_201_CREATED)
def log_turn(session_id: str, req: LogTurnRequest, logger: LoggerDep) -> TurnLog:
    return logger.log_turn(
        session_id,
        user_input=req.user_input,
        assistant_output=req.assistant_output,
        raw_assistant_output=req.raw_assistant_output,
        model=req.model,
        prompt_tokens=req.prompt_tokens,
        completion_tokens=req.completion_tokens,
        latency_ms=req.latency_ms,
        emotion=req.emotion,
        motion=req.motion,
        status=req.status,
        error=req.error,
    )


@app.get("/sessions/{session_id}/turns")
def get_turns(session_id: str, logger: LoggerDep) -> list[TurnLog]:
    return logger.get_turns(session_id)


@app.post("/sessions/{session_id}/end")
def end_session(session_id: str, req: EndSessionRequest, logger: LoggerDep) -> Session:
    logger.end_session(session_id, summary=req.summary)
    session = logger.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return session


# ── Phase 10: read prompt / tool / memory-access / avatar logs for a turn ──────
# Writes happen in-process via InteractionLogger while a turn is being answered;
# these endpoints expose the records for inspection and the dashboard (Phase 16).


@app.get("/turns/{turn_id}/prompts")
def get_prompts(turn_id: str, logger: LoggerDep) -> list[PromptLog]:
    return logger.get_prompts(turn_id)


@app.get("/turns/{turn_id}/tool-calls")
def get_tool_calls(turn_id: str, logger: LoggerDep) -> list[ToolCallLog]:
    return logger.get_tool_calls(turn_id)


@app.get("/turns/{turn_id}/memory-accesses")
def get_memory_accesses(turn_id: str, logger: LoggerDep) -> list[MemoryAccessLog]:
    return logger.get_memory_accesses(turn_id)


@app.get("/turns/{turn_id}/avatar-events")
def get_avatar_events(turn_id: str, logger: LoggerDep) -> list[AvatarEventLog]:
    return logger.get_avatar_events(turn_id)
