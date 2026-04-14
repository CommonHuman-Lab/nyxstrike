"""
server_api/ai_assist/ai_vuln_session.py

POST /api/intelligence/ai-vuln-session

Vulnerability scanning pipeline for a given target URL or host.

Pipeline (in order):
  1. nuclei       — template-based CVE / misconfiguration detection
  2. sqlmap       — SQL injection discovery
  3. dalfox       — XSS vulnerability scanning
  4. nikto        — general web server vulnerability scanning
  5. ai_analyze_session — AI analysis of collected results

Optional:
  - create_session: if true, persists the session and back-fills
    ai_analyze_session's session_id parameter.
"""

import logging

from flask import Blueprint, jsonify, request

from server_core.session_flow import create_session

logger = logging.getLogger(__name__)

api_ai_assist_ai_vuln_session_bp = Blueprint(
    "api_ai_assist_ai_vuln_session", __name__
)


def _build_ai_vuln_steps(target: str) -> list:
    """
    Return the ordered vulnerability scanning pipeline as workflow_steps.
    """
    web_target = (
        target
        if target.startswith("http://") or target.startswith("https://")
        else f"http://{target}"
    )

    return [
        {
            "tool": "nuclei",
            "parameters": {
                "target": web_target,
                "severity": "critical,high,medium",
                "tags": "cve,rce,sqli,xss,lfi,ssrf",
            },
            "expected_outcome": "CVEs, misconfigurations, and critical vulnerabilities",
            "success_probability": 0.90,
            "execution_time_estimate": 120,
            "dependencies": [],
        },
        {
            "tool": "sqlmap",
            "parameters": {
                "url": web_target,
                "additional_args": "--batch --level=2 --risk=2",
            },
            "expected_outcome": "SQL injection vulnerabilities and exploitable parameters",
            "success_probability": 0.80,
            "execution_time_estimate": 90,
            "dependencies": [],
        },
        {
            "tool": "dalfox",
            "parameters": {
                "url": web_target,
                "mining_dom": True,
                "mining_dict": True,
            },
            "expected_outcome": "XSS injection points and reflected / stored XSS vulnerabilities",
            "success_probability": 0.82,
            "execution_time_estimate": 60,
            "dependencies": [],
        },
        {
            "tool": "nikto",
            "parameters": {
                "target": web_target,
                "additional_args": "-nointeractive",
            },
            "expected_outcome": "Common web server vulnerabilities and misconfigurations",
            "success_probability": 0.85,
            "execution_time_estimate": 60,
            "dependencies": [],
        }
    ]


@api_ai_assist_ai_vuln_session_bp.route(
    "/api/intelligence/ai-vuln-session", methods=["POST"]
)
def ai_vuln_session():
    """
    Build an AI Vulnerability Scan session for the given target.

    Expects JSON:
        {
            "target": "https://example.com",
            "create_session": false   // optional, default false
        }

    When create_session is true, the session is persisted and session_id is
    returned in the response.  The ai_analyze_session step's session_id
    parameter is back-filled with the real session ID.

    Returns:
        {
            "success": true,
            "target": "https://example.com",
            "session_name": "AI Vuln Scan",
            "steps": [ ... ],
            "session_id": "sess_abc123"   // only when create_session=true
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"success": False, "error": "target is required"}), 400

    want_session = bool(data.get("create_session", False))

    logger.info(
        "ai_vuln_session: building vuln pipeline for target=%r create_session=%s",
        target, want_session,
    )

    steps = _build_ai_vuln_steps(target)

    response: dict = {
        "success": True,
        "target": target,
        "session_name": "AI Vuln Scan",
        "steps": steps,
    }

    if want_session:
        session_dict = create_session(
            target=target,
            steps=steps,
            source="api",
            objective="ai-vuln-scan",
        )
        sid = session_dict["session_id"]
        for step in steps:
            if step.get("tool") == "ai_analyze_session":
                step["parameters"]["session_id"] = sid
        response["session_id"] = sid
        response["steps"] = steps

    return jsonify(response)
