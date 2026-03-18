from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_param_discovery_x8_bp = Blueprint("api_param_discovery_x8", __name__)


@api_param_discovery_x8_bp.route("/api/tools/x8", methods=["POST"])
def x8():
    """Execute x8 for hidden parameter discovery with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/x8/params.txt")
        method = params.get("method", "GET")
        body = params.get("body", "")
        headers = params.get("headers", "")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 x8 called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"x8 -u {url} -w {wordlist} -X {method}"

        if body:
            command += f" -b '{body}'"

        if headers:
            command += f" -H '{headers}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting x8 parameter discovery: {url}")
        result = execute_command(command)
        logger.info(f"📊 x8 parameter discovery completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in x8 endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
