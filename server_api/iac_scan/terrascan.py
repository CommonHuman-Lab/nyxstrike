from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_iac_scan_terrascan_bp = Blueprint("api_iac_scan_terrascan", __name__)


@api_iac_scan_terrascan_bp.route("/api/tools/terrascan", methods=["POST"])
def terrascan():
    """Execute Terrascan for infrastructure as code security scanning"""
    try:
        params = request.json
        scan_type = params.get("scan_type", "all")  # all, terraform, k8s, etc.
        iac_dir = params.get("iac_dir", ".")
        policy_type = params.get("policy_type", "")
        output_format = params.get("output_format", "json")
        severity = params.get("severity", "")
        additional_args = params.get("additional_args", "")

        command = f"terrascan scan -t {scan_type} -d {iac_dir}"

        if policy_type:
            command += f" -p {policy_type}"

        if output_format:
            command += f" -o {output_format}"

        if severity:
            command += f" --severity {severity}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Terrascan IaC scan: {iac_dir}")
        result = execute_command(command)
        logger.info("Terrascan scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in terrascan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
