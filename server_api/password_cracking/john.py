from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command
from server_core.singletons import ROCKYOU_PATH

logger = logging.getLogger(__name__)

api_password_cracking_john_bp = Blueprint("api_password_cracking_john", __name__)


@api_password_cracking_john_bp.route("/api/tools/john", methods=["POST"])
def john():
    """Execute john with enhanced logging"""
    try:
        params = request.json
        hash_file = params.get("hash_file", "")
        wordlist = params.get("wordlist", ROCKYOU_PATH)
        format_type = params.get("format", "")
        additional_args = params.get("additional_args", "")

        if not hash_file:
            logger.warning("🔐 John called without hash_file parameter")
            return jsonify({
                "error": "Hash file parameter is required"
            }), 400

        command = f"john"

        if format_type:
            command += f" --format={format_type}"

        if wordlist:
            command += f" --wordlist={wordlist}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {hash_file}"

        logger.info(f"🔐 Starting John the Ripper: {hash_file}")
        result = execute_command(command, tool="john")
        logger.info(f"📊 John the Ripper completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in john endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
