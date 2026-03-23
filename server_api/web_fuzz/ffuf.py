from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command
from server_core.singletons import COMMON_DIRB_PATH

logger = logging.getLogger(__name__)

api_web_fuzz_ffuf_bp = Blueprint("api_web_fuzz_ffuf", __name__)


@api_web_fuzz_ffuf_bp.route("/api/tools/ffuf", methods=["POST"])
def ffuf():
    """Execute FFuf web fuzzer with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        mode = params.get("mode", "directory")
        match_codes = params.get("match_codes", "200,204,301,302,307,401,403")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 FFuf called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"ffuf"

        if mode == "directory":
            command += f" -u {url}/FUZZ -w {wordlist}"
        elif mode == "vhost":
            command += f" -u {url} -H 'Host: FUZZ' -w {wordlist}"
        elif mode == "parameter":
            command += f" -u {url}?FUZZ=value -w {wordlist}"
        else:
            command += f" -u {url} -w {wordlist}"

        command += f" -mc {match_codes}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting FFuf {mode} fuzzing: {url}")
        result = execute_command(command)
        logger.info(f"📊 FFuf fuzzing completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in ffuf endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
