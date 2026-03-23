"""
Sessions API — list active and completed scan sessions from SessionStore.
"""

import logging
from flask import Blueprint, jsonify
from server_core.session_store import SessionStore

logger = logging.getLogger(__name__)

api_sessions_bp = Blueprint("sessions", __name__)

_store = SessionStore()


@api_sessions_bp.route("/api/sessions", methods=["GET"])
def list_sessions():
  """Return active and completed scan sessions."""
  try:
    active_ids = _store.list_active()
    active = []
    for sid in active_ids:
      data = _store.load(sid)
      if data:
        active.append({
          "session_id": data.get("session_id", sid),
          "target": data.get("target", "unknown"),
          "status": data.get("status", "active"),
          "total_findings": data.get("total_findings", 0),
          "iterations": data.get("iterations", 0),
          "tools_executed": data.get("tools_executed", []),
          "created_at": data.get("created_at", 0),
          "updated_at": data.get("updated_at", 0),
        })

    completed = _store.list_completed()

    return jsonify({
      "success": True,
      "active": active,
      "completed": completed,
      "total_active": len(active),
      "total_completed": len(completed),
    })
  except Exception as e:
    logger.error(f"Error listing sessions: {e}")
    return jsonify({"success": False, "error": str(e)}), 500
