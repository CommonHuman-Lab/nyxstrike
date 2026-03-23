from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_binary_analysis_binwalk_bp = Blueprint("api_binary_analysis_binwalk", __name__)


@api_binary_analysis_binwalk_bp.route("/api/tools/binwalk", methods=["POST"])
def binwalk():
    """Execute Binwalk for firmware and file analysis with enhanced logging"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        extract = params.get("extract", False)
        additional_args = params.get("additional_args", "")

        if not file_path:
            logger.warning("🔧 Binwalk called without file_path parameter")
            return jsonify({
                "error": "File path parameter is required"
            }), 400

        command = "binwalk"

        if extract:
            command += " -e"

        if additional_args:
            command += f" {additional_args}"

        command += f" {file_path}"

        logger.info(f"🔧 Starting Binwalk analysis: {file_path}")
        result = execute_command(command)
        logger.info(f"📊 Binwalk analysis completed for {file_path}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in binwalk endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
