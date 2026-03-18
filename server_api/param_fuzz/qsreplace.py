from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_param_fuzz_qsreplace_bp = Blueprint("api_param_fuzz_qsreplace", __name__)


@api_param_fuzz_qsreplace_bp.route("/api/tools/qsreplace", methods=["POST"])
def qsreplace():
    """Execute qsreplace for query string parameter replacement"""
    try:
        params = request.json
        urls = params.get("urls", "")
        replacement = params.get("replacement", "FUZZ")
        additional_args = params.get("additional_args", "")

        if not urls:
            logger.warning("🌐 qsreplace called without URLs")
            return jsonify({"error": "URLs parameter is required"}), 400

        command = f"echo '{urls}' | qsreplace '{replacement}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info("🔄 Starting qsreplace parameter replacement")
        result = execute_command(command)
        logger.info("📊 qsreplace parameter replacement completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in qsreplace endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
