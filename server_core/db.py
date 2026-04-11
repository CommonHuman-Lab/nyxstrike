"""
server_core/db.py

Shared SQLite database for NyxStrike.

Single database file at <data_dir>/nyxstrike.db.
All tables are created on first run (CREATE TABLE IF NOT EXISTS).
Thread-safe via a single lock.

Design notes:
  - One connection per instance, kept open for the lifetime of the process.
  - WAL journal mode for better read/write concurrency.
  - Follows the same patterns as SessionStore / RunHistoryStore (SRP, KISS).
  - New feature areas add their own tables here — no separate DB files.

Current tables:
  llm_sessions        — one row per LLM analysis session
  llm_vulnerabilities — parsed vulnerabilities linked to a session
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

import server_core.config_core as config_core

logger = logging.getLogger(__name__)

DB_FILE_NAME = "nyxstrike.db"


class NyxStrikeDB:
  """Shared SQLite database.

  Instantiated once in singletons.py and shared across all blueprints.
  """

  def __init__(self, data_dir: Optional[str] = None) -> None:
    self._data_dir = data_dir or config_core.default_data_dir()
    self._db_path = os.path.join(self._data_dir, DB_FILE_NAME)
    self._lock = threading.Lock()
    os.makedirs(self._data_dir, exist_ok=True)
    self._conn = self._connect()
    self._ensure_tables()

  # ── Connection ──────────────────────────────────────────────────────────────

  def _connect(self) -> sqlite3.Connection:
    conn = sqlite3.connect(self._db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.commit()
    logger.debug("db: opened %s", self._db_path)
    return conn

  def _ensure_tables(self) -> None:
    """Create all tables if they don't exist yet."""
    with self._lock:
      cur = self._conn.cursor()
      cur.executescript("""
        CREATE TABLE IF NOT EXISTS llm_sessions (
          session_id    TEXT PRIMARY KEY,
          target        TEXT NOT NULL,
          objective     TEXT DEFAULT 'comprehensive',
          status        TEXT DEFAULT 'running',
          risk_level    TEXT,
          summary       TEXT,
          full_response TEXT,
          raw_scan_data TEXT,
          provider      TEXT,
          model         TEXT,
          tool_loops    INTEGER DEFAULT 0,
          started_at    TEXT DEFAULT (datetime('now')),
          completed_at  TEXT
        );

        CREATE TABLE IF NOT EXISTS llm_vulnerabilities (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          session_id  TEXT REFERENCES llm_sessions(session_id) ON DELETE CASCADE,
          vuln_name   TEXT,
          severity    TEXT,
          port        TEXT,
          service     TEXT,
          description TEXT,
          fix_text    TEXT,
          created_at  TEXT DEFAULT (datetime('now'))
        );
      """)
      self._conn.commit()
    logger.debug("db: tables verified")

  # ── Internal helpers ─────────────────────────────────────────────────────────

  def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    if row is None:
      return None
    return dict(row)

  def _rows_to_list(self, rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(r) for r in rows]

  # ── LLM Sessions ─────────────────────────────────────────────────────────────

  def create_llm_session(
    self,
    session_id: str,
    target: str,
    objective: str = "comprehensive",
    provider: str = "",
    model: str = "",
  ) -> None:
    """Insert a new LLM session row with status 'running'."""
    with self._lock:
      self._conn.execute(
        """
        INSERT OR IGNORE INTO llm_sessions
          (session_id, target, objective, provider, model, status)
        VALUES (?, ?, ?, ?, ?, 'running')
        """,
        (session_id, target, objective, provider, model),
      )
      self._conn.commit()

  def update_llm_session(self, session_id: str, **fields: Any) -> None:
    """Update one or more columns on an existing session row.

    Allowed fields: status, risk_level, summary, full_response,
                    raw_scan_data, tool_loops, completed_at
    """
    allowed = {
      "status", "risk_level", "summary", "full_response",
      "raw_scan_data", "tool_loops", "completed_at",
    }
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
      return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [session_id]
    with self._lock:
      self._conn.execute(
        f"UPDATE llm_sessions SET {set_clause} WHERE session_id = ?",
        values,
      )
      self._conn.commit()

  def get_llm_session(self, session_id: str) -> Optional[Dict[str, Any]]:
    """Return a single session dict, or None if not found."""
    with self._lock:
      cur = self._conn.execute(
        "SELECT * FROM llm_sessions WHERE session_id = ?",
        (session_id,),
      )
      return self._row_to_dict(cur.fetchone())

  def list_llm_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
    """Return most recent sessions, newest first."""
    with self._lock:
      cur = self._conn.execute(
        "SELECT * FROM llm_sessions ORDER BY started_at DESC LIMIT ?",
        (limit,),
      )
      return self._rows_to_list(cur.fetchall())

  # ── LLM Vulnerabilities ───────────────────────────────────────────────────────

  def save_llm_vulnerability(self, session_id: str, vuln: Dict[str, Any]) -> int:
    """Insert a parsed vulnerability and return its rowid."""
    with self._lock:
      cur = self._conn.execute(
        """
        INSERT INTO llm_vulnerabilities
          (session_id, vuln_name, severity, port, service, description, fix_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
          session_id,
          vuln.get("vuln_name", ""),
          vuln.get("severity", ""),
          vuln.get("port", ""),
          vuln.get("service", ""),
          vuln.get("description", ""),
          vuln.get("fix", vuln.get("fix_text", "")),
        ),
      )
      self._conn.commit()
      return cur.lastrowid

  def get_llm_vulnerabilities(self, session_id: str) -> List[Dict[str, Any]]:
    """Return all vulnerabilities for a session."""
    with self._lock:
      cur = self._conn.execute(
        "SELECT * FROM llm_vulnerabilities WHERE session_id = ? ORDER BY id",
        (session_id,),
      )
      return self._rows_to_list(cur.fetchall())

  # ── Lifecycle ─────────────────────────────────────────────────────────────────

  def close(self) -> None:
    """Close the database connection. Called on server shutdown."""
    with self._lock:
      try:
        self._conn.close()
        logger.debug("db: connection closed")
      except Exception as exc:
        logger.warning("db: error closing connection: %s", exc)
