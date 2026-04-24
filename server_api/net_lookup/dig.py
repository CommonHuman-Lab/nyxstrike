from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_net_lookup_dig_bp = Blueprint("api_net_lookup_dig", __name__)

_RECORD_TYPES = ["A", "MX", "NS", "TXT"]


def _dig(target: str, record_type: str, timeout: int) -> str:
    """Run a single dig +short query and return stdout (or stderr on failure)."""
    cmd = f"dig +short {record_type} {target}"
    result = execute_command(cmd, use_cache=False, timeout=timeout)
    output = (result.get("stdout") or "").strip()
    if not output and result.get("stderr", "").strip():
        output = result.get("stderr", "").strip()
    return output


@api_net_lookup_dig_bp.route("/api/tools/dig", methods=["POST"])
def dig():
    """
    DNS record lookup using dig +short.

    Queries A, MX, NS, and TXT records (or a specific type if requested).

    Expects JSON:
        { "target": "example.com" }

    Optional:
        { "record_types": ["A", "MX", "NS", "TXT"] }  — subset to query
        { "timeout": 15 }                              — per-query timeout in seconds

    Returns:
        {
            "success": bool,
            "target":  "example.com",
            "records": {
                "A":   "93.184.216.34",
                "MX":  "0 .",
                "NS":  "a.iana-servers.net.\nb.iana-servers.net.",
                "TXT": "\"v=spf1 -all\""
            },
            "output":  "<formatted multi-section string>"
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"success": False, "error": "Missing 'target' parameter"}), 400

    requested = data.get("record_types", _RECORD_TYPES)
    # Sanitise — only allow known record types
    record_types = [r.upper() for r in requested if r.upper() in _RECORD_TYPES]
    if not record_types:
        record_types = _RECORD_TYPES

    timeout = int(data.get("timeout", 15))

    logger.info("dig: target=%r types=%s", target, record_types)

    records = {}
    sections = []
    for rtype in record_types:
        output = _dig(target, rtype, timeout)
        records[rtype] = output
        sections.append(f"[{rtype} Records]\n{output}")

    formatted = "\n\n".join(sections)

    return jsonify({
        "success": True,
        "target": target,
        "records": records,
        "output": formatted,
    })
