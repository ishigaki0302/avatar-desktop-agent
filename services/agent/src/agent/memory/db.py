"""SQLite schema for long-term memory (Phase 12).

Memories and tasks live in the same app.sqlite as the interaction logs so that
memory_access_logs can reference a memory id. Profile is a separate Markdown
document (see profile.py) representing the user's current state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

_MEMORY_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
  id               TEXT PRIMARY KEY,
  type             TEXT NOT NULL,
  content          TEXT NOT NULL,
  source           TEXT,
  importance       INTEGER NOT NULL DEFAULT 3,
  created_at       TEXT NOT NULL,
  updated_at       TEXT NOT NULL,
  last_accessed_at TEXT,
  embedding_id     TEXT,
  metadata         TEXT,
  superseded       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_memories_type ON memories (type);

CREATE TABLE IF NOT EXISTS tasks (
  id         TEXT PRIMARY KEY,
  title      TEXT NOT NULL,
  status     TEXT NOT NULL DEFAULT 'todo',
  due_date   TEXT,
  content    TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);
"""


def init_memory_db(conn: sqlite3.Connection) -> None:
    """Create memory/task tables and indexes if they do not exist."""
    conn.executescript(_MEMORY_SCHEMA)
    conn.commit()
