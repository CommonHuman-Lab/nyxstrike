from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command
from server_core.singletons import COMMON_DIRB_PATH

logger = logging.getLogger(__name__)

api_web_fuzz_gobuster_bp = Blueprint("api_web_fuzz_gobuster", __name__)


@api_web_fuzz_gobuster_bp.route("/api/tools/gobuster", methods=["POST"])
def gobuster():
    """Execute gobuster with enhanced logging and intelligent error handling"""
    try:
        params = request.json
        url = params.get("url", "")
        mode = params.get("mode", "dir")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("Gobuster called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        if mode not in ["dir", "dns", "fuzz", "vhost"]:
            logger.warning(f"Invalid gobuster mode: {mode}")
            return jsonify({
                "error": f"Invalid mode: {mode}. Must be one of: dir, dns, fuzz, vhost"
            }), 400

        command = f"gobuster {mode} -u {url} -w {wordlist}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Gobuster {mode} scan: {url}")

        result = execute_command(command)

        logger.info(f"Gobuster scan completed for {url}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in gobuster endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
