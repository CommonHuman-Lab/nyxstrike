from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_param_discovery_arjun_bp = Blueprint("api_param_discovery_arjun", __name__)


@api_param_discovery_arjun_bp.route("/api/tools/arjun", methods=["POST"])
def arjun():
    """Execute Arjun for HTTP parameter discovery with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        method = params.get("method", "GET")
        wordlist = params.get("wordlist", "")
        delay = params.get("delay", 0)
        threads = params.get("threads", 25)
        stable = params.get("stable", False)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Arjun called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"arjun -u {url} -m {method} -t {threads}"

        if wordlist:
            command += f" -w {wordlist}"

        if delay > 0:
            command += f" -d {delay}"

        if stable:
            command += " --stable"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🎯 Starting Arjun parameter discovery: {url}")
        result = execute_command(command)
        logger.info(f"📊 Arjun parameter discovery completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in arjun endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
