from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_iac_scan_checkov_bp = Blueprint("api_iac_scan_checkov", __name__)


@api_iac_scan_checkov_bp.route("/api/tools/checkov", methods=["POST"])
def checkov():
    """Execute Checkov for infrastructure as code security scanning"""
    try:
        params = request.json
        directory = params.get("directory", ".")
        framework = params.get("framework", "")  # terraform, cloudformation, kubernetes, etc.
        check = params.get("check", "")
        skip_check = params.get("skip_check", "")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        command = f"checkov -d {directory}"

        if framework:
            command += f" --framework {framework}"

        if check:
            command += f" --check {check}"

        if skip_check:
            command += f" --skip-check {skip_check}"

        if output_format:
            command += f" --output {output_format}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Checkov IaC scan: {directory}")
        result = execute_command(command)
        logger.info("Checkov scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in checkov endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
