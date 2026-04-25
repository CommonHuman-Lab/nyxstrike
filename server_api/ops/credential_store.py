"""
server_api/ops/credential_store.py

Credential and Loot Store API — structured storage for discovered credentials,
hashes, tokens, keys, and other post-exploitation artifacts.

Credentials:
  GET    /api/credentials                    list (filter: session_id, host, service, type, tag, q)
  POST   /api/credentials                    add
  GET    /api/credentials/<cred_id>          get one
  PATCH  /api/credentials/<cred_id>          update
  DELETE /api/credentials/<cred_id>          delete
  GET    /api/credentials/export             export as JSON

Loot:
  GET    /api/loot                           list (filter: session_id, loot_type, host, tag, q)
  POST   /api/loot                           add
  GET    /api/loot/<loot_id>                 get one
  PATCH  /api/loot/<loot_id>                 update
  DELETE /api/loot/<loot_id>                 delete
  GET    /api/loot/export                    export as JSON
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, Response

from server_core.singletons import db

logger = logging.getLogger(__name__)

api_credentials_bp = Blueprint("credentials", __name__)
api_loot_bp = Blueprint("loot", __name__)

VALID_CRED_TYPES = {"plaintext", "hash", "key", "token", "cookie", "certificate", "other"}
VALID_LOOT_TYPES = {"flag", "file", "config", "hash", "key", "secret", "screenshot", "other"}


def _bad(msg: str, status: int = 400) -> Response:
  return jsonify({"success": False, "error": msg}), status  # type: ignore[return-value]


# ── Credentials ────────────────────────────────────────────────────────────────

@api_credentials_bp.route("/api/credentials/export", methods=["GET"])
def export_credentials():
  """Export all credentials matching query params as JSON."""
  try:
    creds = db.list_credentials(
      session_id=request.args.get("session_id") or None,
      host=request.args.get("host") or None,
      service=request.args.get("service") or None,
      cred_type=request.args.get("type") or None,
      tag=request.args.get("tag") or None,
      query=request.args.get("q") or None,
    )
    return jsonify({
      "success": True,
      "credentials": creds,
      "total": len(creds),
      "exported_at": datetime.utcnow().isoformat() + "Z",
    })
  except Exception as e:
    logger.error("Error exporting credentials: %s", e)
    return _bad(str(e), 500)


@api_credentials_bp.route("/api/credentials", methods=["GET"])
def list_credentials():
  """List credentials with optional filters."""
  try:
    creds = db.list_credentials(
      session_id=request.args.get("session_id") or None,
      host=request.args.get("host") or None,
      service=request.args.get("service") or None,
      cred_type=request.args.get("type") or None,
      tag=request.args.get("tag") or None,
      query=request.args.get("q") or None,
    )
    return jsonify({"success": True, "credentials": creds, "total": len(creds)})
  except Exception as e:
    logger.error("Error listing credentials: %s", e)
    return _bad(str(e), 500)


@api_credentials_bp.route("/api/credentials", methods=["POST"])
def add_credential():
  """Add a new credential record."""
  try:
    body = request.get_json(force=True) or {}
    cred_type = str(body.get("type", "plaintext")).lower()
    if cred_type not in VALID_CRED_TYPES:
      return _bad(f"type must be one of: {', '.join(sorted(VALID_CRED_TYPES))}")
    if not body.get("username") and not body.get("secret"):
      return _bad("at least one of username or secret is required")
    cred = {
      "type": cred_type,
      "username": str(body.get("username", "")).strip(),
      "secret": str(body.get("secret", "")).strip(),
      "hash_type": str(body.get("hash_type", "")).strip(),
      "service": str(body.get("service", "")).strip(),
      "host": str(body.get("host", "")).strip(),
      "port": str(body.get("port", "")).strip(),
      "source_tool": str(body.get("source_tool", "")).strip(),
      "evidence": str(body.get("evidence", "")).strip(),
      "tags": body.get("tags", []) if isinstance(body.get("tags"), list) else [],
      "verified": bool(body.get("verified", False)),
      "notes": str(body.get("notes", "")).strip(),
    }
    session_id = str(body.get("session_id", "")).strip() or None
    cred_id = db.add_credential(cred, session_id=session_id)
    stored = db.get_credential(cred_id)
    return jsonify({"success": True, "credential": stored}), 201
  except Exception as e:
    logger.error("Error adding credential: %s", e)
    return _bad(str(e), 500)


@api_credentials_bp.route("/api/credentials/<cred_id>", methods=["GET"])
def get_credential(cred_id: str):
  """Get a single credential by ID."""
  try:
    cred = db.get_credential(cred_id)
    if not cred:
      return _bad("Credential not found", 404)
    return jsonify({"success": True, "credential": cred})
  except Exception as e:
    logger.error("Error getting credential %s: %s", cred_id, e)
    return _bad(str(e), 500)


@api_credentials_bp.route("/api/credentials/<cred_id>", methods=["PATCH"])
def update_credential(cred_id: str):
  """Update a credential record."""
  try:
    if not db.get_credential(cred_id):
      return _bad("Credential not found", 404)
    body = request.get_json(force=True) or {}
    allowed = {
      "type", "username", "secret", "hash_type", "service", "host", "port",
      "source_tool", "evidence", "tags", "verified", "notes", "session_id",
    }
    updates = {k: v for k, v in body.items() if k in allowed}
    if "type" in updates and updates["type"] not in VALID_CRED_TYPES:
      return _bad(f"type must be one of: {', '.join(sorted(VALID_CRED_TYPES))}")
    db.update_credential(cred_id, **updates)
    return jsonify({"success": True, "credential": db.get_credential(cred_id)})
  except Exception as e:
    logger.error("Error updating credential %s: %s", cred_id, e)
    return _bad(str(e), 500)


@api_credentials_bp.route("/api/credentials/<cred_id>", methods=["DELETE"])
def delete_credential(cred_id: str):
  """Delete a credential record."""
  try:
    if not db.get_credential(cred_id):
      return _bad("Credential not found", 404)
    db.delete_credential(cred_id)
    return jsonify({"success": True, "cred_id": cred_id})
  except Exception as e:
    logger.error("Error deleting credential %s: %s", cred_id, e)
    return _bad(str(e), 500)


# ── Loot ───────────────────────────────────────────────────────────────────────

@api_loot_bp.route("/api/loot/export", methods=["GET"])
def export_loot():
  """Export all loot matching query params as JSON."""
  try:
    items = db.list_loot(
      session_id=request.args.get("session_id") or None,
      loot_type=request.args.get("loot_type") or None,
      host=request.args.get("host") or None,
      tag=request.args.get("tag") or None,
      query=request.args.get("q") or None,
    )
    return jsonify({
      "success": True,
      "loot": items,
      "total": len(items),
      "exported_at": datetime.utcnow().isoformat() + "Z",
    })
  except Exception as e:
    logger.error("Error exporting loot: %s", e)
    return _bad(str(e), 500)


@api_loot_bp.route("/api/loot", methods=["GET"])
def list_loot():
  """List loot with optional filters."""
  try:
    items = db.list_loot(
      session_id=request.args.get("session_id") or None,
      loot_type=request.args.get("loot_type") or None,
      host=request.args.get("host") or None,
      tag=request.args.get("tag") or None,
      query=request.args.get("q") or None,
    )
    return jsonify({"success": True, "loot": items, "total": len(items)})
  except Exception as e:
    logger.error("Error listing loot: %s", e)
    return _bad(str(e), 500)


@api_loot_bp.route("/api/loot", methods=["POST"])
def add_loot():
  """Add a new loot record."""
  try:
    body = request.get_json(force=True) or {}
    title = str(body.get("title", "")).strip()
    if not title:
      return _bad("title is required")
    loot_type = str(body.get("loot_type", "other")).lower()
    if loot_type not in VALID_LOOT_TYPES:
      return _bad(f"loot_type must be one of: {', '.join(sorted(VALID_LOOT_TYPES))}")
    loot = {
      "loot_type": loot_type,
      "title": title,
      "content": str(body.get("content", "")).strip(),
      "path": str(body.get("path", "")).strip(),
      "host": str(body.get("host", "")).strip(),
      "source_tool": str(body.get("source_tool", "")).strip(),
      "tags": body.get("tags", []) if isinstance(body.get("tags"), list) else [],
      "notes": str(body.get("notes", "")).strip(),
    }
    session_id = str(body.get("session_id", "")).strip() or None
    loot_id = db.add_loot(loot, session_id=session_id)
    stored = db.get_loot(loot_id)
    return jsonify({"success": True, "loot": stored}), 201
  except Exception as e:
    logger.error("Error adding loot: %s", e)
    return _bad(str(e), 500)


@api_loot_bp.route("/api/loot/<loot_id>", methods=["GET"])
def get_loot(loot_id: str):
  """Get a single loot item by ID."""
  try:
    item = db.get_loot(loot_id)
    if not item:
      return _bad("Loot item not found", 404)
    return jsonify({"success": True, "loot": item})
  except Exception as e:
    logger.error("Error getting loot %s: %s", loot_id, e)
    return _bad(str(e), 500)


@api_loot_bp.route("/api/loot/<loot_id>", methods=["PATCH"])
def update_loot(loot_id: str):
  """Update a loot item."""
  try:
    if not db.get_loot(loot_id):
      return _bad("Loot item not found", 404)
    body = request.get_json(force=True) or {}
    allowed = {"loot_type", "title", "content", "path", "host", "source_tool", "tags", "notes", "session_id"}
    updates = {k: v for k, v in body.items() if k in allowed}
    if "loot_type" in updates and updates["loot_type"] not in VALID_LOOT_TYPES:
      return _bad(f"loot_type must be one of: {', '.join(sorted(VALID_LOOT_TYPES))}")
    db.update_loot(loot_id, **updates)
    return jsonify({"success": True, "loot": db.get_loot(loot_id)})
  except Exception as e:
    logger.error("Error updating loot %s: %s", loot_id, e)
    return _bad(str(e), 500)


@api_loot_bp.route("/api/loot/<loot_id>", methods=["DELETE"])
def delete_loot(loot_id: str):
  """Delete a loot item."""
  try:
    if not db.get_loot(loot_id):
      return _bad("Loot item not found", 404)
    db.delete_loot(loot_id)
    return jsonify({"success": True, "loot_id": loot_id})
  except Exception as e:
    logger.error("Error deleting loot %s: %s", loot_id, e)
    return _bad(str(e), 500)
