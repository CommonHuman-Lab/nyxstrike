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

Directory layout:
  <data_dir>/sessions/
    <session_id>/
      session.json          — session state
      notes/
        <name>.md           — per-session markdown notes
    completed/
      <session_id>/
        session.json
        notes/
    templates/
      <template_id>.json    — templates stay flat (no notes)
"""

import json
import logging
import os
import re
import shutil
from typing import Any, Dict, List, Optional
import server_core.config_core as config_core

logger = logging.getLogger(__name__)

# Named constants (clean-code: no magic numbers)
SESSIONS_DIR_NAME = "sessions"
COMPLETED_DIR_NAME = "completed"
TEMPLATES_DIR_NAME = "templates"
SESSION_FILE_NAME = "session.json"
NOTES_DIR_NAME = "notes"
MAX_COMPLETED_SESSIONS = 200
SESSION_FILE_SUFFIX = ".json"
NOTE_FILE_SUFFIX = ".md"
NOTE_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_VALID_NOTE_NAME = re.compile(r'^[a-zA-Z0-9_\-]+$')
_VALID_FOLDER_NAME = re.compile(r'^[a-zA-Z0-9_\-]+$')


class SessionStore:
    """Persists scan sessions as JSON files on disk.

    Directory layout:
        <data_dir>/sessions/<id>/session.json  — active sessions
        <data_dir>/sessions/completed/<id>/    — finished sessions
        <data_dir>/sessions/templates/         — saved templates (flat)
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self._data_dir = data_dir or config_core.default_data_dir()
        self._sessions_dir = os.path.join(self._data_dir, SESSIONS_DIR_NAME)
        self._completed_dir = os.path.join(self._sessions_dir, COMPLETED_DIR_NAME)
        self._templates_dir = os.path.join(self._sessions_dir, TEMPLATES_DIR_NAME)
        self._ensure_dirs()
        self._migrate_flat_files()

    @property
    def data_dir(self) -> str:
        """Public accessor for the root data directory path."""
        return self._data_dir

    # ── Directory helpers ──────────────────────────────────────────────

    def _ensure_dirs(self) -> None:
        os.makedirs(self._sessions_dir, exist_ok=True)
        os.makedirs(self._completed_dir, exist_ok=True)
        os.makedirs(self._templates_dir, exist_ok=True)

    def _session_dir(self, session_id: str) -> str:
        """Return the folder for an active session."""
        return os.path.join(self._sessions_dir, session_id)

    def _session_path(self, session_id: str) -> str:
        """Return the session.json path for an active session."""
        return os.path.join(self._session_dir(session_id), SESSION_FILE_NAME)

    def _completed_dir_for(self, session_id: str) -> str:
        """Return the folder for a completed session."""
        return os.path.join(self._completed_dir, session_id)

    def _completed_path(self, session_id: str) -> str:
        """Return the session.json path for a completed session."""
        return os.path.join(self._completed_dir_for(session_id), SESSION_FILE_NAME)

    def _notes_dir(self, session_id: str, completed: bool = False) -> str:
        """Return the notes/ sub-folder for a session."""
        base = self._completed_dir_for(session_id) if completed else self._session_dir(session_id)
        return os.path.join(base, NOTES_DIR_NAME)

    def _template_path(self, template_id: str) -> str:
        return os.path.join(self._templates_dir, f"{template_id}{SESSION_FILE_SUFFIX}")

    # ── Startup migration ──────────────────────────────────────────────

    def _migrate_flat_files(self) -> None:
        """
        One-time migration: move legacy flat files into the new folder layout.

        Handles both:
          - sess_<id>.json  →  sess_<id>/session.json
          - sess_<id>--notes/<name>.md  →  sess_<id>/notes/<name>.md
        in both the active and completed directories.
        """
        self._migrate_dir(self._sessions_dir, completed=False)
        self._migrate_dir(self._completed_dir, completed=True)

    def _migrate_dir(self, base: str, completed: bool) -> None:
        if not os.path.isdir(base):
            return
        for entry in os.listdir(base):
            entry_path = os.path.join(base, entry)

            # Migrate flat JSON files: sess_<id>.json → sess_<id>/session.json
            if entry.endswith(SESSION_FILE_SUFFIX) and os.path.isfile(entry_path):
                session_id = entry[: -len(SESSION_FILE_SUFFIX)]
                # Skip reserved names
                if session_id in (COMPLETED_DIR_NAME, TEMPLATES_DIR_NAME):
                    continue
                target_dir = os.path.join(base, session_id)
                target_json = os.path.join(target_dir, SESSION_FILE_NAME)
                if os.path.exists(target_json):
                    # Already migrated — remove stale flat file
                    try:
                        os.remove(entry_path)
                        logger.info(f"🗂 Removed stale flat file {entry_path}")
                    except OSError:
                        pass
                    continue
                try:
                    os.makedirs(target_dir, exist_ok=True)
                    shutil.move(entry_path, target_json)
                    logger.info(f"🗂 Migrated {entry_path} → {target_json}")
                except OSError as exc:
                    logger.error(f"🗂 Migration failed for {entry_path}: {exc}")

            # Migrate old --notes sibling folders: sess_<id>--notes/ → sess_<id>/notes/
            elif entry.endswith("--notes") and os.path.isdir(entry_path):
                session_id = entry[: -len("--notes")]
                target_notes = os.path.join(base, session_id, NOTES_DIR_NAME)
                if os.path.exists(target_notes):
                    # Already migrated — skip (don't overwrite)
                    continue
                try:
                    parent = os.path.join(base, session_id)
                    os.makedirs(parent, exist_ok=True)
                    shutil.move(entry_path, target_notes)
                    logger.info(f"🗂 Migrated notes {entry_path} → {target_notes}")
                except OSError as exc:
                    logger.error(f"🗂 Notes migration failed for {entry_path}: {exc}")

    # ── Write ─────────────────────────────────────────────────────────

    def save(self, session_id: str, session_dict: Dict[str, Any]) -> bool:
        """Save a session dict to disk. Idempotent — safe to call repeatedly."""
        try:
            session_dir = self._session_dir(session_id)
            os.makedirs(session_dir, exist_ok=True)
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
        """Move a completed session to the completed directory, preserving notes."""
        try:
            completed_session_dir = self._completed_dir_for(session_id)
            os.makedirs(completed_session_dir, exist_ok=True)
            # Write the new session.json in completed/
            path = self._completed_path(session_id)
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(session_dict, f, indent=2, default=str)
            os.replace(tmp_path, path)

            # Move notes if they exist
            active_notes = self._notes_dir(session_id, completed=False)
            completed_notes = self._notes_dir(session_id, completed=True)
            if os.path.isdir(active_notes) and not os.path.exists(completed_notes):
                shutil.move(active_notes, completed_notes)

            # Remove the entire active session folder
            active_dir = self._session_dir(session_id)
            if os.path.isdir(active_dir):
                shutil.rmtree(active_dir)

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

    def save_template(self, template_id: str, template_dict: Dict[str, Any]) -> bool:
        """Save a session template to disk."""
        try:
            path = self._template_path(template_id)
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(template_dict, f, indent=2, default=str)
            os.replace(tmp_path, path)
            return True
        except (OSError, TypeError) as exc:
            logger.error(f"💾 Failed to save template {template_id}: {exc}")
            return False

    def load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Load one session template from disk."""
        path = self._template_path(template_id)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.error(f"💾 Failed to load template {template_id}: {exc}")
            return None

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all saved session templates."""
        if not os.path.isdir(self._templates_dir):
            return []
        templates: List[Dict[str, Any]] = []
        for fname in os.listdir(self._templates_dir):
            if not fname.endswith(SESSION_FILE_SUFFIX):
                continue
            path = os.path.join(self._templates_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                templates.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        templates.sort(key=lambda t: t.get("updated_at", 0), reverse=True)
        return templates

    def delete_template(self, template_id: str) -> bool:
        """Delete one session template."""
        path = self._template_path(template_id)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def list_active(self) -> List[str]:
        """List all active session IDs on disk."""
        if not os.path.isdir(self._sessions_dir):
            return []
        ids = []
        for entry in os.listdir(self._sessions_dir):
            # Must be a directory (the per-session folder) with a session.json inside
            if entry in (COMPLETED_DIR_NAME, TEMPLATES_DIR_NAME):
                continue
            entry_path = os.path.join(self._sessions_dir, entry)
            if os.path.isdir(entry_path) and os.path.isfile(
                os.path.join(entry_path, SESSION_FILE_NAME)
            ):
                ids.append(entry)
        return ids

    def list_completed(self) -> List[Dict[str, Any]]:
        """List completed session summaries (id, target, timestamp)."""
        if not os.path.isdir(self._completed_dir):
            return []
        summaries = []
        for entry in os.listdir(self._completed_dir):
            entry_path = os.path.join(self._completed_dir, entry)
            json_path = os.path.join(entry_path, SESSION_FILE_NAME)
            if not os.path.isdir(entry_path) or not os.path.isfile(json_path):
                continue
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                summaries.append(
                    {
                        "session_id": data.get("session_id", entry),
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
        """Delete an active session folder (including notes)."""
        session_dir = self._session_dir(session_id)
        if os.path.isdir(session_dir):
            shutil.rmtree(session_dir)
            return True
        return False

    def delete_completed(self, session_id: str) -> bool:
        """Delete an archived/completed session folder (including notes)."""
        session_dir = self._completed_dir_for(session_id)
        if os.path.isdir(session_dir):
            shutil.rmtree(session_dir)
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

    # ── Notes ─────────────────────────────────────────────────────────

    @staticmethod
    def _validate_note_name(name: str) -> Optional[str]:
        """Return an error string if the note name is invalid, else None."""
        if not name:
            return "Note name cannot be empty"
        if not _VALID_NOTE_NAME.match(name):
            return "Note name may only contain letters, digits, hyphens, and underscores"
        if len(name) > 120:
            return "Note name too long (max 120 characters)"
        return None

    @staticmethod
    def _validate_folder_name(name: str) -> Optional[str]:
        """Return an error string if the folder name is invalid, else None."""
        if not name:
            return "Folder name cannot be empty"
        if not _VALID_FOLDER_NAME.match(name):
            return "Folder name may only contain letters, digits, hyphens, and underscores"
        if len(name) > 120:
            return "Folder name too long (max 120 characters)"
        return None

    def _resolve_notes_dir(self, session_id: str) -> Optional[str]:
        """Return the notes/ dir for a session regardless of active/completed status."""
        if os.path.exists(self._session_path(session_id)):
            return self._notes_dir(session_id, completed=False)
        if os.path.exists(self._completed_path(session_id)):
            return self._notes_dir(session_id, completed=True)
        return None

    def _safe_note_dir(self, notes_dir: str, folder: str = "") -> Optional[str]:
        """Return the resolved note directory, ensuring it stays within notes_dir."""
        if not folder:
            return notes_dir
        target = os.path.realpath(os.path.join(notes_dir, folder))
        base = os.path.realpath(notes_dir)
        if not target.startswith(base + os.sep):
            return None
        return target

    def list_notes(self, session_id: str) -> List[Dict[str, Any]]:
        """List all markdown notes for a session, including those in sub-folders.

        Each entry has: filename, folder (empty string = root), size, updated_at.
        """
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir or not os.path.isdir(notes_dir):
            return []
        result: List[Dict[str, Any]] = []
        for root, dirs, files in os.walk(notes_dir):
            # Only allow one level of nesting (direct sub-folders of notes/)
            rel_root = os.path.relpath(root, notes_dir)
            if rel_root == ".":
                folder = ""
                # Prune dirs to only valid single-level folders
                dirs[:] = [
                    d for d in dirs
                    if _VALID_FOLDER_NAME.match(d) and not d.startswith(".")
                ]
            else:
                # We are inside a sub-folder; don't recurse deeper
                folder = rel_root
                dirs[:] = []

            for fname in files:
                if not fname.endswith(NOTE_FILE_SUFFIX):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    stat = os.stat(fpath)
                    result.append({
                        "filename": fname[: -len(NOTE_FILE_SUFFIX)],
                        "folder": folder,
                        "size": stat.st_size,
                        "updated_at": int(stat.st_mtime),
                    })
                except OSError:
                    continue
        result.sort(key=lambda n: n["updated_at"], reverse=True)
        return result

    def list_folders(self, session_id: str) -> List[str]:
        """Return sorted list of valid sub-folder names inside the session notes dir."""
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir or not os.path.isdir(notes_dir):
            return []
        folders = []
        for entry in os.listdir(notes_dir):
            if not _VALID_FOLDER_NAME.match(entry):
                continue
            if os.path.isdir(os.path.join(notes_dir, entry)):
                folders.append(entry)
        folders.sort()
        return folders

    def folder_exists(self, session_id: str, folder: str) -> bool:
        """Return True if the folder exists under the session's notes dir."""
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir:
            return False
        target = self._safe_note_dir(notes_dir, folder)
        if not target:
            return False
        return os.path.isdir(target)

    def create_note_folder(self, session_id: str, folder: str) -> bool:
        """Create a sub-folder inside the session notes directory."""
        notes_dir = self._resolve_notes_dir(session_id)
        if notes_dir is None:
            return False
        target = self._safe_note_dir(notes_dir, folder)
        if not target:
            return False
        try:
            os.makedirs(notes_dir, exist_ok=True)
            os.makedirs(target, exist_ok=True)
            return True
        except OSError as exc:
            logger.error(f"📁 Failed to create folder {folder} for {session_id}: {exc}")
            return False

    def delete_note_folder(self, session_id: str, folder: str) -> bool:
        """Delete a sub-folder and all its notes."""
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir:
            return False
        target = self._safe_note_dir(notes_dir, folder)
        if not target:
            return False
        if not os.path.isdir(target):
            return False
        try:
            shutil.rmtree(target)
            return True
        except OSError as exc:
            logger.error(f"📁 Failed to delete folder {folder} for {session_id}: {exc}")
            return False

    def rename_note_folder(self, session_id: str, old_name: str, new_name: str) -> Optional[str]:
        """Rename a sub-folder.  Returns None on success, or an error string."""
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir:
            return "Session not found"
        old_target = self._safe_note_dir(notes_dir, old_name)
        if not old_target or not os.path.isdir(old_target):
            return "Folder not found"
        new_target = self._safe_note_dir(notes_dir, new_name)
        if not new_target:
            return "Invalid new folder name"
        if os.path.exists(new_target):
            return "A folder with that name already exists"
        try:
            os.rename(old_target, new_target)
            return None
        except OSError as exc:
            logger.error(f"📁 Failed to rename folder {old_name} → {new_name} for {session_id}: {exc}")
            return "Failed to rename folder"

    def load_note(self, session_id: str, name: str, folder: str = "") -> Optional[str]:
        """Load raw markdown content of a note. `name` is without .md extension."""
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir:
            return None
        note_dir = self._safe_note_dir(notes_dir, folder)
        if not note_dir:
            return None
        fpath = os.path.join(note_dir, f"{name}{NOTE_FILE_SUFFIX}")
        if not os.path.exists(fpath):
            return None
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                return f.read()
        except OSError as exc:
            logger.error(f"📝 Failed to load note {name} for {session_id}: {exc}")
            return None

    def search_notes(self, session_id: str, query: str, snippet_len: int = 160) -> List[Dict[str, Any]]:
        """Full-text search across all notes for a session.

        Returns a list of matches, each with filename, folder, size, updated_at,
        and a 'snippet' string showing context around the first match.
        Results are sorted by updated_at descending.
        """
        q = query.strip().lower()
        if not q:
            return []
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir or not os.path.isdir(notes_dir):
            return []

        results: List[Dict[str, Any]] = []
        for root, dirs, files in os.walk(notes_dir):
            rel_root = os.path.relpath(root, notes_dir)
            if rel_root == ".":
                folder = ""
                dirs[:] = [
                    d for d in dirs
                    if _VALID_FOLDER_NAME.match(d) and not d.startswith(".")
                ]
            else:
                folder = rel_root
                dirs[:] = []

            for fname in files:
                if not fname.endswith(NOTE_FILE_SUFFIX):
                    continue
                fpath = os.path.join(root, fname)
                try:
                    stat = os.stat(fpath)
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                except OSError:
                    continue

                name_stem = fname[: -len(NOTE_FILE_SUFFIX)]
                # Match on filename or content (case-insensitive)
                name_hit = q in name_stem.lower()
                content_lower = content.lower()
                content_idx = content_lower.find(q)
                if not name_hit and content_idx == -1:
                    continue

                # Build a snippet around the first content match
                if content_idx != -1:
                    start = max(0, content_idx - snippet_len // 3)
                    end = min(len(content), content_idx + len(q) + (snippet_len * 2 // 3))
                    raw = content[start:end].strip()
                    # Collapse newlines for inline display
                    snippet = " ".join(raw.split())
                    if start > 0:
                        snippet = "…" + snippet
                    if end < len(content):
                        snippet = snippet + "…"
                else:
                    snippet = ""

                results.append({
                    "filename": name_stem,
                    "folder": folder,
                    "size": stat.st_size,
                    "updated_at": int(stat.st_mtime),
                    "snippet": snippet,
                    "name_match": name_hit,
                })

        results.sort(key=lambda n: n["updated_at"], reverse=True)
        return results

    def note_exists(self, session_id: str, name: str, folder: str = "") -> bool:
        """Return True if a note with the given name exists."""
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir:
            return False
        note_dir = self._safe_note_dir(notes_dir, folder)
        if not note_dir:
            return False
        return os.path.exists(os.path.join(note_dir, f"{name}{NOTE_FILE_SUFFIX}"))

    def save_note(self, session_id: str, name: str, content: str, folder: str = "") -> bool:
        """Atomically save markdown content as a note. Creates notes/ dir if needed."""
        notes_dir = self._resolve_notes_dir(session_id)
        if notes_dir is None:
            logger.error(f"📝 Session {session_id} not found for note save")
            return False
        if len(content.encode("utf-8")) > NOTE_MAX_BYTES:
            logger.error(f"📝 Note {name} exceeds max size for {session_id}")
            return False
        note_dir = self._safe_note_dir(notes_dir, folder)
        if not note_dir:
            logger.error(f"📝 Invalid folder path {folder} for {session_id}")
            return False
        try:
            os.makedirs(note_dir, exist_ok=True)
            fpath = os.path.join(note_dir, f"{name}{NOTE_FILE_SUFFIX}")
            tmp_path = fpath + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(content)
            os.replace(tmp_path, fpath)
            return True
        except OSError as exc:
            logger.error(f"📝 Failed to save note {name} for {session_id}: {exc}")
            return False

    def delete_note(self, session_id: str, name: str, folder: str = "") -> bool:
        """Delete a note by name (without .md extension)."""
        notes_dir = self._resolve_notes_dir(session_id)
        if not notes_dir:
            return False
        note_dir = self._safe_note_dir(notes_dir, folder)
        if not note_dir:
            return False
        fpath = os.path.join(note_dir, f"{name}{NOTE_FILE_SUFFIX}")
        if not os.path.exists(fpath):
            return False
        try:
            os.remove(fpath)
            return True
        except OSError as exc:
            logger.error(f"📝 Failed to delete note {name} for {session_id}: {exc}")
            return False

    # ── Internal ──────────────────────────────────────────────────────

    def _prune_completed(self) -> None:
        """Keep only the most recent MAX_COMPLETED_SESSIONS completed sessions."""
        if not os.path.isdir(self._completed_dir):
            return
        folders = []
        for entry in os.listdir(self._completed_dir):
            entry_path = os.path.join(self._completed_dir, entry)
            json_path = os.path.join(entry_path, SESSION_FILE_NAME)
            if os.path.isdir(entry_path) and os.path.isfile(json_path):
                folders.append((entry_path, os.path.getmtime(json_path)))

        if len(folders) <= MAX_COMPLETED_SESSIONS:
            return

        folders.sort(key=lambda x: x[1])
        to_remove = folders[: len(folders) - MAX_COMPLETED_SESSIONS]
        for folder_path, _ in to_remove:
            try:
                shutil.rmtree(folder_path)
            except OSError as e:
                logger.error(f"❌ Error pruning completed session {folder_path}: {e}")
