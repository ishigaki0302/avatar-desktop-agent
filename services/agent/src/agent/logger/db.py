"""SQLite schema and connection helpers for interaction logging."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id          TEXT PRIMARY KEY,
  title       TEXT,
  started_at  TEXT NOT NULL,
  ended_at    TEXT,
  summary     TEXT,
  model       TEXT,
  app_version TEXT,
  created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS turn_logs (
  id                   TEXT PRIMARY KEY,
  session_id           TEXT NOT NULL,
  turn_index           INTEGER NOT NULL,
  timestamp            TEXT NOT NULL,
  user_input           TEXT,
  assistant_output     TEXT,
  raw_assistant_output TEXT,
  model                TEXT,
  prompt_tokens        INTEGER,
  completion_tokens    INTEGER,
  latency_ms           INTEGER,
  emotion              TEXT,
  motion               TEXT,
  status               TEXT,
  error                TEXT,
  created_at           TEXT NOT NULL,
  FOREIGN KEY (session_id) REFERENCES sessions (id)
);

CREATE INDEX IF NOT EXISTS idx_turn_logs_session
  ON turn_logs (session_id, turn_index);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Open a SQLite connection with row access by column name."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they do not exist."""
    conn.executescript(_SCHEMA)
    conn.commit()
