from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_data_processing_anew_bp = Blueprint("api_data_processing_anew", __name__)


@api_data_processing_anew_bp.route("/api/tools/anew", methods=["POST"])
def anew():
    """Execute anew for appending new lines to files (useful for data processing)"""
    try:
        params = request.json
        input_data = params.get("input_data", "")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not input_data:
            logger.warning("📝 Anew called without input data")
            return jsonify({"error": "Input data is required"}), 400

        if output_file:
            command = f"echo '{input_data}' | anew {output_file}"
        else:
            command = f"echo '{input_data}' | anew"

        if additional_args:
            command += f" {additional_args}"

        logger.info("📝 Starting anew data processing")
        result = execute_command(command)
        logger.info("📊 anew data processing completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in anew endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
