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

CREATE TABLE IF NOT EXISTS prompt_logs (
  id             TEXT PRIMARY KEY,
  turn_id        TEXT NOT NULL,
  system_prompt  TEXT,
  memory_context TEXT,
  recent_context TEXT,
  tool_context   TEXT,
  final_prompt   TEXT,
  created_at     TEXT NOT NULL,
  FOREIGN KEY (turn_id) REFERENCES turn_logs (id)
);

CREATE TABLE IF NOT EXISTS tool_call_logs (
  id          TEXT PRIMARY KEY,
  turn_id     TEXT NOT NULL,
  tool_name   TEXT NOT NULL,
  input_json  TEXT,
  output_json TEXT,
  status      TEXT,
  latency_ms  INTEGER,
  error       TEXT,
  created_at  TEXT NOT NULL,
  FOREIGN KEY (turn_id) REFERENCES turn_logs (id)
);

CREATE TABLE IF NOT EXISTS memory_access_logs (
  id               TEXT PRIMARY KEY,
  turn_id          TEXT NOT NULL,
  memory_id        TEXT,
  access_type      TEXT NOT NULL,
  relevance_score  REAL,
  recency_score    REAL,
  importance_score REAL,
  final_score      REAL,
  reason           TEXT,
  created_at       TEXT NOT NULL,
  FOREIGN KEY (turn_id) REFERENCES turn_logs (id)
);

CREATE TABLE IF NOT EXISTS avatar_event_logs (
  id          TEXT PRIMARY KEY,
  turn_id     TEXT NOT NULL,
  emotion     TEXT,
  motion      TEXT,
  tts_enabled INTEGER,
  tts_text    TEXT,
  started_at  TEXT,
  ended_at    TEXT,
  created_at  TEXT NOT NULL,
  FOREIGN KEY (turn_id) REFERENCES turn_logs (id)
);

CREATE INDEX IF NOT EXISTS idx_prompt_logs_turn ON prompt_logs (turn_id);
CREATE INDEX IF NOT EXISTS idx_tool_call_logs_turn ON tool_call_logs (turn_id);
CREATE INDEX IF NOT EXISTS idx_memory_access_logs_turn ON memory_access_logs (turn_id);
CREATE TABLE IF NOT EXISTS explicit_feedback_logs (
  id         TEXT PRIMARY KEY,
  turn_id    TEXT NOT NULL,
  rating     INTEGER,
  label      TEXT,
  comment    TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (turn_id) REFERENCES turn_logs (id)
);

CREATE INDEX IF NOT EXISTS idx_avatar_event_logs_turn ON avatar_event_logs (turn_id);
CREATE INDEX IF NOT EXISTS idx_explicit_feedback_logs_turn ON explicit_feedback_logs (turn_id);
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
