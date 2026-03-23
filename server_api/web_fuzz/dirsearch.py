from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command
from server_core.singletons import COMMON_DIRSEARCH_PATH

logger = logging.getLogger(__name__)

api_web_fuzz_dirsearch_bp = Blueprint("api_web_fuzz_dirsearch", __name__)


@api_web_fuzz_dirsearch_bp.route("/api/tools/dirsearch", methods=["POST"])
def dirsearch():
    """Execute Dirsearch for advanced directory and file discovery with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        extensions = params.get("extensions", "php,html,js,txt,xml,json")
        wordlist = params.get("wordlist", COMMON_DIRSEARCH_PATH)
        threads = params.get("threads", 30)
        recursive = params.get("recursive", False)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Dirsearch called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"dirsearch -u {url} -e {extensions} -w {wordlist} -t {threads}"

        if recursive:
            command += " -r"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"📁 Starting Dirsearch scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Dirsearch scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in dirsearch endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
