from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_scan_phaseaccess_bp = Blueprint("api_web_scan_phaseaccess", __name__)


def _bool(val) -> bool:
    """Coerce UI values to bool. Handles True/False, 'true'/'false', 1/0."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() == "true"
    return bool(val)


@api_web_scan_phaseaccess_bp.route("/api/tools/phaseaccess", methods=["POST"])
def phaseaccess():
    """Execute PhaseAccess IDOR/BOLA scanner."""
    try:
        params = request.json or {}
        target = params.get("target", "")
        if not target:
            return jsonify({"error": "target parameter is required"}), 400

        command = f"phaseaccess -u {target} --json -q"

        # ---- HTTP method / body ----
        method = params.get("method", "GET")
        if method and method != "GET":
            command += f" -X {method}"

        body = params.get("body", "")
        if body:
            command += f" -d {body!r}"

        # ---- Session A ----
        for key, val in (params.get("session_a_headers") or {}).items():
            command += f" -H {key}:{val!r}"

        session_a_cookies = params.get("session_a_cookies", "")
        if session_a_cookies:
            command += f" -c {session_a_cookies!r}"

        label_a = params.get("session_a_label", "")
        if label_a and label_a != "session_a":
            command += f" --label-a {label_a}"

        # ---- Session B ----
        for key, val in (params.get("session_b_headers") or {}).items():
            command += f" --header-b {key}:{val!r}"

        session_b_cookies = params.get("session_b_cookies", "")
        if session_b_cookies:
            command += f" --cookie-b {session_b_cookies!r}"

        label_b = params.get("session_b_label", "")
        if label_b:
            command += f" --label-b {label_b}"

        # ---- Form login — session A ----
        login_url = params.get("login_url", "")
        if login_url:
            command += f" --login-url {login_url}"

        login_user = params.get("login_user", "")
        if login_user:
            command += f" --login-user {login_user!r}"

        login_pass = params.get("login_pass", "")
        if login_pass:
            command += f" --login-pass {login_pass!r}"

        login_user_field = params.get("login_user_field", "")
        if login_user_field:
            command += f" --login-user-field {login_user_field}"

        login_pass_field = params.get("login_pass_field", "")
        if login_pass_field:
            command += f" --login-pass-field {login_pass_field}"

        # ---- Form login — session B ----
        login_url_b = params.get("login_url_b", "")
        if login_url_b:
            command += f" --login-url-b {login_url_b}"

        login_user_b = params.get("login_user_b", "")
        if login_user_b:
            command += f" --login-user-b {login_user_b!r}"

        login_pass_b = params.get("login_pass_b", "")
        if login_pass_b:
            command += f" --login-pass-b {login_pass_b!r}"

        # ---- Crawl ----
        if _bool(params.get("crawl")):
            command += " --crawl"

        crawl_depth = params.get("crawl_depth", 3)
        if crawl_depth and int(crawl_depth) != 3:
            command += f" --crawl-depth {int(crawl_depth)}"

        crawl_pages = params.get("crawl_pages", 100)
        if crawl_pages and int(crawl_pages) != 100:
            command += f" --crawl-pages {int(crawl_pages)}"

        if _bool(params.get("browser_crawl")):
            command += " --browser-crawl"

        if _bool(params.get("auto_login")):
            command += " --auto-login"

        # ---- OpenAPI / spec import ----
        openapi = params.get("openapi", "")
        if openapi:
            command += f" --openapi {openapi}"

        base_url = params.get("base_url", "")
        if base_url:
            command += f" --base-url {base_url}"

        # ---- HAR / Burp import ----
        targets_file = params.get("targets", "")
        if targets_file:
            command += f" --targets {targets_file}"

        # ---- Stored IDOR chaining ----
        chain_create = params.get("chain_create", "")
        if chain_create:
            command += f" --chain-create {chain_create}"

        chain_body = params.get("chain_body", "")
        if chain_body:
            command += f" --chain-body {chain_body!r}"

        chain_read = params.get("chain_read", "")
        if chain_read:
            command += f" --chain-read {chain_read}"

        # ---- Network / TLS ----
        proxy = params.get("proxy", "")
        if proxy:
            command += f" --proxy {proxy}"

        if not _bool(params.get("verify_ssl", True)):
            command += " --insecure"

        delay = params.get("delay", 0.0)
        if delay and float(delay) > 0:
            command += f" --delay {float(delay)}"

        threads = params.get("threads", 5)
        if threads and int(threads) != 5:
            command += f" -t {int(threads)}"

        timeout = params.get("timeout", 15)
        if timeout and int(timeout) != 15:
            command += f" --timeout {int(timeout)}"

        user_agent = params.get("user_agent", "")
        if user_agent:
            command += f" --user-agent {user_agent!r}"

        # ---- Scan tuning ----
        max_candidates = params.get("max_candidates", 10)
        if max_candidates and int(max_candidates) != 10:
            command += f" --max-candidates {int(max_candidates)}"

        min_confidence = params.get("min_confidence", "")
        if min_confidence:
            command += f" --min-confidence {min_confidence}"

        if not _bool(params.get("method_bypass", True)):
            command += " --no-method-bypass"

        if not _bool(params.get("param_pollution", True)):
            command += " --no-param-pollution"

        if not _bool(params.get("mass_assignment", True)):
            command += " --no-mass-assignment"

        if not _bool(params.get("soft_delete", True)):
            command += " --no-soft-delete"

        if not _bool(params.get("blind_idor", True)):
            command += " --no-blind-idor"

        for extra_url in (params.get("extra_urls") or []):
            command += f" --extra-url {extra_url}"

        additional_args = params.get("additional_args", "")
        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting PhaseAccess IDOR scan: {target}")
        result = execute_command(command, use_recovery=True)
        # Exit code 1 = findings found (not an error) — treat as success
        if result.get("return_code") == 1:
            result["success"] = True
        logger.info(f"PhaseAccess scan completed for {target}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in phaseaccess endpoint: {e}")
        return jsonify({"error": f"Server error: {e}"}), 500
