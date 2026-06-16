"""FastAPI entry point for the avatar-agent backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel

from agent.config import settings
from agent.logger.interaction_logger import (
    AvatarEventLog,
    ExplicitFeedbackLog,
    InteractionLogger,
    MemoryAccessLog,
    PromptLog,
    Session,
    ToolCallLog,
    TurnLog,
)
from agent.memory.profile import ProfileStore
from agent.memory.retrieval import MemoryRetriever, ScoredMemory, build_context
from agent.memory.store import Memory, MemoryStore, MemoryType, Task, TaskStatus

app = FastAPI(title="avatar-agent", version="0.1.0")


@lru_cache
def get_logger() -> InteractionLogger:
    """Return the process-wide interaction logger (created on first use)."""
    return InteractionLogger(Path(settings.storage_dir) / "app.sqlite")


LoggerDep = Annotated[InteractionLogger, Depends(get_logger)]


@lru_cache
def get_memory_store() -> MemoryStore:
    """Return the process-wide long-term memory store (created on first use)."""
    return MemoryStore(Path(settings.storage_dir) / "app.sqlite")


MemoryStoreDep = Annotated[MemoryStore, Depends(get_memory_store)]


@lru_cache
def get_profile_store() -> ProfileStore:
    """Return the process-wide profile store (storage/memory/profile.md)."""
    return ProfileStore(Path(settings.storage_dir) / "memory" / "profile.md")


ProfileStoreDep = Annotated[ProfileStore, Depends(get_profile_store)]


@lru_cache
def get_retriever() -> MemoryRetriever:
    """Return the process-wide memory retriever (created on first use)."""
    return MemoryRetriever(Path(settings.storage_dir) / "app.sqlite", get_memory_store())


RetrieverDep = Annotated[MemoryRetriever, Depends(get_retriever)]


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


class FeedbackRequest(BaseModel):
    rating: int | None = None
    label: str | None = None
    comment: str | None = None


class CreateMemoryRequest(BaseModel):
    type: MemoryType
    content: str
    source: str | None = None
    importance: int = 3
    metadata: dict[str, object] | None = None


class UpdateMemoryRequest(BaseModel):
    content: str | None = None
    importance: int | None = None
    source: str | None = None
    metadata: dict[str, object] | None = None


class CreateTaskRequest(BaseModel):
    title: str
    status: TaskStatus = "todo"
    due_date: str | None = None
    content: str | None = None


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    status: TaskStatus | None = None
    due_date: str | None = None
    content: str | None = None


class ProfileRequest(BaseModel):
    content: str


class RetrieveRequest(BaseModel):
    query: str
    limit: int = 5
    min_score: float = 0.0
    turn_id: str | None = None


class RetrieveResponse(BaseModel):
    results: list[ScoredMemory]
    context: str


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


# ── Phase 11: explicit feedback ────────────────────────────────────────────────


@app.post("/turns/{turn_id}/feedback", status_code=status.HTTP_201_CREATED)
def post_feedback(turn_id: str, req: FeedbackRequest, logger: LoggerDep) -> ExplicitFeedbackLog:
    return logger.log_explicit_feedback(
        turn_id,
        rating=req.rating,
        label=req.label,
        comment=req.comment,
    )


@app.get("/turns/{turn_id}/feedback")
def get_feedback(turn_id: str, logger: LoggerDep) -> list[ExplicitFeedbackLog]:
    return logger.get_feedback(turn_id)


# ── Phase 12: long-term memory (memories / tasks / profile) ────────────────────


@app.post("/memories", status_code=status.HTTP_201_CREATED)
def create_memory(req: CreateMemoryRequest, store: MemoryStoreDep) -> Memory:
    return store.add_memory(
        req.type,
        req.content,
        source=req.source,
        importance=req.importance,
        metadata=req.metadata,
    )


@app.get("/memories")
def search_memories(
    store: MemoryStoreDep,
    q: str | None = None,
    memory_type: Annotated[MemoryType | None, Query(alias="type")] = None,
    limit: int = 20,
) -> list[Memory]:
    return store.search_memories(q, memory_type=memory_type, limit=limit)


@app.get("/memories/{memory_id}")
def get_memory(memory_id: str, store: MemoryStoreDep) -> Memory:
    memory = store.get_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="memory not found")
    return memory


@app.patch("/memories/{memory_id}")
def update_memory(memory_id: str, req: UpdateMemoryRequest, store: MemoryStoreDep) -> Memory:
    updated = store.update_memory(
        memory_id,
        content=req.content,
        importance=req.importance,
        source=req.source,
        metadata=req.metadata,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="memory not found")
    return updated


@app.post("/memories/{memory_id}/supersede")
def supersede_memory(memory_id: str, store: MemoryStoreDep) -> Memory:
    store.supersede_memory(memory_id)
    memory = store.get_memory(memory_id)
    if memory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="memory not found")
    return memory


@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(req: CreateTaskRequest, store: MemoryStoreDep) -> Task:
    return store.add_task(req.title, status=req.status, due_date=req.due_date, content=req.content)


@app.get("/tasks")
def list_tasks(
    store: MemoryStoreDep,
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
) -> list[Task]:
    return store.list_tasks(status=task_status)


@app.patch("/tasks/{task_id}")
def update_task(task_id: str, req: UpdateTaskRequest, store: MemoryStoreDep) -> Task:
    updated = store.update_task(
        task_id,
        title=req.title,
        status=req.status,
        due_date=req.due_date,
        content=req.content,
    )
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return updated


@app.get("/profile")
def get_profile(profile: ProfileStoreDep) -> dict[str, str]:
    return {"content": profile.read()}


@app.put("/profile")
def put_profile(req: ProfileRequest, profile: ProfileStoreDep) -> dict[str, str]:
    profile.write(req.content)
    return {"content": profile.read()}


# ── Phase 13: memory retrieval ─────────────────────────────────────────────────


@app.post("/retrieve")
def retrieve_memories(
    req: RetrieveRequest,
    store: MemoryStoreDep,
    retriever: RetrieverDep,
    logger: LoggerDep,
) -> RetrieveResponse:
    results = retriever.retrieve(
        req.query,
        limit=req.limit,
        min_score=req.min_score,
        logger=logger if req.turn_id else None,
        turn_id=req.turn_id,
    )
    open_tasks = [*store.list_tasks(status="todo"), *store.list_tasks(status="in_progress")]
    return RetrieveResponse(results=results, context=build_context(results, open_tasks))
