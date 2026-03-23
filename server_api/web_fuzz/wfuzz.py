from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command
from server_core.singletons import COMMON_DIRB_PATH

logger = logging.getLogger(__name__)

api_web_fuzz_wfuzz_bp = Blueprint("api_web_fuzz_wfuzz", __name__)


@api_web_fuzz_wfuzz_bp.route("/api/tools/wfuzz", methods=["POST"])
def wfuzz():
    """Execute Wfuzz for web application fuzzing with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Wfuzz called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"wfuzz -w {wordlist} '{url}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Wfuzz scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Wfuzz scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in wfuzz endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
