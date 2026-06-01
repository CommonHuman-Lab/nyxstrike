from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_scan_breachsql_bp = Blueprint("api_web_scan_breachsql", __name__)


def _bool(val) -> bool:
    """Coerce UI values to bool. Handles True/False, 'true'/'false', 1/0."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() == "true"
    return bool(val)


@api_web_scan_breachsql_bp.route("/api/tools/breachsql", methods=["POST"])
def breachsql():
    """Execute BreachSQL SQL injection scanner."""
    try:
        params = request.json or {}
        url = params.get("url", "")
        if not url:
            return jsonify({"error": "url parameter is required"}), 400

        command = f"breachsql -u {url}"

        data = params.get("data", "")
        if data:
            command += f" -d {data!r}"

        for header in (params.get("headers") or {}).items():
            command += f" -H {header[0]}:{header[1]!r}"

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

        dbms = params.get("dbms", "auto")
        if dbms and dbms != "auto":
            command += f" --dbms {dbms}"

        technique = params.get("technique", "EBTUO")
        if technique and technique != "EBTUO":
            command += f" --technique {technique}"

        time_threshold = params.get("time_threshold", 4)
        if time_threshold and int(time_threshold) != 4:
            command += f" --time-threshold {int(time_threshold)}"

        risk = params.get("risk", 1)
        if risk and int(risk) != 1:
            command += f" --risk {int(risk)}"

        path_params = params.get("path_params") or []
        if path_params:
            command += f" --path-params {','.join(path_params)}"

        cookie_params = params.get("cookie_params") or []
        if cookie_params:
            command += f" --cookie-params {','.join(cookie_params)}"

        header_params = params.get("header_params") or []
        if header_params:
            command += f" --header-params {','.join(header_params)}"

        if _bool(params.get("exploit")):
            command += " --exploit"

        dump = params.get("dump", "")
        if dump:
            command += f" --dump {dump}"

        if _bool(params.get("dump_all")):
            command += " --dump-all"

        if _bool(params.get("crawl")):
            command += " --crawl"

        max_pages = params.get("max_pages", 100)
        if max_pages and int(max_pages) != 100:
            command += f" --max-pages {int(max_pages)}"

        max_depth = params.get("max_depth", 3)
        if max_depth and int(max_depth) != 3:
            command += f" --max-depth {int(max_depth)}"

        additional_args = params.get("additional_args", "")
        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting BreachSQL scan: {url}")
        result = execute_command(command)
        # Exit code 1 = findings found (not an error) — treat as success
        if result.get("return_code") == 1:
            result["success"] = True
        logger.info(f"BreachSQL scan completed for {url}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in breachsql endpoint: {e}")
        return jsonify({"error": f"Server error: {e}"}), 500
