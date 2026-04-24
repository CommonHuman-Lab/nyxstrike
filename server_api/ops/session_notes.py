"""
Session Notes API — per-session markdown file management with folder support.

Routes:
  GET    /api/sessions/<id>/notes                       list all notes (all folders)
  GET    /api/sessions/<id>/notes/search?q=<query>      full-text search across notes
  GET    /api/sessions/<id>/notes/<name>                fetch note content (?folder=<f>)
  POST   /api/sessions/<id>/notes                       create note (?folder=<f>)
  PUT    /api/sessions/<id>/notes/<name>                update note (?folder=<f>)
  DELETE /api/sessions/<id>/notes/<name>                delete note (?folder=<f>)
  POST   /api/sessions/<id>/notes/<name>/upload         upload .md (?folder=<f> &overwrite=1)

  GET    /api/sessions/<id>/notes/folders               list folders
  POST   /api/sessions/<id>/notes/folders               create folder
  DELETE /api/sessions/<id>/notes/folders/<folder>      delete folder (and its notes)
  PATCH  /api/sessions/<id>/notes/folders/<folder>      rename folder
"""

import logging
from flask import Blueprint, jsonify, request, Response

from server_core.singletons import session_store
from server_core.session_store import _VALID_NOTE_NAME, _VALID_FOLDER_NAME, NOTE_MAX_BYTES
from server_core.session_flow import append_event

logger = logging.getLogger(__name__)

api_session_notes_bp = Blueprint("session_notes", __name__)


def _session_exists(session_id: str) -> bool:
  """Return True if the session exists in active or completed storage."""
  from server_core.session_flow import load_session_any
  return load_session_any(session_id) is not None


def _bad(msg: str, status: int = 400) -> Response:
  return jsonify({"success": False, "error": msg}), status  # type: ignore[return-value]


def _validate_name(name: str):
  """Return (clean_name, error_response).

  When error_response is not None, clean_name is None.
  When error_response is None, clean_name is a non-empty str.
  """
  err = session_store._validate_note_name(name)
  if err:
    return None, _bad(err)
  return name, None


def _validate_folder(folder: str):
  """Return (clean_folder, error_response). Empty folder string is always valid (root)."""
  if not folder:
    return "", None
  err = session_store._validate_folder_name(folder)
  if err:
    return None, _bad(err)
  return folder, None


def _get_folder() -> str:
  """Extract and return the ?folder= query param (stripped, default empty string)."""
  return (request.args.get("folder") or "").strip()


# ── List notes ────────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes", methods=["GET"])
def list_notes(session_id: str):
  if not _session_exists(session_id):
    return _bad("Session not found", 404)
  notes = session_store.list_notes(session_id)
  return jsonify({"success": True, "notes": notes})


# ── List folders ──────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/folders", methods=["GET"])
def list_folders(session_id: str):
  if not _session_exists(session_id):
    return _bad("Session not found", 404)
  folders = session_store.list_folders(session_id)
  return jsonify({"success": True, "folders": folders})


# ── Search notes ───────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/search", methods=["GET"])
def search_notes(session_id: str):
  """Full-text search across note filenames and content.

  Query params:
    q      — required search query (min 2 chars)
  """
  if not _session_exists(session_id):
    return _bad("Session not found", 404)
  q = (request.args.get("q") or "").strip()
  if len(q) < 2:
    return _bad("Query must be at least 2 characters", 400)
  results = session_store.search_notes(session_id, q)
  return jsonify({"success": True, "results": results, "query": q})


# ── Create folder ─────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/folders", methods=["POST"])
def create_folder(session_id: str):
  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  body = request.get_json(silent=True) or {}
  name = (body.get("name") or "").strip()

  clean, err = _validate_folder(name)
  if err:
    return err
  if not clean:
    return _bad("Folder name cannot be empty")

  assert clean is not None

  if session_store.folder_exists(session_id, clean):
    return _bad(f"Folder '{clean}' already exists", 409)

  ok = session_store.create_note_folder(session_id, clean)
  if not ok:
    return _bad("Failed to create folder", 500)

  return jsonify({"success": True, "folder": clean}), 201


# ── Delete folder ─────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/folders/<folder>", methods=["DELETE"])
def delete_folder(session_id: str, folder: str):
  clean, err = _validate_folder(folder)
  if err:
    return err
  if not clean:
    return _bad("Folder name cannot be empty")

  assert clean is not None

  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  if not session_store.folder_exists(session_id, clean):
    return _bad("Folder not found", 404)

  ok = session_store.delete_note_folder(session_id, clean)
  if not ok:
    return _bad("Failed to delete folder", 500)

  return jsonify({"success": True})


@api_session_notes_bp.route("/api/sessions/<session_id>/notes/folders/<folder>", methods=["PATCH"])
def rename_folder(session_id: str, folder: str):
  clean, err = _validate_folder(folder)
  if err:
    return err
  if not clean:
    return _bad("Folder name cannot be empty")

  assert clean is not None

  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  data = request.get_json(silent=True) or {}
  new_name = str(data.get("new_name", "")).strip()
  new_clean, nerr = _validate_folder(new_name)
  if nerr:
    return nerr
  if not new_clean:
    return _bad("New folder name cannot be empty")

  assert new_clean is not None

  rename_err = session_store.rename_note_folder(session_id, clean, new_clean)
  if rename_err:
    status = 409 if "already exists" in rename_err else 500
    return _bad(rename_err, status)

  return jsonify({"success": True, "folder": new_clean})


