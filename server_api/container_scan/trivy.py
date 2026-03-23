from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_container_scan_trivy_bp = Blueprint("api_container_scan_trivy", __name__)


@api_container_scan_trivy_bp.route("/api/tools/trivy", methods=["POST"])
def trivy():
    """Execute Trivy for container/filesystem vulnerability scanning"""
    try:
        params = request.json
        scan_type = params.get("scan_type", "image")  # image, fs, repo
        target = params.get("target", "")
        output_format = params.get("output_format", "json")
        severity = params.get("severity", "")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("Trivy called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"trivy {scan_type} {target}"

        if output_format:
            command += f" --format {output_format}"

        if severity:
            command += f" --severity {severity}"

        if output_file:
            command += f" --output {output_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Trivy {scan_type} scan: {target}")
        result = execute_command(command)
        if output_file:
            result["output_file"] = output_file
        logger.info(f"Trivy scan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in trivy endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
