"""
server_api/ai_assist/llm_agent_api.py

Flask blueprint for the LLM agent endpoints.

Endpoints:
  POST /api/intelligence/analyze-session
      Analyse an existing NyxStrike workflow session with the LLM.
      Body: { "session_id": "sess_<hex>" }

  POST /api/intelligence/follow-up-session
      Produce a prioritised follow-up action plan for a session.
      Body: { "session_id": "sess_<hex>", "save_to_notes": true }

  GET  /api/intelligence/llm-agent-scan/<session_id>
      Retrieve results for a past LLM analysis session.

  GET  /api/intelligence/llm-agent-sessions
      List recent LLM agent sessions (default: last 50).

  GET  /api/intelligence/llm-status
      Report LLM backend availability and configuration.
"""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, request

from server_core.singletons import db, llm_client, run_history, session_store

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
    save_to_notes = bool(body.get("save_to_notes", False))

    if not session_id:
      return jsonify({"success": False, "error": "session_id is required"}), 400

    import uuid as _uuid
    from server_core.llm_agent import analyze_session, format_analysis_md
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

    # ── Optionally save the analysis as a notes file ──────────────────────────
    saved_path: str | None = None
    if result.get("success") and save_to_notes:
      try:
        target = result.get("target", session_id)
        objective = result.get("objective", "")
        md_content = format_analysis_md(result, session_id, target, objective)
        base = f"analysis-{datetime.now().strftime('%Y-%m-%d')}"
        folder = "analysis"
        for i in range(20):
          name = base if i == 0 else f"{base}-{i + 1}"
          if not session_store.note_exists(session_id, name, folder):
            ok = session_store.save_note(session_id, name, md_content, folder)
            if ok:
              saved_path = f"notes/{folder}/{name}.md"
            break
        if saved_path is None:
          logger.warning("analyze_session_endpoint: could not find free filename for notes save")
      except Exception as save_exc:
        logger.error("analyze_session_endpoint: failed to save analysis to notes: %s", save_exc)

    response_body = dict(result)
    if saved_path:
      response_body["saved_path"] = saved_path

    status_code = 200 if result.get("success") else 502
    return jsonify(response_body), status_code

  except Exception as exc:
    logger.exception("analyze_session_endpoint: unexpected error")
    return jsonify({"success": False, "error": str(exc)}), 500


@api_ai_assist_llm_agent_bp.route(
  "/api/intelligence/follow-up-session",
  methods=["POST"],
)
def follow_up_session_endpoint():
  """Produce a prioritised follow-up action plan for an existing workflow session.

  Reads the session's tool run logs and existing findings, then asks the LLM
  to plan the next concrete tool invocations.  Optionally saves the plan as a
  markdown note under notes/follow-up/.

  Request body (JSON):
    session_id   (str):  A ``sess_`` prefixed session ID from SessionStore.
    save_to_notes (bool): If true, save the plan to notes/follow-up/.

  Returns:
    JSON with session_id, target, objective, summary, steps, next_steps,
    logs_analysed, saved_path (if saved), and success flag.
  """
  try:
    body = request.get_json(silent=True) or {}
    session_id = (body.get("session_id") or "").strip()
    save_to_notes = bool(body.get("save_to_notes", False))

    if not session_id:
      return jsonify({"success": False, "error": "session_id is required"}), 400

    import uuid as _uuid
    from server_core.llm_agent import follow_up_session, format_followup_md
    from server_core.process_manager import AITaskManager

    task_id = f"ai_followup_{_uuid.uuid4().hex[:8]}"
    AITaskManager.register_task(task_id, "ai_follow_up_session", session_id=session_id)
    cancelled = False
    try:
      result = follow_up_session(
        session_id=session_id,
        llm_client=llm_client,
        db=db,
        run_history=run_history,
      )
      cancelled = AITaskManager.is_cancelled(task_id)
    finally:
      AITaskManager.unregister_task(task_id)

    if cancelled:
      return jsonify({"success": False, "error": "Follow-up was cancelled"}), 200

    # ── Optionally save the plan as a notes file ──────────────────────────────
    saved_path: str | None = None
    if result.get("success") and save_to_notes:
      try:
        target = result.get("target", session_id)
        objective = result.get("objective", "")
        md_content = format_followup_md(result, session_id, target, objective)
        base = f"follow-up-{datetime.now().strftime('%Y-%m-%d')}"
        folder = "follow-up"
        for i in range(20):
          name = base if i == 0 else f"{base}-{i + 1}"
          if not session_store.note_exists(session_id, name, folder):
            ok = session_store.save_note(session_id, name, md_content, folder)
            if ok:
              saved_path = f"notes/{folder}/{name}.md"
            break
        if saved_path is None:
          logger.warning("follow_up_session_endpoint: could not find free filename for notes save")
      except Exception as save_exc:
        logger.error("follow_up_session_endpoint: failed to save follow-up to notes: %s", save_exc)

    response_body = dict(result)
    if saved_path:
      response_body["saved_path"] = saved_path

    status_code = 200 if result.get("success") else 502
    return jsonify(response_body), status_code

  except Exception as exc:
    logger.exception("follow_up_session_endpoint: unexpected error")
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
