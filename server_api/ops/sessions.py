"""
Sessions API — durable session create/read/update + handover integration.
"""

import logging
import time
import json
import re
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, Response, stream_with_context

from server_core.singletons import session_store
from server_core.session_flow import (
  create_session,
  extract_workflow_steps,
  load_session_any,
  normalize_step,
  update_session,
)
from tool_registry import classify_intent
from server_core.singletons import llm_client as _llm_client

logger = logging.getLogger(__name__)

api_sessions_bp = Blueprint("sessions", __name__)


def _slugify(name: str) -> str:
  s = (name or "").strip().lower()
  s = re.sub(r"[^a-z0-9]+", "-", s)
  s = s.strip("-")
  return s or f"template-{uuid.uuid4().hex[:6]}"


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
  raw_steps = data.get("workflow_steps", [])
  workflow_steps = []
  if isinstance(raw_steps, list):
    target = data.get("target", "")
    for s in raw_steps:
      ns = normalize_step(s, target)
      if ns:
        workflow_steps.append(ns)
  return {
    "session_id": data.get("session_id", fallback_sid),
    "name": data.get("name", ""),
    "description": data.get("description", ""),
    "target": data.get("target", "unknown"),
    "status": data.get("status", "active"),
    "total_findings": data.get("total_findings", 0),
    "risk_level": data.get("risk_level", "unknown"),
    "iterations": data.get("iterations", 0),
    "tools_executed": data.get("tools_executed", []),
    "workflow_steps": workflow_steps if isinstance(workflow_steps, list) else [],
    "source": data.get("source", "legacy"),
    "objective": data.get("objective", ""),
    "metadata": data.get("metadata", {}),
    "handover_history": data.get("handover_history", []),
    "findings": data.get("findings", []),
    "event_log": data.get("event_log", []),
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
      name=data.get("name", ""),
      description=data.get("description", ""),
    )

    return jsonify({
      "success": True,
      "session": _summary_from_data(session, session.get("session_id", "")),
      "timestamp": datetime.now().isoformat(),
    })
  except Exception as e:
    logger.error(f"Error creating session: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/from-template", methods=["POST"])
@api_sessions_bp.route("/api/session-from-template", methods=["POST"])
def create_session_from_template():
  """Create durable session from a saved template id."""
  try:
    data = request.get_json(force=True) or {}
    target = str(data.get("target", "")).strip()
    template_id = str(data.get("template_id", "")).strip()
    if not target:
      return jsonify({"success": False, "error": "Target is required"}), 400
    if not template_id:
      return jsonify({"success": False, "error": "template_id is required"}), 400

    template = session_store.load_template(template_id)
    if not template:
      return jsonify({"success": False, "error": "Template not found"}), 404

    steps = template.get("workflow_steps", [])
    if not isinstance(steps, list):
      steps = []
    # Legacy fallback: template may only have tool names
    if len(steps) == 0 and isinstance(template.get("tools_executed"), list):
      steps = [{"tool": t, "parameters": {}} for t in template.get("tools_executed", [])]

    metadata = data.get("metadata", {}) if isinstance(data.get("metadata", {}), dict) else {}
    metadata = {
      **metadata,
      "template_id": template_id,
      "template_name": template.get("name", template_id),
      "mode": "from_template",
    }

    session = create_session(
      target=target,
      steps=steps,
      source=data.get("source", "web"),
      objective=data.get("objective", "from_template"),
      metadata=metadata,
      session_id=data.get("session_id"),
    )

    return jsonify({
      "success": True,
      "session": _summary_from_data(session, session.get("session_id", "")),
      "template": {
        "template_id": template_id,
        "name": template.get("name", template_id),
        "step_count": len(session.get("workflow_steps", [])),
      },
      "timestamp": datetime.now().isoformat(),
    })
  except Exception as e:
    logger.error(f"Error creating session from template: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
  """Return one session (active or completed) with full workflow details."""
  try:
    loaded = load_session_any(session_id)
    if not loaded:
      return jsonify({"success": False, "error": "Session not found"}), 404
    session_data, state = loaded
    cleaned_steps = []
    if isinstance(session_data.get("workflow_steps"), list):
      target = session_data.get("target", "")
      for s in session_data.get("workflow_steps", []):
        ns = normalize_step(s, target)
        if ns:
          cleaned_steps.append(ns)
      if cleaned_steps != session_data.get("workflow_steps", []):
        session_data["workflow_steps"] = cleaned_steps
        session_data["tools_executed"] = [s.get("tool", "") for s in cleaned_steps if isinstance(s, dict)]
        update_session(session_id, {"workflow_steps": cleaned_steps})
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
      "name",
      "description",
      "target",
      "status",
      "total_findings",
      "risk_level",
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


@api_sessions_bp.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
  """Delete a session from active or completed storage."""
  try:
    active_deleted = session_store.delete(session_id)
    completed_deleted = session_store.delete_completed(session_id)
    if not active_deleted and not completed_deleted:
      return jsonify({"success": False, "error": "Session not found"}), 404

    return jsonify({
      "success": True,
      "deleted": {
        "active": active_deleted,
        "completed": completed_deleted,
      },
      "session_id": session_id,
      "timestamp": datetime.now().isoformat(),
    })
  except Exception as e:
    logger.error(f"Error deleting session {session_id}: {e}")
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
      f"Objective: {session_data.get('objective', '')}",
      f"Tools: {', '.join(step_names)}",
      f"Findings: {session_data.get('total_findings', 0)}",
      f"Iterations: {session_data.get('iterations', 0)}",
      f"Metadata: {json.dumps(session_data.get('metadata', {}))}",
      f"Note: {note}",
      "Classify next best action for manual execution.",
    ])

    category, confidence = classify_intent(description, _llm_client if _llm_client.is_available() else None)
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


