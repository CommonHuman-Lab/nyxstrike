"""
server_api/ai_assist/ai_osint_session.py

POST /api/intelligence/ai-osint-session

Passive OSINT pipeline for domain targets.  Bare IPv4 addresses are
rejected with a 400 because OSINT tools require a domain or hostname.

Pipeline (in order):
  1. subfinder    — passive subdomain enumeration
  2. theharvester — email addresses and hostnames from public sources
  3. gau          — historical URLs from wayback, commoncrawl, otx, urlscan
  4. waybackurls  — Wayback Machine historical URL discovery
  5. ai_analyze_session — AI analysis of collected OSINT results

Optional:
  - create_session: if true, persists the session and back-fills
    ai_analyze_session's session_id parameter.
"""

import logging
import re

from flask import Blueprint, jsonify, request

from server_core.session_flow import create_session

logger = logging.getLogger(__name__)

_IPV4_RE = re.compile(
    r'^(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)$'
)

api_ai_assist_ai_osint_session_bp = Blueprint(
    "api_ai_assist_ai_osint_session", __name__
)


def _build_ai_osint_steps(domain: str) -> list:
    """
    Return the ordered OSINT pipeline as workflow_steps.
    """
    return [
        {
            "tool": "subfinder",
            "parameters": {"domain": domain},
            "expected_outcome": "Passively discovered subdomains",
            "success_probability": 0.88,
            "execution_time_estimate": 45,
            "dependencies": [],
        },
        {
            "tool": "theharvester",
            "parameters": {"domain": domain},
            "expected_outcome": "Email addresses and hostnames from public sources",
            "success_probability": 0.85,
            "execution_time_estimate": 60,
            "dependencies": [],
        },
        {
            "tool": "gau",
            "parameters": {
                "domain": domain,
                "include_subs": True,
            },
            "expected_outcome": "Historical URLs from Wayback Machine, CommonCrawl, OTX, and URLScan",
            "success_probability": 0.88,
            "execution_time_estimate": 60,
            "dependencies": [],
        },
        {
            "tool": "waybackurls",
            "parameters": {
                "domain": domain,
                "get_versions": False,
                "no_subs": False,
            },
            "expected_outcome": "Historical endpoint URLs from the Wayback Machine",
            "success_probability": 0.85,
            "execution_time_estimate": 45,
            "dependencies": [],
        }
    ]


@api_ai_assist_ai_osint_session_bp.route(
    "/api/intelligence/ai-osint-session", methods=["POST"]
)
def ai_osint_session():
    """
    Build an AI OSINT session for the given domain target.

    Expects JSON:
        {
            "target": "example.com",
            "create_session": false   // optional, default false
        }

    Bare IPv4 addresses are rejected — OSINT tools require a domain or
    hostname.

    When create_session is true, the session is persisted and session_id is
    returned in the response.  The ai_analyze_session step's session_id
    parameter is back-filled with the real session ID.

    Returns:
        {
            "success": true,
            "target": "example.com",
            "session_name": "AI OSINT",
            "steps": [ ... ],
            "session_id": "sess_abc123"   // only when create_session=true
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"success": False, "error": "target is required"}), 400

    # Strip scheme so we can do a clean IP check.
    bare = target.replace("http://", "").replace("https://", "").split("/")[0]
    if _IPV4_RE.match(bare):
        return jsonify({
            "success": False,
            "error": "OSINT tools require a domain or hostname, not a bare IP address",
        }), 400

    want_session = bool(data.get("create_session", False))
    domain = bare  # OSINT tools want the domain without scheme / path.

    logger.info(
        "ai_osint_session: building OSINT pipeline for target=%r create_session=%s",
        target, want_session,
    )

    steps = _build_ai_osint_steps(domain)

    response: dict = {
        "success": True,
        "target": target,
        "session_name": "AI OSINT",
        "steps": steps,
    }

    if want_session:
        session_dict = create_session(
            target=target,
            steps=steps,
            source="api",
            objective="ai-osint",
        )
        sid = session_dict["session_id"]
        for step in steps:
            if step.get("tool") == "ai_analyze_session":
                step["parameters"]["session_id"] = sid
        response["session_id"] = sid
        response["steps"] = steps

    return jsonify(response)
