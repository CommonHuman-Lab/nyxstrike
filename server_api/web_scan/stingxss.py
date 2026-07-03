from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_scan_stingxss_bp = Blueprint("api_web_scan_stingxss", __name__)


def _bool(val) -> bool:
    """Coerce UI values to bool. Handles True/False, 'true'/'false', 1/0."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() == "true"
    return bool(val)


@api_web_scan_stingxss_bp.route("/api/tools/stingxss", methods=["POST"])
def stingxss():
    """Execute StingXSS context-aware XSS scanner."""
    try:
        params = request.json or {}
        url = params.get("url", "")
        if not url:
            return jsonify({"error": "url parameter is required"}), 400

        command = f"stingxss -u {url}"

        data = params.get("data", "")
        if data:
            command += f" -d {data!r}"

        for key, val in (params.get("headers") or {}).items():
            command += f" -H {key}:{val!r}"

        cookies = params.get("cookies", "")
        if cookies:
            command += f" -c {cookies!r}"

        proxy = params.get("proxy", "")
        if proxy:
            command += f" --proxy {proxy}"

        threads = params.get("threads", 5)
        if threads and int(threads) != 5:
            command += f" -t {int(threads)}"

        timeout = params.get("timeout", 15)
        if timeout and int(timeout) != 15:
            command += f" --timeout {int(timeout)}"

        level = params.get("level", 1)
        if level and int(level) != 1:
            command += f" --level {int(level)}"

        if _bool(params.get("crawl")):
            command += " --crawl"

        max_pages = params.get("max_pages", 50)
        if max_pages and int(max_pages) != 50:
            command += f" --max-pages {int(max_pages)}"

        max_depth = params.get("max_depth", 3)
        if max_depth and int(max_depth) != 3:
            command += f" --max-depth {int(max_depth)}"

        blind_callback = params.get("blind_callback", "")
        if blind_callback:
            command += f" --blind {blind_callback}"

        if _bool(params.get("browser")):
            command += " --browser"
            if not _bool(params.get("browser_headless", True)):
                command += " --no-browser-headless"

        if _bool(params.get("test_stored")):
            command += " --test-stored"

        if _bool(params.get("poc")):
            command += " --poc"

        for header in (params.get("inject_headers") or []):
            command += f" --inject-headers {header}"

        custom_payloads = params.get("custom_payloads") or []
        if custom_payloads:
            # custom_payloads is a list — only supported via file; skip if list provided directly
            pass

        if not _bool(params.get("probe_filter", True)):
            command += " --no-probe-filter"

        if _bool(params.get("graphql")):
            command += " --graphql"

        if _bool(params.get("websocket")):
            command += " --websocket"

        additional_args = params.get("additional_args", "")
        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting StingXSS scan: {url}")
        result = execute_command(command, use_recovery=True)
        # Exit code 1 = findings found (not an error) — treat as success
        if result.get("return_code") == 1:
            result["success"] = True
        logger.info(f"StingXSS scan completed for {url}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in stingxss endpoint: {e}")
        return jsonify({"error": f"Server error: {e}"}), 500
