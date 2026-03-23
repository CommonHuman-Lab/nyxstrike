"""
Run History API

GET  /api/runs/history  — return the last N server-side tool executions
POST /api/runs/clear    — clear the run history
"""

import logging
from flask import Blueprint, jsonify, request

from server_core.singletons import run_history

logger = logging.getLogger(__name__)

api_runs_bp = Blueprint("api_runs", __name__)


@api_runs_bp.route("/api/runs/history", methods=["GET"])
def get_run_history():
  """Return the last N tool execution records (most-recent first)."""
  try:
    limit = request.args.get("limit", type=int)
    entries = run_history.get_all()
    if limit and limit > 0:
      entries = entries[:limit]
    return jsonify({"success": True, "total": len(entries), "runs": entries})
  except Exception as e:
    logger.error(f"Error fetching run history: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_runs_bp.route("/api/runs/clear", methods=["POST"])
def clear_run_history():
  """Clear all server-side run history entries."""
  try:
    run_history.clear()
    return jsonify({"success": True})
  except Exception as e:
    logger.error(f"Error clearing run history: {e}")
    return jsonify({"success": False, "error": str(e)}), 500
