from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_net_lookup_http_headers_bp = Blueprint("api_net_lookup_http_headers", __name__)


@api_net_lookup_http_headers_bp.route("/api/tools/http-headers", methods=["POST"])
def http_headers():
    """
    Fetch HTTP response headers for a target using curl -sI.

    Expects JSON:
        { "target": "example.com" }

    Optional:
        { "https": true }   — probe https:// instead of http://
        { "follow_redirects": false }  — disable --location (default: true)
        { "timeout": 10 }   — max-time in seconds (default: 10)

    Returns:
        {
            "success": bool,
            "output":  "<raw header string>",
            "headers": { "<Name>": "<value>", ... },
            "status_line": "HTTP/1.1 200 OK",
            "target": "http://example.com"
        }
    """
    data = request.get_json(force=True, silent=True) or {}
    target = (data.get("target") or "").strip()
    if not target:
        return jsonify({"success": False, "error": "Missing 'target' parameter"}), 400

    scheme = "https" if data.get("https") else "http"
    # Strip any existing scheme the caller may have included
    clean = target.replace("https://", "").replace("http://", "")
    url = f"{scheme}://{clean}"

    timeout = int(data.get("timeout", 10))
    follow = data.get("follow_redirects", True)

    cmd = f"curl -sI -k --max-time {timeout}"
    if follow:
        cmd += " --location"
    cmd += f" {url}"

    logger.info("http_headers: running %s", cmd)

    result = execute_command(cmd, use_cache=False, timeout=timeout + 5)
    success = result.get("success", False)
    raw = result.get("stdout", "") or ""
    if not success and result.get("stderr"):
        raw = raw + result.get("stderr", "")

    # Parse headers into a dict (last response block wins — handles redirects)
    headers, status_line = _parse_headers(raw)

    return jsonify({
        "success": success,
        "output": raw,
        "headers": headers,
        "status_line": status_line,
        "target": url,
    })


def _parse_headers(raw: str) -> tuple:
    """
    Parse the raw curl -I output into (headers_dict, status_line).
    When curl follows redirects, multiple response blocks are present;
    we keep only the final one.
    """
    # Split into per-response blocks (separated by blank lines between headers)
    blocks = []
    current: list = []
    for line in raw.splitlines():
        if line.strip() == "" and current:
            blocks.append(current)
            current = []
        else:
            current.append(line)
    if current:
        blocks.append(current)

    # Use the last non-empty block
    block = blocks[-1] if blocks else []

    status_line = block[0].strip() if block else ""
    headers: dict = {}
    for line in block[1:]:
        if ":" in line:
            name, _, value = line.partition(":")
            headers[name.strip()] = value.strip()

    return headers, status_line
