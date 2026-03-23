from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_binary_analysis_strings_bp = Blueprint("api_binary_analysis_strings", __name__)


@api_binary_analysis_strings_bp.route("/api/tools/strings", methods=["POST"])
def strings():
    """Extract strings from a binary file with enhanced logging"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        min_len = params.get("min_len", 4)
        additional_args = params.get("additional_args", "")

        if not file_path:
            logger.warning("🔧 Strings called without file_path parameter")
            return jsonify({
                "error": "File path parameter is required"
            }), 400

        command = f"strings -n {min_len}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {file_path}"

        logger.info(f"🔧 Starting Strings extraction: {file_path}")
        result = execute_command(command)
        logger.info(f"📊 Strings extraction completed for {file_path}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in strings endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
