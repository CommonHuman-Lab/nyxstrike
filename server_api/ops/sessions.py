"""
Sessions API — durable session create/read/update + handover integration.
"""

import logging
import time
import json
from datetime import datetime
from flask import Blueprint, jsonify, request, Response, stream_with_context

from server_core.singletons import session_store
from server_core.session_flow import (
  create_session,
  extract_workflow_steps,
  load_session_any,
  update_session,
)
from tool_registry import classify_intent

logger = logging.getLogger(__name__)

api_sessions_bp = Blueprint("sessions", __name__)


def _build_sessions_payload():
  active_ids = session_store.list_active()
  active = []
  for sid in active_ids:
    data = session_store.load(sid)
    if data:
      active.append(_summary_from_data(data, sid))

  completed_raw = session_store.list_completed()
  completed = []
  for item in completed_raw:
    sid = item.get("session_id", "")
    full = session_store.load_completed(sid) if sid else None
    completed.append(_summary_from_data(full or item, sid))

  return {
    "success": True,
    "active": active,
    "completed": completed,
    "total_active": len(active),
    "total_completed": len(completed),
  }

def _summary_from_data(data, fallback_sid):
  workflow_steps = data.get("workflow_steps", [])
  return {
    "session_id": data.get("session_id", fallback_sid),
    "target": data.get("target", "unknown"),
    "status": data.get("status", "active"),
    "total_findings": data.get("total_findings", 0),
    "iterations": data.get("iterations", 0),
    "tools_executed": data.get("tools_executed", []),
    "workflow_steps": workflow_steps if isinstance(workflow_steps, list) else [],
    "source": data.get("source", "legacy"),
    "objective": data.get("objective", ""),
    "metadata": data.get("metadata", {}),
    "handover_history": data.get("handover_history", []),
    "created_at": data.get("created_at", 0),
    "updated_at": data.get("updated_at", 0),
  }


@api_sessions_bp.route("/api/sessions", methods=["GET"])
def list_sessions():
  """Return active and completed scan sessions."""
  try:
    return jsonify(_build_sessions_payload())
  except Exception as e:
    logger.error(f"Error listing sessions: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/stream", methods=["GET"])
def stream_sessions():
  """SSE endpoint — streams session list updates every 2 seconds."""
  def generate():
    last_json = None
    while True:
      try:
        payload = _build_sessions_payload()
        js = json.dumps(payload, separators=(",", ":"))
        if js != last_json:
          yield f"data: {js}\n\n"
          last_json = js
        else:
          yield ": keepalive\n\n"
      except Exception as e:
        yield f"data: {{\"success\":false,\"error\":\"{str(e)}\"}}\n\n"
      time.sleep(2)

  return Response(
    stream_with_context(generate()),
    mimetype="text/event-stream",
    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
  )


@api_sessions_bp.route("/api/sessions", methods=["POST"])
def create_session_from_web_or_workflow():
  """Create a durable session. Accepts direct steps or workflow object."""
  try:
    data = request.get_json(force=True) or {}
    target = data.get("target", "")
    if not target:
      return jsonify({"success": False, "error": "Target is required"}), 400

    steps = data.get("workflow_steps")
    if not isinstance(steps, list):
      workflow_obj = data.get("workflow") or data.get("attack_chain") or {}
      if isinstance(workflow_obj, dict):
        if isinstance(workflow_obj.get("steps"), list):
          steps = workflow_obj.get("steps", [])
        else:
          steps = extract_workflow_steps(workflow_obj, target)
      else:
        steps = []

    session = create_session(
      target=target,
      steps=steps,
      source=data.get("source", "web"),
      objective=data.get("objective", ""),
      metadata=data.get("metadata", {}),
      session_id=data.get("session_id"),
    )

    return jsonify({
      "success": True,
      "session": _summary_from_data(session, session.get("session_id", "")),
      "timestamp": datetime.now().isoformat(),
    })
  except Exception as e:
    logger.error(f"Error creating session: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
  """Return one session (active or completed) with full workflow details."""
  try:
    loaded = load_session_any(session_id)
    if not loaded:
      return jsonify({"success": False, "error": "Session not found"}), 404
    session_data, state = loaded
    return jsonify({
      "success": True,
      "state": state,
      "session": _summary_from_data(session_data, session_id),
    })
  except Exception as e:
    logger.error(f"Error getting session {session_id}: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/<session_id>", methods=["PATCH"])
def patch_session(session_id):
  """Update persisted session details (target, status, workflow steps, findings, iterations)."""
  try:
    data = request.get_json(force=True) or {}
    allowed = {
      "target",
      "status",
      "total_findings",
      "iterations",
      "workflow_steps",
      "objective",
      "metadata",
      "source",
      "tools_executed",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    updated = update_session(session_id, updates)
    if not updated:
      return jsonify({"success": False, "error": "Session not found"}), 404

    return jsonify({
      "success": True,
      "session": _summary_from_data(updated, session_id),
      "timestamp": datetime.now().isoformat(),
    })
  except Exception as e:
    logger.error(f"Error updating session {session_id}: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/<session_id>/handover", methods=["POST"])
def handover_session(session_id):
  """Handover session context to LLM classification and store result in session history."""
  try:
    loaded = load_session_any(session_id)
    if not loaded:
      return jsonify({"success": False, "error": "Session not found"}), 404

    session_data, _state = loaded
    body = request.get_json(force=True) or {}
    note = body.get("note", "")

    step_names = [
      s.get("tool", "")
      for s in (session_data.get("workflow_steps", []) if isinstance(session_data.get("workflow_steps"), list) else [])
      if isinstance(s, dict)
    ]
    if not step_names:
      step_names = session_data.get("tools_executed", []) if isinstance(session_data.get("tools_executed"), list) else []

    description = "\n".join([
      f"Session ID: {session_id}",
      f"Target: {session_data.get('target', 'unknown')}",
      f"Status: {session_data.get('status', 'active')}",
      f"Tools: {', '.join(step_names)}",
      f"Findings: {session_data.get('total_findings', 0)}",
      f"Iterations: {session_data.get('iterations', 0)}",
      f"Note: {note}",
      "Classify next best action for manual execution.",
    ])

    category, confidence = classify_intent(description)
    handover_result = {
      "timestamp": datetime.now().isoformat(),
      "session_id": session_id,
      "category": category,
      "confidence": confidence,
      "note": note,
    }

    history = session_data.get("handover_history", [])
    if not isinstance(history, list):
      history = []
    history.append(handover_result)

    updated = update_session(session_id, {"handover_history": history})

    return jsonify({
      "success": True,
      "handover": handover_result,
      "session": _summary_from_data(updated or session_data, session_id),
    })
  except Exception as e:
    logger.error(f"Error handing over session {session_id}: {e}")
    return jsonify({"success": False, "error": str(e)}), 500
