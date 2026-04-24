"""
server_api/ai_assist/ai_profiling_session.py

POST /api/intelligence/ai-profiling-session

Target-aware adaptive profiling pipeline.  The tool selection is adjusted
based on whether the caller supplied a bare IPv4 address, a URL, or a domain
name.

Pipeline (always included):
  1. nmap         — service/version scan
  2. whois        — registration / ownership info
  3. whatweb      — web technology fingerprint  (skipped for bare IPs)
  4. http-headers — HTTP response headers       (skipped for bare IPs)
  5. dig          — DNS records                 (skipped for bare IPs)

Domain / URL only:
  6. subfinder    — passive subdomain enumeration
  7. theharvester — email & host harvesting

All target types:
  8. gobuster     — directory brute-force
  9. nikto        — web server vulnerability scan
 10. ai_analyze_session — AI analysis of collected results

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

api_ai_assist_ai_profiling_session_bp = Blueprint(
    "api_ai_assist_ai_profiling_session", __name__
)


def _classify_target(target: str) -> str:
    """Return 'ip', 'url', or 'domain'."""
    if _IPV4_RE.match(target):
        return "ip"
    if target.startswith("http://") or target.startswith("https://") or "/" in target:
        return "url"
    return "domain"


def _build_ai_profiling_steps(target: str, target_type: str) -> list:
    """
    Return the ordered profiling pipeline as workflow_steps, adapted to
    the target type.
    """
    # Gobuster and HTTP tools want a proper URL prefix.
    web_target = (
        target
        if target.startswith("http://") or target.startswith("https://")
        else f"http://{target}"
    )
    # Domain tools want a bare hostname / domain.
    domain_target = (
        target
        .replace("http://", "")
        .replace("https://", "")
        .split("/")[0]
    )

    steps = [
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
            "parameters": {"target": target},
            "expected_outcome": "Domain registration, registrar, and IP ownership info",
            "success_probability": 0.95,
            "execution_time_estimate": 10,
            "dependencies": [],
        },
    ]

    # Web-facing / domain targets get richer HTTP + DNS enumeration.
    if target_type in ("domain", "url"):
        steps += [
            {
                "tool": "whatweb",
                "parameters": {"url": web_target},
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
                "expected_outcome": "HTTP response headers including security headers",
                "success_probability": 0.92,
                "execution_time_estimate": 15,
                "dependencies": ["nmap"],
            },
            {
                "tool": "dig",
                "parameters": {
                    "target": domain_target,
                    "record_types": ["A", "MX", "NS", "TXT"],
                    "timeout": 15,
                },
                "expected_outcome": "DNS A, MX, NS, and TXT records",
                "success_probability": 0.95,
                "execution_time_estimate": 15,
                "dependencies": [],
            },
            {
                "tool": "subfinder",
                "parameters": {"domain": domain_target},
                "expected_outcome": "Passive subdomain enumeration results",
                "success_probability": 0.88,
                "execution_time_estimate": 45,
                "dependencies": [],
            },
            {
                "tool": "theharvester",
                "parameters": {"domain": domain_target},
                "expected_outcome": "Email addresses and hostnames from public sources",
                "success_probability": 0.85,
                "execution_time_estimate": 60,
                "dependencies": [],
            },
        ]

    steps += [
        {
            "tool": "gobuster",
            "parameters": {
                "url": web_target,
                "mode": "dir",
                "wordlist": "/usr/share/wordlists/dirb/common.txt",
            },
            "expected_outcome": "Hidden directories and files on the web server",
            "success_probability": 0.88,
            "execution_time_estimate": 90,
            "dependencies": ["nmap"],
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
            "dependencies": ["nmap"],
        }
    ]

    return steps


@api_ai_assist_ai_profiling_session_bp.route(
    "/api/intelligence/ai-profiling-session", methods=["POST"]
)
def ai_profiling_session():
    """
    Build a target-aware AI Profiling session for the given target.

    Expects JSON:
        {
            "target": "example.com",
            "create_session": false   // optional, default false
        }

    When create_session is true, the session is persisted and session_id is
    returned in the response.  The ai_analyze_session step's session_id
    parameter is back-filled with the real session ID.

    Returns:
        {
            "success": true,
            "target": "example.com",
            "target_type": "domain",
            "session_name": "AI Profiling",
            "steps": [ ... ],
            "session_id": "sess_abc123"   // only when create_session=true
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"success": False, "error": "target is required"}), 400

    want_session = bool(data.get("create_session", False))
    target_type = _classify_target(target)

    logger.info(
        "ai_profiling_session: building pipeline for target=%r type=%s create_session=%s",
        target, target_type, want_session,
    )

    steps = _build_ai_profiling_steps(target, target_type)

    response: dict = {
        "success": True,
        "target": target,
        "target_type": target_type,
        "session_name": "AI Profiling",
        "steps": steps,
    }

    if want_session:
        session_dict = create_session(
            target=target,
            steps=steps,
            source="api",
            objective="ai-profiling",
        )
        sid = session_dict["session_id"]
        for step in steps:
            if step.get("tool") == "ai_analyze_session":
                step["parameters"]["session_id"] = sid
        response["session_id"] = sid
        response["steps"] = steps

    return jsonify(response)
