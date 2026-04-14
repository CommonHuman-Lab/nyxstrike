"""
server_api/ai_assist/ai_recon_session.py

POST /api/intelligence/ai-recon-session

Returns a standard recon pipeline as workflow_steps for a given
target.

Recon tools included:
  1. nmap         — service/version scan with default scripts
  2. whois        — domain registration and IP ownership info
  3. whatweb      — web technology fingerprinting
  4. http-headers — HTTP response headers (security headers, server info)
  5. dig          — DNS A, MX, NS, TXT records
"""

import logging
from flask import Blueprint, jsonify, request
from server_core.session_flow import create_session

logger = logging.getLogger(__name__)

api_ai_assist_ai_recon_session_bp = Blueprint("api_ai_assist_ai_recon_session", __name__)


def _build_ai_recon_steps(target: str) -> list:
    """
    Return the ordered recon pipeline as workflow_steps.
    """
    return [
        {
            "tool": "nmap",
            "parameters": {
                "target": target,
                "additional_args": "-sV -sC -T4 -p-",
            },
            "expected_outcome": "Service versions, and basic script results",
            "success_probability": 0.95,
            "execution_time_estimate": 60,
            "dependencies": [],
        },
        {
            "tool": "whois",
            "parameters": {
                "target": target,
            },
            "expected_outcome": "Domain registration, registrar, and IP ownership info",
            "success_probability": 0.95,
            "execution_time_estimate": 10,
            "dependencies": [],
        },
        {
            "tool": "whatweb",
            "parameters": {
                "url": target,
            },
            "expected_outcome": "Web technology fingerprint: CMS, frameworks, server headers",
            "success_probability": 0.90,
            "execution_time_estimate": 30,
            "dependencies": ["nmap"],
        },
        {
            "tool": "http-headers",
            "parameters": {
                "target": target,
                "https": False,
                "follow_redirects": True,
                "timeout": 10,
            },
            "expected_outcome": "HTTP response headers including security headers and server info",
            "success_probability": 0.92,
            "execution_time_estimate": 15,
            "dependencies": ["nmap"],
        },
        {
            "tool": "dig",
            "parameters": {
                "target": target,
                "record_types": ["A", "MX", "NS", "TXT"],
                "timeout": 15,
            },
            "expected_outcome": "DNS A, MX, NS, and TXT records including SPF/DKIM/DMARC",
            "success_probability": 0.95,
            "execution_time_estimate": 15,
            "dependencies": [],
        },
        {
            "tool": "nikto",
            "parameters": {
                "target": target,
                "additional_args": "-nointeractive",
            },
            "expected_outcome": "Common web server vulnerabilities and misconfigurations",
            "success_probability": 0.85,
            "execution_time_estimate": 60,
            "dependencies": ["whatweb", "http-headers"],
        }
    ]


@api_ai_assist_ai_recon_session_bp.route("/api/intelligence/ai-recon-session", methods=["POST"])
def ai_recon_session():
    """
    Build a standard AI Recon session for the given target.

    Expects JSON: { "target": "example.com", "create_session": false }

    When create_session is true, also persists the session via SessionStore
    and returns the session_id in the response. The ai_analyze_session step's
    session_id parameter is back-filled with the real session ID.

    Returns:
        {
            "success": true,
            "target": "example.com",
            "session_name": "AI Recon",
            "steps": [ ... ],
            "session_id": "sess_abc123"   # only when create_session=true
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"success": False, "error": "target is required"}), 400

    want_session = bool(data.get("create_session", False))

    logger.info(
        "ai_recon_session: building recon pipeline for target=%r create_session=%s",
        target, want_session,
    )

    steps = _build_ai_recon_steps(target)

    response: dict = {
        "success": True,
        "target": target,
        "session_name": "AI Recon",
        "steps": steps,
    }

    if want_session:
        session_dict = create_session(
            target=target,
            steps=steps,
            source="api",
            objective="ai-recon",
        )
        sid = session_dict["session_id"]
        # Back-fill the ai_analyze_session step's session_id parameter.
        for step in steps:
            if step.get("tool") == "ai_analyze_session":
                step["parameters"]["session_id"] = sid
        response["session_id"] = sid
        response["steps"] = steps

    return jsonify(response)
