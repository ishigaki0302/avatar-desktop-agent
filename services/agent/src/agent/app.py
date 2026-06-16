"""FastAPI entry point for the avatar-agent backend."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agent.analytics.analyzer import Analyzer, LLMAnalyzer, RuleAnalyzer
from agent.analytics.store import AnalyticsStore, InferredFeedbackLog
from agent.config import settings
from agent.dashboard import (
    Dashboard,
    DashboardStats,
    DissatisfactionEntry,
    SessionDetail,
    SessionOverview,
)
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
from agent.memory.writer import LLMExtractor, MemoryWriter

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


@lru_cache
def get_memory_writer() -> MemoryWriter:
    """Return the process-wide memory writer (created on first use)."""
    return MemoryWriter(get_memory_store())


MemoryWriterDep = Annotated[MemoryWriter, Depends(get_memory_writer)]


@lru_cache
def get_analytics_store() -> AnalyticsStore:
    """Return the process-wide analytics store (created on first use)."""
    return AnalyticsStore(Path(settings.storage_dir) / "app.sqlite")


AnalyticsStoreDep = Annotated[AnalyticsStore, Depends(get_analytics_store)]


@lru_cache
def get_analyzer() -> Analyzer:
    """Return the configured analyzer (rule by default, ollama when requested)."""
    if settings.analytics_backend == "ollama":
        return LLMAnalyzer(settings.ollama_base_url, settings.ollama_model)
    return RuleAnalyzer()


AnalyzerDep = Annotated[Analyzer, Depends(get_analyzer)]


@lru_cache
def get_dashboard() -> Dashboard:
    """Return the process-wide dashboard aggregator (created on first use)."""
    return Dashboard(Path(settings.storage_dir) / "app.sqlite")


DashboardDep = Annotated[Dashboard, Depends(get_dashboard)]


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


class ExplicitWriteRequest(BaseModel):
    text: str
    turn_id: str | None = None


class ExtractRequest(BaseModel):
    conversation: str
    turn_id: str | None = None


class AnalyzeRequest(BaseModel):
    user_input: str
    latency_ms: int | None = None


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


# ── Phase 14: memory write / consolidation ─────────────────────────────────────


@app.post("/memory-write/explicit")
def write_explicit(req: ExplicitWriteRequest, writer: MemoryWriterDep, logger: LoggerDep) -> Memory | None:
    return writer.write_explicit(
        req.text,
        logger=logger if req.turn_id else None,
        turn_id=req.turn_id,
    )


@app.post("/memory-write/consolidate")
def consolidate_memories(writer: MemoryWriterDep) -> dict[str, int]:
    return {"merged": writer.consolidate_duplicates()}


@app.post("/memory-write/extract")
def extract_and_write(req: ExtractRequest, writer: MemoryWriterDep, logger: LoggerDep) -> list[Memory]:
    # Uses the LLM extractor (requires Ollama); returns [] best-effort if unavailable.
    extractor = LLMExtractor(settings.ollama_base_url, settings.ollama_model)
    ops = extractor.extract(req.conversation)
    return writer.apply(ops, logger=logger if req.turn_id else None, turn_id=req.turn_id)


# ── Phase 15: interaction analytics ────────────────────────────────────────────


@app.post("/turns/{turn_id}/analyze", status_code=status.HTTP_201_CREATED)
def analyze_turn(
    turn_id: str,
    req: AnalyzeRequest,
    analyzer: AnalyzerDep,
    analytics: AnalyticsStoreDep,
) -> InferredFeedbackLog:
    analysis = analyzer.analyze(req.user_input, latency_ms=req.latency_ms)
    return analytics.record(turn_id, analysis)


@app.get("/turns/{turn_id}/inferred-feedback")
def get_inferred_feedback(turn_id: str, analytics: AnalyticsStoreDep) -> list[InferredFeedbackLog]:
    return analytics.get_for_turn(turn_id)


@app.get("/analytics/issue-types")
def get_issue_type_counts(analytics: AnalyticsStoreDep) -> dict[str, int]:
    return analytics.issue_type_counts()


# ── Phase 16: dashboard (read-only aggregation + simple UI) ────────────────────


@app.get("/dashboard/sessions")
def dashboard_sessions(dashboard: DashboardDep) -> list[SessionOverview]:
    return dashboard.list_sessions()


@app.get("/dashboard/sessions/{session_id}")
def dashboard_session_detail(session_id: str, dashboard: DashboardDep) -> SessionDetail:
    detail = dashboard.session_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    return detail


@app.get("/dashboard/search")
def dashboard_search(dashboard: DashboardDep, q: str, limit: int = 50) -> list[TurnLog]:
    return dashboard.search_turns(q, limit=limit)


@app.get("/dashboard/dissatisfaction")
def dashboard_dissatisfaction(dashboard: DashboardDep, limit: int = 50) -> list[DissatisfactionEntry]:
    return dashboard.dissatisfaction(limit=limit)


@app.get("/dashboard/stats")
def dashboard_stats(dashboard: DashboardDep) -> DashboardStats:
    return dashboard.stats()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> str:
    return _DASHBOARD_HTML


_DASHBOARD_HTML = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>avatar-agent dashboard</title>
<style>
  body { font-family: system-ui, sans-serif; margin: 24px; max-width: 920px; color: #222; }
  h1 { font-size: 20px; } h2 { font-size: 16px; margin-top: 28px; }
  .stat { display: inline-block; background: #f0f4ff; border-radius: 8px; padding: 8px 12px; margin: 4px; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { border: 1px solid #ddd; padding: 6px 8px; text-align: left; }
  .bad { color: #c0392b; } input { padding: 6px; } button { padding: 6px 12px; }
</style>
</head>
<body>
<h1>avatar-agent dashboard</h1>
<div id="stats"></div>

<h2>セッション</h2>
<table id="sessions"><thead><tr>
  <th>started</th><th>model</th><th>turns</th><th>avg latency(ms)</th><th>avg satisfaction</th>
</tr></thead><tbody></tbody></table>

<h2>不満ログ</h2>
<table id="dissat"><thead><tr>
  <th>issue</th><th>satisfaction</th><th>user_input</th><th>evidence</th>
</tr></thead><tbody></tbody></table>

<h2>会話検索</h2>
<input id="q" placeholder="キーワード"><button id="searchBtn">検索</button>
<table id="results"><thead><tr><th>timestamp</th><th>user</th><th>assistant</th></tr></thead><tbody></tbody></table>

<script>
const fmt = (v) => (v == null ? "-" : (typeof v === "number" ? v.toFixed(2) : v));
async function getJSON(url) { const r = await fetch(url); return r.ok ? r.json() : null; }
function rows(tableId, items, cols) {
  const tb = document.querySelector(`#${tableId} tbody`);
  tb.innerHTML = "";
  for (const it of items) {
    const tr = document.createElement("tr");
    for (const c of cols) { const td = document.createElement("td"); td.textContent = fmt(it[c]); tr.appendChild(td); }
    tb.appendChild(tr);
  }
}
async function load() {
  const s = await getJSON("/dashboard/stats");
  if (s) {
    document.getElementById("stats").innerHTML =
      [["sessions", s.session_count], ["turns", s.turn_count],
       ["avg latency(ms)", fmt(s.avg_latency_ms)], ["avg satisfaction", fmt(s.avg_satisfaction)],
       ["tool success", fmt(s.tool_success_rate)], ["memory accesses", s.memory_access_count]]
      .map(([k, v]) => `<span class="stat">${k}: <b>${v}</b></span>`).join("") +
      "<div>issue types: " + JSON.stringify(s.issue_type_counts) + "</div>";
  }
  rows("sessions", (await getJSON("/dashboard/sessions")) || [],
       ["started_at", "model", "turn_count", "avg_latency_ms", "avg_satisfaction"]);
  rows("dissat", (await getJSON("/dashboard/dissatisfaction")) || [],
       ["issue_type", "predicted_satisfaction", "user_input", "evidence"]);
}
document.getElementById("searchBtn").addEventListener("click", async () => {
  const q = document.getElementById("q").value.trim();
  if (!q) return;
  rows("results", (await getJSON("/dashboard/search?q=" + encodeURIComponent(q))) || [],
       ["timestamp", "user_input", "assistant_output"]);
});
load();
</script>
</body>
</html>
"""