# ── Get note content ──────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/<name>", methods=["GET"])
def get_note(session_id: str, name: str):
  clean, err = _validate_name(name)
  if err:
    return err
  assert clean is not None

  folder = _get_folder()
  folder_clean, ferr = _validate_folder(folder)
  if ferr:
    return ferr
  assert folder_clean is not None

  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  content = session_store.load_note(session_id, clean, folder_clean)
  if content is None:
    return _bad("Note not found", 404)

  # Support ?download=1 for file download
  if request.args.get("download") == "1":
    return Response(
      content,
      mimetype="text/markdown",
      headers={"Content-Disposition": f'attachment; filename="{clean}.md"'},
    )

  return jsonify({"success": True, "filename": clean, "folder": folder_clean, "content": content})


# ── Create note ───────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes", methods=["POST"])
def create_note(session_id: str):
  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  body = request.get_json(silent=True) or {}
  name = (body.get("filename") or "").strip()
  content = body.get("content", "")
  folder = (body.get("folder") or "").strip()

  clean, err = _validate_name(name)
  if err:
    return err
  assert clean is not None

  folder_clean, ferr = _validate_folder(folder)
  if ferr:
    return ferr
  assert folder_clean is not None

  if not isinstance(content, str):
    return _bad("content must be a string")

  if len(content.encode("utf-8")) > NOTE_MAX_BYTES:
    return _bad(f"Note content exceeds maximum size of {NOTE_MAX_BYTES // (1024 * 1024)} MB")

  if session_store.note_exists(session_id, clean, folder_clean):
    return _bad(f"Note '{clean}' already exists. Use PUT to update.", 409)

  ok = session_store.save_note(session_id, clean, content, folder_clean)
  if not ok:
    return _bad("Failed to save note", 500)

  path_label = f"{folder_clean}/{clean}.md" if folder_clean else f"{clean}.md"
  append_event(session_id, "note_added", f"Note created: {path_label}", {
    "filename": clean,
    "folder": folder_clean,
  })

  return jsonify({"success": True, "filename": clean, "folder": folder_clean}), 201


# ── Update note ───────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/<name>", methods=["PUT"])
def update_note(session_id: str, name: str):
  clean, err = _validate_name(name)
  if err:
    return err
  assert clean is not None

  folder = _get_folder()
  folder_clean, ferr = _validate_folder(folder)
  if ferr:
    return ferr
  assert folder_clean is not None

  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  body = request.get_json(silent=True) or {}
  content = body.get("content", "")

  if not isinstance(content, str):
    return _bad("content must be a string")

  if len(content.encode("utf-8")) > NOTE_MAX_BYTES:
    return _bad(f"Note content exceeds maximum size of {NOTE_MAX_BYTES // (1024 * 1024)} MB")

  ok = session_store.save_note(session_id, clean, content, folder_clean)
  if not ok:
    return _bad("Failed to save note", 500)

  path_label = f"{folder_clean}/{clean}.md" if folder_clean else f"{clean}.md"
  append_event(session_id, "note_added", f"Note updated: {path_label}", {
    "filename": clean,
    "folder": folder_clean,
  })

  return jsonify({"success": True, "filename": clean, "folder": folder_clean})


# ── Delete note ───────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/<name>", methods=["DELETE"])
def delete_note(session_id: str, name: str):
  clean, err = _validate_name(name)
  if err:
    return err
  assert clean is not None

  folder = _get_folder()
  folder_clean, ferr = _validate_folder(folder)
  if ferr:
    return ferr
  assert folder_clean is not None

  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  deleted = session_store.delete_note(session_id, clean, folder_clean)
  if not deleted:
    return _bad("Note not found", 404)

  return jsonify({"success": True})


# ── Upload note ───────────────────────────────────────────────────────────────

@api_session_notes_bp.route("/api/sessions/<session_id>/notes/<name>/upload", methods=["POST"])
def upload_note(session_id: str, name: str):
  """
  Multipart upload of a .md file into the session notes.

  On filename conflict returns 409 with {conflict: true, filename: name}
  unless ?overwrite=1 is passed.
  """
  clean, err = _validate_name(name)
  if err:
    return err
  assert clean is not None

  folder = _get_folder()
  folder_clean, ferr = _validate_folder(folder)
  if ferr:
    return ferr
  assert folder_clean is not None

  if not _session_exists(session_id):
    return _bad("Session not found", 404)

  file = request.files.get("file")
  if not file:
    return _bad("No file provided — send a multipart field named 'file'")

  original_filename = file.filename or ""
  if not original_filename.lower().endswith(".md"):
    return _bad("Only .md files are accepted")

  raw = file.read()
  if len(raw) > NOTE_MAX_BYTES:
    return _bad(f"File exceeds maximum size of {NOTE_MAX_BYTES // (1024 * 1024)} MB")

  try:
    content = raw.decode("utf-8")
  except UnicodeDecodeError:
    return _bad("File must be valid UTF-8 text")

  overwrite = request.args.get("overwrite") == "1"

  if session_store.note_exists(session_id, clean, folder_clean) and not overwrite:
    return jsonify({"success": False, "conflict": True, "filename": clean, "folder": folder_clean}), 409

  ok = session_store.save_note(session_id, clean, content, folder_clean)
  if not ok:
    return _bad("Failed to save uploaded note", 500)

  path_label = f"{folder_clean}/{clean}.md" if folder_clean else f"{clean}.md"
  append_event(session_id, "note_added", f"Note uploaded: {path_label}", {
    "filename": clean,
    "folder": folder_clean,
  })

  return jsonify({"success": True, "filename": clean, "folder": folder_clean}), 201
