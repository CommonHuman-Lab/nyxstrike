from flask import Blueprint, request, jsonify
import logging
from pathlib import Path

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_file_carving_foremost_bp = Blueprint("api_file_carving_foremost", __name__)


@api_file_carving_foremost_bp.route("/api/tools/foremost", methods=["POST"])
def foremost():
    """Execute Foremost for file carving with enhanced logging"""
    try:
        params = request.json
        input_file = params.get("input_file", "")
        output_dir = params.get("output_dir", "/tmp/foremost_output")
        file_types = params.get("file_types", "")
        additional_args = params.get("additional_args", "")

        if not input_file:
            logger.warning("📁 Foremost called without input_file parameter")
            return jsonify({
                "error": "Input file parameter is required"
            }), 400

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        command = f"foremost -o {output_dir}"

        if file_types:
            command += f" -t {file_types}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {input_file}"

        logger.info(f"📁 Starting Foremost file carving: {input_file}")
        result = execute_command(command)
        result["output_directory"] = output_dir
        logger.info(f"📊 Foremost carving completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in foremost endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
