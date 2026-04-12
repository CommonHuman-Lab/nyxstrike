"""
server_api/ai_assist/llm_agent_api.py

Flask blueprint for the LLM agent endpoints.

Endpoints:
  POST /api/intelligence/analyze-session
      Analyse an existing NyxStrike workflow session with the LLM.
      Body: { "session_id": "sess_<hex>" }

  GET  /api/intelligence/llm-agent-scan/<session_id>
      Retrieve results for a past LLM analysis session.

  GET  /api/intelligence/llm-agent-sessions
      List recent LLM agent sessions (default: last 50).

  GET  /api/intelligence/llm-status
      Report LLM backend availability and configuration.
"""

import logging

from flask import Blueprint, jsonify, request

from server_core.singletons import db, llm_client, run_history

logger = logging.getLogger(__name__)

api_ai_assist_llm_agent_bp = Blueprint("api_ai_assist_llm_agent", __name__)


@api_ai_assist_llm_agent_bp.route(
  "/api/intelligence/analyze-session",
  methods=["POST"],
)
def analyze_session_endpoint():
  """Analyse an existing NyxStrike workflow session using the LLM.

  Reads the session's tool run logs, sends them to the LLM for
  interpretation, and persists structured findings to NyxStrikeDB.
  The LLM does not dispatch any tools — this is a pure analysis pass.

  Request body (JSON):
    session_id (str): A ``sess_`` prefixed session ID from SessionStore.

  Returns:
    JSON with llm_session_id, session_id, target, objective, risk_level,
    summary, vulnerabilities, logs_analysed, full_response.
  """
  try:
    body = request.get_json(silent=True) or {}
    session_id = (body.get("session_id") or "").strip()

    if not session_id:
      return jsonify({"success": False, "error": "session_id is required"}), 400

    import uuid as _uuid
    from server_core.llm_agent import analyze_session
    from server_core.process_manager import AITaskManager

    task_id = f"ai_analyze_{_uuid.uuid4().hex[:8]}"
    AITaskManager.register_task(task_id, "ai_analyze_session", session_id=session_id)
    cancelled = False
    try:
      result = analyze_session(
        session_id=session_id,
        llm_client=llm_client,
        db=db,
        run_history=run_history,
      )
      cancelled = AITaskManager.is_cancelled(task_id)
    finally:
      AITaskManager.unregister_task(task_id)

    if cancelled:
      return jsonify({"success": False, "error": "Analysis was cancelled"}), 200

    status_code = 200 if result.get("success") else 502
    return jsonify(result), status_code

  except Exception as exc:
    logger.exception("analyze_session_endpoint: unexpected error")
    return jsonify({"success": False, "error": str(exc)}), 500


@api_ai_assist_llm_agent_bp.route(
  "/api/intelligence/llm-agent-scan/<session_id>",
  methods=["GET"],
)
def llm_agent_scan_result(session_id: str):
  """Retrieve a past LLM agent scan session and its findings."""
  try:
    if db is None:
      return jsonify({"success": False, "error": "Database not available"}), 503

    session = db.get_llm_session(session_id)
    if not session:
      return jsonify({"success": False, "error": f"Session '{session_id}' not found"}), 404

    vulnerabilities = db.get_llm_vulnerabilities(session_id)

    return jsonify({
      "success": True,
      "session": session,
      "vulnerabilities": vulnerabilities,
    })

  except Exception as exc:
    logger.exception("llm_agent_api: error fetching session %r", session_id)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_ai_assist_llm_agent_bp.route("/api/intelligence/llm-agent-sessions", methods=["GET"])
def llm_agent_sessions():
  """List recent LLM agent scan sessions."""
  try:
    if db is None:
      return jsonify({"success": False, "error": "Database not available"}), 503

    limit = min(int(request.args.get("limit", 50)), 200)
    sessions = db.list_llm_sessions(limit=limit)
    return jsonify({"success": True, "sessions": sessions, "count": len(sessions)})

  except Exception as exc:
    logger.exception("llm_agent_api: error listing sessions")
    return jsonify({"success": False, "error": str(exc)}), 500


@api_ai_assist_llm_agent_bp.route("/api/intelligence/llm-status", methods=["GET"])
def llm_status():
  """Report LLM backend availability and configuration."""
  try:
    status = llm_client.status()
    return jsonify({"success": True, **status})
  except Exception as exc:
    logger.exception("llm_agent_api: error in /llm-status")
    return jsonify({"success": False, "error": str(exc)}), 500
