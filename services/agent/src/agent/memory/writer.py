"""Memory write & consolidation (Phase 14).

Turns conversation into long-term memory:
- Hot path: explicit "覚えて" requests are saved immediately (deterministic).
- Background: a pluggable extractor proposes CREATE/UPDATE/DELETE/NOOP ops
  (LLMExtractor uses Ollama; inject a fake in tests). apply() executes them.
- Consolidation: near-duplicate memories are merged (older superseded).
All writes are recorded to memory_access_logs when a logger + turn_id are given.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

import httpx
from pydantic import BaseModel

from agent.memory.embeddings import get_embedder
from agent.memory.store import MemoryType  # noqa: TC001  (pydantic field type, resolved at runtime)

if TYPE_CHECKING:
    from agent.logger.interaction_logger import InteractionLogger
    from agent.memory.embeddings import Embedder
    from agent.memory.store import Memory, MemoryStore

_EXPLICIT_PATTERNS = (
    re.compile(r"覚え(て|とい?て|ておい?て|ておいて)"),
    re.compile(r"記憶し(て|ておいて)"),
    re.compile(r"メモし(て|ておいて)"),
)
_EXPLICIT_IMPORTANCE = 5
_DEDUP_THRESHOLD = 0.97
_MIN_MEMORIES_TO_DEDUP = 2
_EXTRACT_TIMEOUT_S = 60.0

Operation = Literal["CREATE", "UPDATE", "DELETE", "NOOP"]
_ACCESS_FOR_OP: dict[Operation, Literal["write", "update", "delete"]] = {
    "CREATE": "write",
    "UPDATE": "update",
    "DELETE": "delete",
}


class MemoryOperation(BaseModel):
    """A proposed change to long-term memory."""

    operation: Operation
    memory_type: MemoryType = "semantic"
    content: str = ""
    target_id: str | None = None
    reason: str | None = None


@runtime_checkable
class MemoryExtractor(Protocol):
    """Proposes memory operations from a conversation snippet."""

    def extract(self, conversation: str) -> list[MemoryOperation]: ...


def is_explicit_memory_request(text: str) -> bool:
    """True if the user explicitly asked to remember something."""
    return any(pattern.search(text) for pattern in _EXPLICIT_PATTERNS)


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=False))


class MemoryWriter:
    """Applies memory operations and consolidates duplicates."""

    def __init__(self, store: MemoryStore, embedder: Embedder | None = None) -> None:
        self._store = store
        self._embedder = embedder if embedder is not None else get_embedder()

    def write_explicit(
        self,
        text: str,
        *,
        logger: InteractionLogger | None = None,
        turn_id: str | None = None,
    ) -> Memory | None:
        """Hot path: save the user's text verbatim when they asked to remember it."""
        if not is_explicit_memory_request(text):
            return None
        memory = self._store.add_memory(
            "semantic",
            text.strip(),
            source="explicit",
            importance=_EXPLICIT_IMPORTANCE,
        )
        self._log(logger, turn_id, "write", memory.id, "explicit memory request")
        return memory

    def apply(
        self,
        operations: list[MemoryOperation],
        *,
        logger: InteractionLogger | None = None,
        turn_id: str | None = None,
    ) -> list[Memory]:
        """Execute extractor-proposed operations; returns created/updated memories."""
        applied: list[Memory] = []
        for op in operations:
            memory = self._apply_one(op)
            if memory is not None:
                applied.append(memory)
            access = _ACCESS_FOR_OP.get(op.operation)
            target = memory.id if memory is not None else op.target_id
            if access is not None and target is not None:
                self._log(logger, turn_id, access, target, op.reason)
        return applied

    def _apply_one(self, op: MemoryOperation) -> Memory | None:
        if op.operation == "CREATE" and op.content:
            return self._store.add_memory(op.memory_type, op.content, source="extracted")
        if op.operation == "UPDATE" and op.target_id:
            return self._store.update_memory(op.target_id, content=op.content or None)
        if op.operation == "DELETE" and op.target_id:
            self._store.supersede_memory(op.target_id)
        return None

    def consolidate_duplicates(self, *, threshold: float = _DEDUP_THRESHOLD) -> int:
        """Supersede near-duplicate memories, keeping the most recent of each pair."""
        memories = self._store.search_memories(limit=500)
        if len(memories) < _MIN_MEMORIES_TO_DEDUP:
            return 0
        vectors = self._embedder.embed([m.content for m in memories])
        # Most recent first so we keep the newest and supersede older duplicates.
        order = sorted(range(len(memories)), key=lambda i: memories[i].updated_at, reverse=True)
        kept: list[int] = []
        merged = 0
        for i in order:
            if any(_cosine(vectors[i], vectors[k]) >= threshold for k in kept):
                self._store.supersede_memory(memories[i].id)
                merged += 1
            else:
                kept.append(i)
        return merged

    def _log(
        self,
        logger: InteractionLogger | None,
        turn_id: str | None,
        access_type: Literal["write", "update", "delete"],
        memory_id: str,
        reason: str | None,
    ) -> None:
        if logger is not None and turn_id is not None:
            logger.log_memory_access(turn_id, access_type, memory_id=memory_id, reason=reason)


class LLMExtractor:
    """Extracts memory operations via Ollama (opt-in; requires a running model)."""

    _SYSTEM = (
        "会話から長期記憶に保存すべき情報を抽出する。"
        'JSON 配列のみを返す。各要素は {"operation":"CREATE|UPDATE|DELETE|NOOP",'
        '"memory_type":"semantic|episodic|procedural|archival","content":"...",'
        '"reason":"..."}。保存価値がなければ [] を返す。'
    )

    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url
        self._model = model

    def extract(self, conversation: str) -> list[MemoryOperation]:
        try:
            res = httpx.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "format": "json",
                    "messages": [
                        {"role": "system", "content": self._SYSTEM},
                        {"role": "user", "content": conversation},
                    ],
                },
                timeout=_EXTRACT_TIMEOUT_S,
            )
            res.raise_for_status()
            content = res.json()["message"]["content"]
            parsed = json.loads(content)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError):
            return []
        items = parsed if isinstance(parsed, list) else parsed.get("operations", [])
        ops: list[MemoryOperation] = []
        for item in items:
            try:
                ops.append(MemoryOperation.model_validate(item))
            except ValueError:
                # Skip malformed items, keep the rest.
                continue
        return ops