@api_sessions_bp.route("/api/sessions/templates", methods=["GET"])
@api_sessions_bp.route("/api/session-templates", methods=["GET"])
def list_session_templates():
  """List saved session templates."""
  try:
    templates = session_store.list_templates()
    return jsonify({"success": True, "templates": templates, "total": len(templates)})
  except Exception as e:
    logger.error(f"Error listing session templates: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/templates", methods=["POST"])
@api_sessions_bp.route("/api/session-templates", methods=["POST"])
def create_session_template():
  """Create template from provided workflow steps."""
  try:
    data = request.get_json(force=True) or {}
    name = str(data.get("name", "")).strip()
    steps = data.get("workflow_steps", [])
    source_session_id = str(data.get("source_session_id", "")).strip()
    if not name:
      return jsonify({"success": False, "error": "Template name is required"}), 400
    if not isinstance(steps, list) or len(steps) == 0:
      return jsonify({"success": False, "error": "workflow_steps is required"}), 400

    template_id = _slugify(name)
    if session_store.load_template(template_id):
      template_id = f"{template_id}-{uuid.uuid4().hex[:4]}"

    cleaned_steps = []
    for s in steps:
      ns = normalize_step(s, "")
      if ns:
        cleaned_steps.append(ns)

    template = {
      "template_id": template_id,
      "name": name,
      "workflow_steps": cleaned_steps,
      "source_session_id": source_session_id,
      "created_at": int(time.time()),
      "updated_at": int(time.time()),
    }
    ok = session_store.save_template(template_id, template)
    if not ok:
      return jsonify({"success": False, "error": "Failed saving template"}), 500

    return jsonify({"success": True, "template": template, "timestamp": datetime.now().isoformat()})
  except Exception as e:
    logger.error(f"Error creating session template: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/templates/<template_id>", methods=["PATCH"])
@api_sessions_bp.route("/api/session-templates/<template_id>", methods=["PATCH"])
def update_session_template(template_id):
  """Update an existing session template."""
  try:
    data = request.get_json(force=True) or {}
    has_name = "name" in data
    has_steps = "workflow_steps" in data
    if not has_name and not has_steps:
      return jsonify({"success": False, "error": "No update fields provided"}), 400

    name = str(data.get("name", "")).strip() if has_name else ""
    if has_name and not name:
      return jsonify({"success": False, "error": "Template name is required"}), 400

    raw_steps = data.get("workflow_steps", []) if has_steps else []
    if has_steps and not isinstance(raw_steps, list):
      return jsonify({"success": False, "error": "workflow_steps must be a list"}), 400

    cleaned_steps = []
    if has_steps:
      for s in raw_steps:
        ns = normalize_step(s, "")
        if ns:
          cleaned_steps.append(ns)
      if len(cleaned_steps) == 0:
        return jsonify({"success": False, "error": "workflow_steps is required"}), 400

    template = session_store.load_template(template_id)
    if not template:
      return jsonify({"success": False, "error": "Template not found"}), 404

    if has_name:
      template["name"] = name
    if has_steps:
      template["workflow_steps"] = cleaned_steps
    template["updated_at"] = int(time.time())
    ok = session_store.save_template(template_id, template)
    if not ok:
      return jsonify({"success": False, "error": "Failed updating template"}), 500

    return jsonify({"success": True, "template": template, "timestamp": datetime.now().isoformat()})
  except Exception as e:
    logger.error(f"Error updating session template {template_id}: {e}")
    return jsonify({"success": False, "error": str(e)}), 500


@api_sessions_bp.route("/api/sessions/templates/<template_id>", methods=["DELETE"])
@api_sessions_bp.route("/api/session-templates/<template_id>", methods=["DELETE"])
def delete_session_template(template_id):
  """Delete a session template."""
  try:
    ok = session_store.delete_template(template_id)
    if not ok:
      return jsonify({"success": False, "error": "Template not found"}), 404
    return jsonify({"success": True, "template_id": template_id, "timestamp": datetime.now().isoformat()})
  except Exception as e:
    logger.error(f"Error deleting session template {template_id}: {e}")
    return jsonify({"success": False, "error": str(e)}), 500
