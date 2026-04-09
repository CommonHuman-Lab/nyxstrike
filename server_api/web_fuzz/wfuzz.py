from flask import Blueprint, request, jsonify
import logging
import shlex
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)
DEFAULT_WFUZZ_WORDLIST = "/usr/share/wfuzz/wordlist/general/common.txt"

api_web_fuzz_wfuzz_bp = Blueprint("api_web_fuzz_wfuzz", __name__)


@api_web_fuzz_wfuzz_bp.route("/api/tools/wfuzz", methods=["POST"])
def wfuzz():
    """Execute Wfuzz for web application fuzzing with enhanced logging"""
    try:
        params = request.get_json(silent=True) or {}
        url = params.get("url", "")
        wordlist = params.get("wordlist", DEFAULT_WFUZZ_WORDLIST)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Wfuzz called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        target_url = url
        # Wfuzz normally requires a FUZZ placeholder in URL/data/header unless using all-params mode (-V).
        if "FUZZ" not in target_url and "FUZ" not in target_url and " -V" not in f" {additional_args} ":
            target_url = f"{target_url.rstrip('/')}/FUZZ"

        default_args = "-c --hc 404"
        effective_args = f"{default_args} {additional_args}".strip()
        command = f"wfuzz {effective_args} -z file,{shlex.quote(wordlist)} {shlex.quote(target_url)}"

        logger.info(f"🔍 Starting Wfuzz scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Wfuzz scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in wfuzz endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
