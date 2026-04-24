"""
server_api/ai_assist/ai_followup_session.py

POST /api/intelligence/ai-followup-session

LLM-driven next-step generator.  Loads an existing session's findings
(vulnerabilities, summary, risk_level, next_steps) and issues a single
LLM call asking it to produce a prioritised list of concrete follow-up
workflow steps.

The LLM response is parsed for structured tags:
  STEP: <tool_name> | PARAMS: <json-object> | REASON: <short rationale>

Each parsed tag becomes one element in the returned ``workflow_steps``
list (same shape as other AI session endpoints).

Optional:
  - create_session: if true, persists a new session from the generated
    steps and returns the new session_id.
"""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

from server_core.session_flow import create_session, load_session_any
from server_core.singletons import db, llm_client

logger = logging.getLogger(__name__)

api_ai_assist_ai_followup_session_bp = Blueprint(
    "api_ai_assist_ai_followup_session", __name__
)

# ── Tag parser ─────────────────────────────────────────────────────────────────
# STEP: <tool> | PARAMS: <json> | REASON: <text>
_STEP_RE = re.compile(
    r'STEP:\s*(?P<tool>[^|\n]+)\s*\|\s*PARAMS:\s*(?P<params>\{[^}]*\})\s*\|\s*REASON:\s*(?P<reason>[^\n]+)',
    re.IGNORECASE,
)

_FOLLOWUP_SYSTEM_PROMPT = """\
You are an expert penetration tester producing a prioritised follow-up action plan.

You will be given:
  - A target and objective
  - A risk level and executive summary from a prior automated scan
  - A list of discovered vulnerabilities (name, severity, description)
  - Optional recommended next tools already identified by the previous scan

Your task is to produce a SHORT, EXECUTABLE follow-up workflow (3–8 steps) using
only real security tools.  Each step must be on its own line in this exact format:

  STEP: <tool_name> | PARAMS: {"key": "value", ...} | REASON: <one-line rationale>

Rules:
  - tool_name must be an exact lowercase tool identifier (e.g. nuclei, sqlmap,
    dalfox, gobuster, ffuf, nikto, subfinder, theharvester, nmap, gau,
    waybackurls, wpscan, metasploit, john, hashcat).
  - PARAMS must be valid compact JSON (one line, no newlines inside).
  - REASON must be a single line; no newlines.
  - Output ONLY the STEP: lines — no prose, no markdown, no other text.
  - Order steps from highest to lowest impact.
  - Do NOT repeat a tool that already ran unless the parameters are meaningfully
    different (e.g. a different wordlist, different severity filter, new endpoint).
"""


def _parse_followup_steps(transcript: str, target: str) -> List[Dict[str, Any]]:
    """Parse STEP: tags from the LLM response into workflow_steps dicts."""
    steps = []
    for m in _STEP_RE.finditer(transcript):
        tool = m.group("tool").strip()
        reason = m.group("reason").strip()
        try:
            params = json.loads(m.group("params"))
        except (json.JSONDecodeError, ValueError):
            params = {}

        steps.append({
            "tool": tool,
            "parameters": params,
            "expected_outcome": reason,
            "success_probability": 0.80,
            "execution_time_estimate": 60,
            "dependencies": [],
        })
    return steps


