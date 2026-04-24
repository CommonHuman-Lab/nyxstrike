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
  chat_sessions       — named chat conversation threads
  chat_messages       — individual messages within a chat thread
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

        CREATE TABLE IF NOT EXISTS chat_sessions (
          id         TEXT PRIMARY KEY,
          name       TEXT DEFAULT '',
          summary    TEXT DEFAULT '',
          created_at TEXT DEFAULT (datetime('now')),
          updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS chat_messages (
          id              INTEGER PRIMARY KEY AUTOINCREMENT,
          chat_session_id TEXT REFERENCES chat_sessions(id) ON DELETE CASCADE,
          role            TEXT NOT NULL,
          content         TEXT NOT NULL,
          stats           TEXT DEFAULT NULL,
          is_summarized   INTEGER DEFAULT 0,
          created_at      TEXT DEFAULT (datetime('now'))
        );
      """)
      self._conn.commit()

    # ── Auto-migrations ───────────────────────────────────────────────────────
    self._migrate_chat_messages_stats()

    logger.debug("db: tables verified")

  # ── Auto-migrations ─────────────────────────────────────────────────────────

  def _migrate_chat_messages_stats(self) -> None:
    """Add stats column to chat_messages if missing (existing DBs)."""
    cur = self._conn.execute("PRAGMA table_info(chat_messages)")
    columns = {row[1] for row in cur.fetchall()}
    if "stats" not in columns:
      self._conn.execute("ALTER TABLE chat_messages ADD COLUMN stats TEXT DEFAULT NULL")
      self._conn.commit()
      logger.info("db: migrated chat_messages — added stats column")

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

  # ── Chat Sessions ─────────────────────────────────────────────────────────────

  def create_chat_session(self, session_id: str, name: str = "") -> Dict[str, Any]:
    """Insert a new chat session and return it as a dict."""
    with self._lock:
      self._conn.execute(
        "INSERT OR IGNORE INTO chat_sessions (id, name) VALUES (?, ?)",
        (session_id, name),
      )
      self._conn.commit()
      cur = self._conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
      return self._row_to_dict(cur.fetchone()) or {}

  def rename_chat_session(self, session_id: str, name: str) -> None:
    """Update the name of a chat session."""
    with self._lock:
      self._conn.execute(
        "UPDATE chat_sessions SET name = ?, updated_at = datetime('now') WHERE id = ?",
        (name, session_id),
      )
      self._conn.commit()

  def update_chat_summary(self, session_id: str, summary: str) -> None:
    """Replace the rolling summary for a chat session."""
    with self._lock:
      self._conn.execute(
        "UPDATE chat_sessions SET summary = ?, updated_at = datetime('now') WHERE id = ?",
        (summary, session_id),
      )
      self._conn.commit()

  def delete_chat_session(self, session_id: str) -> None:
    """Delete a chat session and all its messages (CASCADE)."""
    with self._lock:
      self._conn.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
      self._conn.commit()

  def get_chat_session(self, session_id: str) -> Optional[Dict[str, Any]]:
    """Return a single chat session dict, or None."""
    with self._lock:
      cur = self._conn.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
      return self._row_to_dict(cur.fetchone())

  def list_chat_sessions(self) -> List[Dict[str, Any]]:
    """Return all chat sessions, newest first."""
    with self._lock:
      cur = self._conn.execute(
        "SELECT * FROM chat_sessions ORDER BY updated_at DESC"
      )
      return self._rows_to_list(cur.fetchall())

  # ── Chat Messages ─────────────────────────────────────────────────────────────

  def add_chat_message(self, chat_session_id: str, role: str, content: str, stats: Optional[str] = None) -> int:
    """Insert a message and return its rowid."""
    with self._lock:
      cur = self._conn.execute(
        """
        INSERT INTO chat_messages (chat_session_id, role, content, stats)
        VALUES (?, ?, ?, ?)
        """,
        (chat_session_id, role, content, stats),
      )
      self._conn.execute(
        "UPDATE chat_sessions SET updated_at = datetime('now') WHERE id = ?",
        (chat_session_id,),
      )
      self._conn.commit()
      return cur.lastrowid  # type: ignore[return-value]

  def get_active_chat_messages(self, chat_session_id: str) -> List[Dict[str, Any]]:
    """Return non-summarized messages for a session, oldest first."""
    with self._lock:
      cur = self._conn.execute(
        """
        SELECT * FROM chat_messages
        WHERE chat_session_id = ? AND is_summarized = 0
        ORDER BY id ASC
        """,
        (chat_session_id,),
      )
      return self._rows_to_list(cur.fetchall())

  def get_all_chat_messages(self, chat_session_id: str) -> List[Dict[str, Any]]:
    """Return all messages (including summarized) for a session, oldest first."""
    with self._lock:
      cur = self._conn.execute(
        "SELECT * FROM chat_messages WHERE chat_session_id = ? ORDER BY id ASC",
        (chat_session_id,),
      )
      return self._rows_to_list(cur.fetchall())

  def mark_messages_summarized(self, message_ids: List[int]) -> None:
    """Mark a batch of messages as folded into the rolling summary."""
    if not message_ids:
      return
    placeholders = ",".join("?" for _ in message_ids)
    with self._lock:
      self._conn.execute(
        f"UPDATE chat_messages SET is_summarized = 1 WHERE id IN ({placeholders})",
        message_ids,
      )
      self._conn.commit()

  def count_active_chat_messages(self, chat_session_id: str) -> int:
    """Return count of non-summarized messages for a session."""
    with self._lock:
      cur = self._conn.execute(
        "SELECT COUNT(*) FROM chat_messages WHERE chat_session_id = ? AND is_summarized = 0",
        (chat_session_id,),
      )
      row = cur.fetchone()
      return row[0] if row else 0

  # ── Lifecycle ─────────────────────────────────────────────────────────────────

  def close(self) -> None:
    """Close the database connection. Called on server shutdown."""
    with self._lock:
      try:
        self._conn.close()
        logger.debug("db: connection closed")
      except Exception as exc:
        logger.warning("db: error closing connection: %s", exc)
