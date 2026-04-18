from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_scan_interactsh_bp = Blueprint("api_web_scan_interactsh", __name__)

@api_web_scan_interactsh_bp.route("/api/tools/web_scan/interactsh", methods=["POST"])
def interactsh():
    """Execute interactsh-client for OOB interaction capture"""
    try:
        params = request.json or {}
        server = params.get("server", "")
        token = params.get("token", "")
        n = params.get("n", 1)
        poll_interval = params.get("poll_interval", 5)
        timeout = params.get("timeout", 60)
        additional_args = params.get("additional_args", "")

        command = f"interactsh-client -json -n {n} -pi {poll_interval}"

        if server:
            command += f" -server {server}"
        if token:
            command += f" -token {token}"
        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔗 Starting interactsh-client (n={n}, poll_interval={poll_interval}s, timeout={timeout}s)")
        result = execute_command(command, timeout=timeout)
        logger.info("📊 interactsh-client completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in interactsh endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
