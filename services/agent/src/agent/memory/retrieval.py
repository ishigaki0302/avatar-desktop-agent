"""Memory retrieval (Phase 13).

Ranks long-term memories for a query by a weighted blend of:
  final = WR*relevance + WC*recency + WI*importance
where relevance is cosine similarity over (pluggable) embeddings. Embeddings are
cached per memory in `memory_embeddings`. Retrieved memories can be logged to
memory_access_logs and formatted for prompt injection.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

from agent.logger.db import connect
from agent.memory.embeddings import get_embedder

# Runtime import (not TYPE_CHECKING): pydantic resolves `Memory` as a field type at runtime.
from agent.memory.store import Memory  # noqa: TC001

if TYPE_CHECKING:
    from pathlib import Path

    from agent.logger.interaction_logger import InteractionLogger
    from agent.memory.embeddings import Embedder
    from agent.memory.store import MemoryStore, Task

_WEIGHT_RELEVANCE = 0.6
_WEIGHT_RECENCY = 0.2
_WEIGHT_IMPORTANCE = 0.2
_RECENCY_HALF_LIFE_DAYS = 14.0
_IMPORTANCE_MAX = 5
_CANDIDATE_LIMIT = 500
_DEFAULT_TOP_K = 5
_SECONDS_PER_DAY = 86_400.0

_CREATE_EMBEDDINGS = """
CREATE TABLE IF NOT EXISTS memory_embeddings (
  memory_id TEXT PRIMARY KEY,
  dim       INTEGER NOT NULL,
  vector    TEXT NOT NULL
)
"""


def _cosine(a: list[float], b: list[float]) -> float:
    # Embedders return normalized vectors, so the dot product is the cosine.
    return sum(x * y for x, y in zip(a, b, strict=False))


class ScoredMemory(BaseModel):
    """A memory with its retrieval scores."""

    memory: Memory
    relevance: float
    recency: float
    importance: float
    final: float


class MemoryRetriever:
    """Embedding-based retrieval over the long-term memory store."""

    def __init__(self, db_path: Path, store: MemoryStore, embedder: Embedder | None = None) -> None:
        self._db_path = db_path
        self._store = store
        self._embedder = embedder if embedder is not None else get_embedder()
        with closing(connect(db_path)) as conn, conn:
            conn.execute(_CREATE_EMBEDDINGS)

    def retrieve(
        self,
        query: str,
        *,
        limit: int = _DEFAULT_TOP_K,
        min_score: float = 0.0,
        logger: InteractionLogger | None = None,
        turn_id: str | None = None,
    ) -> list[ScoredMemory]:
        memories = self._store.search_memories(limit=_CANDIDATE_LIMIT)
        if not memories:
            return []

        vectors = self._ensure_embeddings(memories)
        query_vec = self._embedder.embed([query])[0]
        now = datetime.now(tz=UTC)

        scored: list[ScoredMemory] = []
        for memory in memories:
            relevance = max(0.0, _cosine(query_vec, vectors[memory.id]))
            recency = self._recency(memory.updated_at, now)
            importance = memory.importance / _IMPORTANCE_MAX
            final = _WEIGHT_RELEVANCE * relevance + _WEIGHT_RECENCY * recency + _WEIGHT_IMPORTANCE * importance
            if final >= min_score:
                scored.append(
                    ScoredMemory(
                        memory=memory,
                        relevance=relevance,
                        recency=recency,
                        importance=importance,
                        final=final,
                    ),
                )

        scored.sort(key=lambda s: s.final, reverse=True)
        top = scored[:limit]

        if logger is not None and turn_id is not None:
            for sm in top:
                logger.log_memory_access(
                    turn_id,
                    "read",
                    memory_id=sm.memory.id,
                    relevance_score=sm.relevance,
                    recency_score=sm.recency,
                    importance_score=sm.importance,
                    final_score=sm.final,
                    reason="retrieved for query",
                )
        return top

    @staticmethod
    def _recency(updated_at: str, now: datetime) -> float:
        try:
            updated = datetime.fromisoformat(updated_at)
        except ValueError:
            return 0.0
        age_days = max(0.0, (now - updated).total_seconds() / _SECONDS_PER_DAY)
        return 0.5 ** (age_days / _RECENCY_HALF_LIFE_DAYS)

    def _ensure_embeddings(self, memories: list[Memory]) -> dict[str, list[float]]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute("SELECT memory_id, vector FROM memory_embeddings").fetchall()
        cached: dict[str, list[float]] = {row["memory_id"]: json.loads(row["vector"]) for row in rows}

        missing = [m for m in memories if m.id not in cached]
        if missing:
            new_vectors = self._embedder.embed([m.content for m in missing])
            with closing(connect(self._db_path)) as conn, conn:
                for memory, vec in zip(missing, new_vectors, strict=True):
                    conn.execute(
                        "INSERT OR REPLACE INTO memory_embeddings (memory_id, dim, vector) VALUES (?, ?, ?)",
                        (memory.id, len(vec), json.dumps(vec)),
                    )
                    cached[memory.id] = vec
        return cached


def build_context(scored: list[ScoredMemory], tasks: list[Task] | None = None) -> str:
    """Format retrieved memories (+ open tasks) for system-prompt injection."""
    lines: list[str] = []
    if scored:
        lines.append("# 関連する記憶")
        lines.extend(f"- {sm.memory.content}" for sm in scored)
    if tasks:
        if lines:
            lines.append("")
        lines.append("# 現在のタスク")
        lines.extend(f"- [{task.status}] {task.title}" for task in tasks)
    return "\n".join(lines)
