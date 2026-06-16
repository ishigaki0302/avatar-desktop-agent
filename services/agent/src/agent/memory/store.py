"""Long-term memory store: memories + tasks (Phase 12).

v1 uses SQLite with keyword (substring) search ordered by importance and
recency. Vector / embedding search and relevance·recency·importance scoring are
deferred to Phase 13 (Memory Retrieval); `embedding_id` is reserved for that.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from agent.logger.db import connect  # shared SQLite connection helper
from agent.memory.db import init_memory_db

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

MemoryType = Literal["semantic", "episodic", "procedural", "archival"]
TaskStatus = Literal["todo", "in_progress", "done", "blocked", "cancelled"]

_IMPORTANCE_MIN = 1
_IMPORTANCE_MAX = 5
_DEFAULT_IMPORTANCE = 3
_DEFAULT_SEARCH_LIMIT = 20

_INSERT_MEMORY = """
INSERT INTO memories
  (id, type, content, source, importance, created_at, updated_at,
   last_accessed_at, embedding_id, metadata, superseded)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
"""

# Fixed query with optional filters handled via `? IS NULL OR ...` (no dynamic SQL).
_SEARCH_MEMORIES = """
SELECT * FROM memories
WHERE (? IS NULL OR type = ?)
  AND (? IS NULL OR content LIKE ?)
  AND (superseded = 0 OR ? = 1)
ORDER BY importance DESC, updated_at DESC
LIMIT ?
"""

_UPDATE_MEMORY = """
UPDATE memories SET
  content = COALESCE(?, content),
  importance = COALESCE(?, importance),
  source = COALESCE(?, source),
  metadata = COALESCE(?, metadata),
  updated_at = ?
WHERE id = ?
"""

_INSERT_TASK = """
INSERT INTO tasks (id, title, status, due_date, content, created_at, updated_at)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""

_UPDATE_TASK = """
UPDATE tasks SET
  title = COALESCE(?, title),
  status = COALESCE(?, status),
  due_date = COALESCE(?, due_date),
  content = COALESCE(?, content),
  updated_at = ?
WHERE id = ?
"""


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _new_id() -> str:
    return uuid4().hex


class Memory(BaseModel):
    """A unit of long-term memory (semantic/episodic/procedural/archival)."""

    id: str
    type: MemoryType
    content: str
    source: str | None = None
    importance: int = Field(default=_DEFAULT_IMPORTANCE, ge=_IMPORTANCE_MIN, le=_IMPORTANCE_MAX)
    created_at: str
    updated_at: str
    last_accessed_at: str | None = None
    embedding_id: str | None = None
    metadata: dict[str, object] | None = None
    superseded: bool = False


class Task(BaseModel):
    """A tracked task / todo with a lifecycle status."""

    id: str
    title: str
    status: TaskStatus = "todo"
    due_date: str | None = None
    content: str | None = None
    created_at: str
    updated_at: str


def _row_to_memory(row: sqlite3.Row) -> Memory:
    data = dict(row)
    raw_metadata = data.pop("metadata", None)
    data["metadata"] = json.loads(raw_metadata) if raw_metadata else None
    data["superseded"] = bool(data["superseded"])
    return Memory(**data)


class MemoryStore:
    """Long-term memory storage backed by SQLite (memories + tasks)."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        with closing(connect(db_path)) as conn:
            init_memory_db(conn)

    # ── Memories ───────────────────────────────────────────────────────────────

    def add_memory(
        self,
        memory_type: MemoryType,
        content: str,
        *,
        source: str | None = None,
        importance: int = _DEFAULT_IMPORTANCE,
        metadata: dict[str, object] | None = None,
    ) -> Memory:
        now = _now_iso()
        memory = Memory(
            id=_new_id(),
            type=memory_type,
            content=content,
            source=source,
            importance=importance,
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_MEMORY,
                (
                    memory.id,
                    memory.type,
                    memory.content,
                    memory.source,
                    memory.importance,
                    memory.created_at,
                    memory.updated_at,
                    memory.last_accessed_at,
                    memory.embedding_id,
                    json.dumps(metadata) if metadata is not None else None,
                ),
            )
        return memory

    def get_memory(self, memory_id: str) -> Memory | None:
        with closing(connect(self._db_path)) as conn:
            row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        return _row_to_memory(row) if row is not None else None

    def search_memories(
        self,
        query: str | None = None,
        *,
        memory_type: MemoryType | None = None,
        include_superseded: bool = False,
        limit: int = _DEFAULT_SEARCH_LIMIT,
    ) -> list[Memory]:
        like = f"%{query}%" if query else None
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                _SEARCH_MEMORIES,
                (memory_type, memory_type, query, like, int(include_superseded), limit),
            ).fetchall()
        return [_row_to_memory(row) for row in rows]

    def update_memory(
        self,
        memory_id: str,
        *,
        content: str | None = None,
        importance: int | None = None,
        source: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> Memory | None:
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _UPDATE_MEMORY,
                (
                    content,
                    importance,
                    source,
                    json.dumps(metadata) if metadata is not None else None,
                    _now_iso(),
                    memory_id,
                ),
            )
        return self.get_memory(memory_id)

    def supersede_memory(self, memory_id: str) -> None:
        """Mark a memory as superseded (kept for history, hidden from search)."""
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                "UPDATE memories SET superseded = 1, updated_at = ? WHERE id = ?",
                (_now_iso(), memory_id),
            )

    # ── Tasks ──────────────────────────────────────────────────────────────────

    def add_task(
        self,
        title: str,
        *,
        status: TaskStatus = "todo",
        due_date: str | None = None,
        content: str | None = None,
    ) -> Task:
        now = _now_iso()
        task = Task(
            id=_new_id(),
            title=title,
            status=status,
            due_date=due_date,
            content=content,
            created_at=now,
            updated_at=now,
        )
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _INSERT_TASK,
                (task.id, task.title, task.status, task.due_date, task.content, task.created_at, task.updated_at),
            )
        return task

    def get_task(self, task_id: str) -> Task | None:
        with closing(connect(self._db_path)) as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return Task(**dict(row)) if row is not None else None

    def list_tasks(self, *, status: TaskStatus | None = None) -> list[Task]:
        with closing(connect(self._db_path)) as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE (? IS NULL OR status = ?) ORDER BY created_at DESC",
                (status, status),
            ).fetchall()
        return [Task(**dict(row)) for row in rows]

    def update_task(
        self,
        task_id: str,
        *,
        title: str | None = None,
        status: TaskStatus | None = None,
        due_date: str | None = None,
        content: str | None = None,
    ) -> Task | None:
        with closing(connect(self._db_path)) as conn, conn:
            conn.execute(
                _UPDATE_TASK,
                (title, status, due_date, content, _now_iso(), task_id),
            )
        return self.get_task(task_id)
