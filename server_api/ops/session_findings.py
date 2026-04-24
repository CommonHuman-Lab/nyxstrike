"""
Session Findings API — per-session vulnerability/finding records.

Routes:
  GET    /api/sessions/<id>/findings                  list all findings
  POST   /api/sessions/<id>/findings                  add a finding
  PATCH  /api/sessions/<id>/findings/<finding_id>     update a finding
  DELETE /api/sessions/<id>/findings/<finding_id>     delete a finding
"""

import logging
import time
import uuid
from datetime import datetime
from flask import Blueprint, jsonify, request, Response

from server_core.session_flow import load_session_any, update_session, append_event

logger = logging.getLogger(__name__)

api_session_findings_bp = Blueprint("session_findings", __name__)

VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}


def _bad(msg: str, status: int = 400) -> Response:
  return jsonify({"success": False, "error": msg}), status  # type: ignore[return-value]


def _generate_finding_id() -> str:
  return f"finding_{uuid.uuid4().hex[:8]}"


# ── List findings ──────────────────────────────────────────────────────────────

@api_session_findings_bp.route("/api/sessions/<session_id>/findings", methods=["GET"])
def list_findings(session_id: str):
  """Return all findings for a session."""
  try:
    loaded = load_session_any(session_id)
    if not loaded:
      return _bad("Session not found", 404)
    session_data, _state = loaded
    findings = session_data.get("findings", [])
    if not isinstance(findings, list):
      findings = []
    return jsonify({"success": True, "findings": findings, "total": len(findings)})
  except Exception as e:
    logger.error(f"Error listing findings for {session_id}: {e}")
    return _bad(str(e), 500)


# ── Add finding ────────────────────────────────────────────────────────────────

@api_session_findings_bp.route("/api/sessions/<session_id>/findings", methods=["POST"])
def add_finding(session_id: str):
  """Add a vulnerability/finding to a session."""
  try:
    loaded = load_session_any(session_id)
    if not loaded:
      return _bad("Session not found", 404)

    session_data, _state = loaded
    body = request.get_json(force=True) or {}

    title = str(body.get("title", "")).strip()
    if not title:
      return _bad("title is required")

    severity = str(body.get("severity", "info")).lower()
    if severity not in VALID_SEVERITIES:
      return _bad(f"severity must be one of: {', '.join(sorted(VALID_SEVERITIES))}")

    ts = int(time.time())
    finding = {
      "finding_id": _generate_finding_id(),
      "title": title,
      "severity": severity,
      "description": str(body.get("description", "")).strip(),
      "tool": str(body.get("tool", "")).strip(),
      "step_key": str(body.get("step_key", "")).strip(),
      "evidence": str(body.get("evidence", "")).strip(),
      "recommendation": str(body.get("recommendation", "")).strip(),
      "cve": str(body.get("cve", "")).strip(),
      "tags": body.get("tags", []) if isinstance(body.get("tags"), list) else [],
      "status": "open",
      "created_at": ts,
      "updated_at": ts,
    }

    findings = session_data.get("findings", [])
    if not isinstance(findings, list):
      findings = []
    findings.append(finding)

    # Recompute total_findings and risk_level
    risk_level = _compute_risk_level(findings)
    updated = update_session(session_id, {
      "findings": findings,
      "total_findings": len(findings),
      "risk_level": risk_level,
    })

    if updated:
      append_event(session_id, "finding_added", f"Finding added: {title} [{severity}]", {
        "finding_id": finding["finding_id"],
        "severity": severity,
        "tool": finding["tool"],
      })

    return jsonify({
      "success": True,
      "finding": finding,
      "total_findings": len(findings),
      "risk_level": risk_level,
      "timestamp": datetime.now().isoformat(),
    }), 201
  except Exception as e:
    logger.error(f"Error adding finding for {session_id}: {e}")
    return _bad(str(e), 500)


# ── Update finding ─────────────────────────────────────────────────────────────

@api_session_findings_bp.route("/api/sessions/<session_id>/findings/<finding_id>", methods=["PATCH"])
def update_finding(session_id: str, finding_id: str):
  """Update a specific finding."""
  try:
    loaded = load_session_any(session_id)
    if not loaded:
      return _bad("Session not found", 404)

    session_data, _state = loaded
    findings = session_data.get("findings", [])
    if not isinstance(findings, list):
      findings = []

    idx = next((i for i, f in enumerate(findings) if f.get("finding_id") == finding_id), None)
    if idx is None:
      return _bad("Finding not found", 404)

    body = request.get_json(force=True) or {}
    finding = dict(findings[idx])

    allowed = {"title", "severity", "description", "tool", "step_key", "evidence",
               "recommendation", "cve", "tags", "status"}
    for k, v in body.items():
      if k not in allowed:
        continue
      if k == "severity" and str(v).lower() not in VALID_SEVERITIES:
        return _bad(f"severity must be one of: {', '.join(sorted(VALID_SEVERITIES))}")
      finding[k] = v

    finding["updated_at"] = int(time.time())
    findings[idx] = finding

    risk_level = _compute_risk_level(findings)
    update_session(session_id, {
      "findings": findings,
      "total_findings": len(findings),
      "risk_level": risk_level,
    })

    return jsonify({
      "success": True,
      "finding": finding,
      "timestamp": datetime.now().isoformat(),
    })
  except Exception as e:
    logger.error(f"Error updating finding {finding_id} for {session_id}: {e}")
    return _bad(str(e), 500)


# ── Delete finding ─────────────────────────────────────────────────────────────

@api_session_findings_bp.route("/api/sessions/<session_id>/findings/<finding_id>", methods=["DELETE"])
def delete_finding(session_id: str, finding_id: str):
  """Delete a specific finding."""
  try:
    loaded = load_session_any(session_id)
    if not loaded:
      return _bad("Session not found", 404)

    session_data, _state = loaded
    findings = session_data.get("findings", [])
    if not isinstance(findings, list):
      findings = []

    orig_len = len(findings)
    findings = [f for f in findings if f.get("finding_id") != finding_id]
    if len(findings) == orig_len:
      return _bad("Finding not found", 404)

    risk_level = _compute_risk_level(findings)
    update_session(session_id, {
      "findings": findings,
      "total_findings": len(findings),
      "risk_level": risk_level,
    })

    return jsonify({
      "success": True,
      "finding_id": finding_id,
      "total_findings": len(findings),
      "risk_level": risk_level,
      "timestamp": datetime.now().isoformat(),
    })
  except Exception as e:
    logger.error(f"Error deleting finding {finding_id} for {session_id}: {e}")
    return _bad(str(e), 500)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _compute_risk_level(findings: list) -> str:
  """Derive risk level from findings severity."""
  if not findings:
    return "unknown"
  severities = {f.get("severity", "info") for f in findings if isinstance(f, dict)}
  for level in ("critical", "high", "medium", "low"):
    if level in severities:
      return level
  return "info"
