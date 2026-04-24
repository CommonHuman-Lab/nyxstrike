"""
Run History API

GET  /api/runs/history         — return the last N server-side tool executions (full)
GET  /api/runs/history/summary — return the last N entries with only id, tool,
                                  timestamp, success, execution_time (no stdout/stderr/params)
POST /api/runs/clear           — clear the run history
"""

import logging
from flask import Blueprint, jsonify, request

from server_core.singletons import run_history

logger = logging.getLogger(__name__)

api_runs_bp = Blueprint("api_runs", __name__)


@api_runs_bp.route("/api/runs/history", methods=["GET"])
def get_run_history():
  """Return the last N tool execution records (most-recent first), including full stdout/stderr."""
  try:
    limit = request.args.get("limit", type=int)
    entries = run_history.get_all()
    if limit and limit > 0:
      entries = entries[:limit]
    return jsonify({"success": True, "total": len(entries), "runs": entries})
  except Exception as e:
    logger.error(f"Error fetching run history: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_runs_bp.route("/api/runs/history/summary", methods=["GET"])
def get_run_history_summary():
  """Return lightweight run history — only id, tool, timestamp, success, execution_time.

  Omits stdout, stderr, and params so the dashboard can fetch recent run counts
  without paying the cost of large tool output payloads.
  """
  try:
    limit = request.args.get("limit", type=int)
    entries = run_history.get_all()
    if limit and limit > 0:
      entries = entries[:limit]
    summary = [
      {
        "id": e["id"],
        "tool": e.get("tool", "unknown"),
        "timestamp": e.get("timestamp", ""),
        "success": e.get("success", False),
        "execution_time": e.get("execution_time", 0.0),
      }
      for e in entries
    ]
    return jsonify({"success": True, "total": len(summary), "runs": summary})
  except Exception as e:
    logger.error(f"Error fetching run history summary: {e}")
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
