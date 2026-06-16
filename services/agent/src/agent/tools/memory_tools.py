"""Memory tools: search / write over the long-term memory store (Phase 17)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent.memory.store import MemoryStore, MemoryType

_DEFAULT_SEARCH_LIMIT = 10
_DEFAULT_IMPORTANCE = 3


class MemoryTools:
    """Thin tool wrapper over MemoryStore (returns JSON-able dicts)."""

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    def search(
        self,
        query: str,
        memory_type: MemoryType | None = None,
        limit: int = _DEFAULT_SEARCH_LIMIT,
    ) -> list[dict[str, object]]:
        memories = self._store.search_memories(query, memory_type=memory_type, limit=limit)
        return [m.model_dump() for m in memories]

    def write(
        self,
        content: str,
        memory_type: MemoryType = "semantic",
        importance: int = _DEFAULT_IMPORTANCE,
    ) -> dict[str, object]:
        return self._store.add_memory(memory_type, content, source="tool", importance=importance).model_dump()