@api_ai_assist_ai_followup_session_bp.route(
    "/api/intelligence/ai-followup-session", methods=["POST"]
)
def ai_followup_session():
    """
    Generate an LLM-driven follow-up workflow from an existing session's findings.

    Expects JSON:
        {
            "session_id": "sess_abc123",
            "create_session": false   // optional, default false
        }

    The endpoint:
      1. Loads the session and its findings (risk_level, summary, vulnerabilities,
         next_steps) from SessionStore.
      2. Sends a single LLM call asking for a prioritised follow-up plan.
      3. Parses ``STEP: … | PARAMS: … | REASON: …`` tags into workflow_steps.
      4. Optionally persists a new session from those steps.

    Returns:
        {
            "success": true,
            "source_session_id": "sess_abc123",
            "target": "example.com",
            "session_name": "AI Follow-up",
            "workflow_steps": [ ... ],
            "session_id": "sess_xyz789"   // only when create_session=true
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    source_session_id = (data.get("session_id") or "").strip()
    if not source_session_id:
        return jsonify({"success": False, "error": "session_id is required"}), 400

    want_session = bool(data.get("create_session", False))

    # ── Load source session ────────────────────────────────────────────────────
    loaded = load_session_any(source_session_id)
    if not loaded:
        return jsonify({
            "success": False,
            "error": f"Session '{source_session_id}' not found",
        }), 404

    session_dict, _ = loaded
    target = session_dict.get("target", "unknown")
    objective = session_dict.get("objective", "")
    risk_level = session_dict.get("risk_level", "UNKNOWN")
    summary = session_dict.get("summary", "")
    prior_next_steps: List[Dict] = session_dict.get("next_steps", [])
    tools_executed: List[str] = session_dict.get("tools_executed", [])

    # ── Check LLM availability ─────────────────────────────────────────────────
    if not llm_client.is_available():
        return jsonify({
            "success": False,
            "error": "LLM provider is not available. Check server settings.",
        }), 503

    # ── Pull vulnerability list from DB ────────────────────────────────────────
    vuln_lines: List[str] = []
    if db:
        try:
            # llm_sessions linked to this source session have a matching objective
            for ls in (db.get_llm_sessions_for_target(target) or []):
                if source_session_id not in str(ls.get("objective", "")):
                    continue
                lsid = ls.get("session_id", "")
                for v in (db.get_llm_vulnerabilities(lsid) or []):
                    name = v.get("vuln_name", "unknown")
                    sev = v.get("severity", "?")
                    desc = v.get("description", "")
                    vuln_lines.append(f"  [{sev}] {name}: {desc}")
        except Exception as exc:
            logger.warning("ai_followup_session: could not load vulns from DB: %s", exc)

    vuln_block = "\n".join(vuln_lines) if vuln_lines else "  (no structured vulnerabilities recorded)"

    prior_next_block = "\n".join(
        f"  {ns.get('tool', '?')}: {ns.get('reason', '')}"
        for ns in prior_next_steps
    ) or "  (none)"

    # ── Build LLM prompt ───────────────────────────────────────────────────────
    user_message = (
        f"Source session: {source_session_id}\n"
        f"Target: {target}\n"
        f"Objective: {objective or 'comprehensive security assessment'}\n"
        f"Tools already run: {', '.join(tools_executed) or 'N/A'}\n"
        f"Risk level: {risk_level}\n\n"
        f"Executive summary:\n{summary or '(none)'}\n\n"
        f"Discovered vulnerabilities:\n{vuln_block}\n\n"
        f"Previously recommended next steps:\n{prior_next_block}\n\n"
        "Based on the above, produce a prioritised follow-up action plan."
    )

    messages = [
        {"role": "system", "content": _FOLLOWUP_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    logger.info(
        "ai_followup_session: calling LLM for source_session=%r target=%r",
        source_session_id, target,
    )

    # ── Single LLM call ────────────────────────────────────────────────────────
    try:
        response = llm_client.chat(messages)
    except RuntimeError as exc:
        logger.error("ai_followup_session: LLM call failed: %s", exc)
        return jsonify({
            "success": False,
            "error": f"LLM call failed: {exc}",
        }), 500

    # ── Parse STEP: tags ───────────────────────────────────────────────────────
    workflow_steps = _parse_followup_steps(response, target)

    if not workflow_steps:
        logger.warning(
            "ai_followup_session: LLM returned no parseable STEP: tags for session=%r",
            source_session_id,
        )

    # ── Optionally persist the new follow-up session ───────────────────────────
    response_body: dict = {
        "success": True,
        "source_session_id": source_session_id,
        "target": target,
        "session_name": "AI Follow-up",
        "workflow_steps": workflow_steps,
    }

    if want_session and workflow_steps:
        new_session = create_session(
            target=target,
            steps=workflow_steps,
            source="api",
            objective=f"ai-followup:{source_session_id}",
        )
        response_body["session_id"] = new_session["session_id"]

    return jsonify(response_body)
