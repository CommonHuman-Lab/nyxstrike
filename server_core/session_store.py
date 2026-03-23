"""
Session Store — JSON file persistence for scan sessions.

Saves scan sessions to disk so they survive server restarts.
Implements checkpoint/resume pattern 
from skills/autonomous-mode/autonomous-agent-patterns and durable execution from skills/workflow-automation.

Design notes (senior-engineering/architecture):
  - SRP: this module only handles disk I/O for sessions
  - KISS: JSON files in a data directory, no external DB
  - Named constants, guard clauses, early returns
  - Idempotent writes (safe to call repeatedly)
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import server_core.config_core as config_core

logger = logging.getLogger(__name__)

# Named constants (clean-code: no magic numbers)
DATA_DIR_NAME = config_core.get("DATA_DIR_NAME", ".hexstrike_data")
SESSIONS_DIR_NAME = "sessions"
COMPLETED_DIR_NAME = "completed"
MAX_COMPLETED_SESSIONS = 200
SESSION_FILE_SUFFIX = ".json"


def _default_data_dir() -> str:
    """Resolve the data directory path. Uses HEXSTRIKE_DATA_DIR env var or cwd."""
    return os.environ.get("HEXSTRIKE_DATA_DIR", os.path.join(os.getcwd(), DATA_DIR_NAME))


class SessionStore:
    """Persists scan sessions as JSON files on disk.

    Directory layout:
        <data_dir>/sessions/           — active sessions (one JSON per session)
        <data_dir>/sessions/completed/ — finished sessions (archived for memory)
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self._data_dir = data_dir or _default_data_dir()
        self._sessions_dir = os.path.join(self._data_dir, SESSIONS_DIR_NAME)
        self._completed_dir = os.path.join(self._sessions_dir, COMPLETED_DIR_NAME)
        self._ensure_dirs()

    @property
    def data_dir(self) -> str:
        """Public accessor for the root data directory path."""
        return self._data_dir

    def _ensure_dirs(self) -> None:
        os.makedirs(self._sessions_dir, exist_ok=True)
        os.makedirs(self._completed_dir, exist_ok=True)

    def _session_path(self, session_id: str) -> str:
        return os.path.join(self._sessions_dir, f"{session_id}{SESSION_FILE_SUFFIX}")

    def _completed_path(self, session_id: str) -> str:
        return os.path.join(self._completed_dir, f"{session_id}{SESSION_FILE_SUFFIX}")

    # ── Write ─────────────────────────────────────────────────────────

    def save(self, session_id: str, session_dict: Dict[str, Any]) -> bool:
        """Save a session dict to disk. Idempotent — safe to call repeatedly."""
        try:
            path = self._session_path(session_id)
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(session_dict, f, indent=2, default=str)
            os.replace(tmp_path, path)
            return True
        except (OSError, TypeError) as exc:
            logger.error(f"💾 Failed to save session {session_id}: {exc}")
            return False

    def archive(self, session_id: str, session_dict: Dict[str, Any]) -> bool:
        """Move a completed session to the completed directory."""
        try:
            path = self._completed_path(session_id)
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(session_dict, f, indent=2, default=str)
            os.replace(tmp_path, path)
            # Remove active session file if it exists
            active_path = self._session_path(session_id)
            if os.path.exists(active_path):
                os.remove(active_path)
            self._prune_completed()
            logger.info(f"📦 Archived session {session_id}")
            return True
        except (OSError, TypeError) as exc:
            logger.error(f"💾 Failed to archive session {session_id}: {exc}")
            return False

    # ── Read ──────────────────────────────────────────────────────────

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a session from disk. Returns None if not found."""
        path = self._session_path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"💾 Failed to load session {session_id}: {exc}")
            return None

    def load_completed(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load a completed (archived) session."""
        path = self._completed_path(session_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"💾 Failed to load completed session {session_id}: {exc}")
            return None

    def list_active(self) -> List[str]:
        """List all active session IDs on disk."""
        if not os.path.isdir(self._sessions_dir):
            return []
        return [
            f.removesuffix(SESSION_FILE_SUFFIX)
            for f in os.listdir(self._sessions_dir)
            if f.endswith(SESSION_FILE_SUFFIX) and os.path.isfile(os.path.join(self._sessions_dir, f))
        ]

    def list_completed(self) -> List[Dict[str, Any]]:
        """List completed session summaries (id, target, timestamp)."""
        if not os.path.isdir(self._completed_dir):
            return []
        summaries = []
        for fname in os.listdir(self._completed_dir):
            if not fname.endswith(SESSION_FILE_SUFFIX):
                continue
            path = os.path.join(self._completed_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                summaries.append(
                    {
                        "session_id": data.get("session_id", fname.removesuffix(SESSION_FILE_SUFFIX)),
                        "target": data.get("target", "unknown"),
                        "total_findings": data.get("total_findings", 0),
                        "iterations": data.get("iterations", 0),
                        "tools_executed": data.get("tools_executed", []),
                        "created_at": data.get("created_at", 0),
                        "updated_at": data.get("updated_at", 0),
                    }
                )
            except (json.JSONDecodeError, OSError):
                continue
        summaries.sort(key=lambda s: s.get("updated_at", 0), reverse=True)
        return summaries

    # ── Delete ────────────────────────────────────────────────────────

    def delete(self, session_id: str) -> bool:
        """Delete an active session file."""
        path = self._session_path(session_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    # ── Restore ───────────────────────────────────────────────────────

    def load_all_active(self) -> List[Dict[str, Any]]:
        """Load all active sessions from disk. Used on server startup to restore state."""
        sessions = []
        for session_id in self.list_active():
            data = self.load(session_id)
            if data:
                sessions.append(data)
        return sessions

    # ── Internal ──────────────────────────────────────────────────────

    def _prune_completed(self) -> None:
        """Keep only the most recent MAX_COMPLETED_SESSIONS completed sessions."""
        if not os.path.isdir(self._completed_dir):
            return
        files = []
        for fname in os.listdir(self._completed_dir):
            if not fname.endswith(SESSION_FILE_SUFFIX):
                continue
            fpath = os.path.join(self._completed_dir, fname)
            files.append((fpath, os.path.getmtime(fpath)))

        if len(files) <= MAX_COMPLETED_SESSIONS:
            return

        files.sort(key=lambda x: x[1])
        to_remove = files[: len(files) - MAX_COMPLETED_SESSIONS]
        for fpath, _ in to_remove:
            try:
                os.remove(fpath)
            except OSError as e:
                logger.error(f"❌ Error pruning completed session {fpath}: {e}")
