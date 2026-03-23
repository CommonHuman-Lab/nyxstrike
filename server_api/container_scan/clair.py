from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_container_scan_clair_bp = Blueprint("api_container_scan_clair", __name__)


@api_container_scan_clair_bp.route("/api/tools/clair", methods=["POST"])
def clair():
    """Execute Clair for container vulnerability analysis"""
    try:
        params = request.json
        image = params.get("image", "")
        config = params.get("config", "/etc/clair/config.yaml")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        if not image:
            logger.warning("Clair called without image parameter")
            return jsonify({"error": "Image parameter is required"}), 400

        command = f"clairctl analyze {image}"

        if config:
            command += f" --config {config}"

        if output_format:
            command += f" --format {output_format}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Clair vulnerability scan: {image}")
        result = execute_command(command)
        logger.info(f"Clair scan completed for {image}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in clair endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
