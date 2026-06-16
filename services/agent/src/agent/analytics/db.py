"""SQLite schema for interaction analytics (Phase 15)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

_ANALYTICS_SCHEMA = """
CREATE TABLE IF NOT EXISTS inferred_feedback_logs (
  id                     TEXT PRIMARY KEY,
  turn_id                TEXT NOT NULL,
  predicted_satisfaction REAL,
  issue_type             TEXT,
  issue_detail           TEXT,
  evidence               TEXT,
  confidence             REAL,
  created_at             TEXT NOT NULL,
  FOREIGN KEY (turn_id) REFERENCES turn_logs (id)
);

CREATE INDEX IF NOT EXISTS idx_inferred_feedback_turn ON inferred_feedback_logs (turn_id);
CREATE INDEX IF NOT EXISTS idx_inferred_feedback_issue ON inferred_feedback_logs (issue_type);
"""


def init_analytics_db(conn: sqlite3.Connection) -> None:
    """Create the inferred_feedback_logs table and indexes if absent."""
    conn.executescript(_ANALYTICS_SCHEMA)
    conn.commit()
