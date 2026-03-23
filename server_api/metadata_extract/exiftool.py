from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_metadata_extract_exiftool_bp = Blueprint("api_metadata_extract_exiftool", __name__)


@api_metadata_extract_exiftool_bp.route("/api/tools/exiftool", methods=["POST"])
def exiftool():
    """Execute ExifTool for metadata extraction with enhanced logging"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        output_format = params.get("output_format", "")  # json, xml, csv
        tags = params.get("tags", "")
        additional_args = params.get("additional_args", "")

        if not file_path:
            logger.warning("📷 ExifTool called without file_path parameter")
            return jsonify({
                "error": "File path parameter is required"
            }), 400

        command = f"exiftool"

        if output_format:
            command += f" -{output_format}"

        if tags:
            command += f" -{tags}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {file_path}"

        logger.info(f"📷 Starting ExifTool analysis: {file_path}")
        result = execute_command(command)
        logger.info(f"📊 ExifTool analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in exiftool endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
