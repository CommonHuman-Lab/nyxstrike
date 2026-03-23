from flask import Blueprint, request, jsonify
from pathlib import Path
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_cloud_audit_prowler_bp = Blueprint("api_cloud_audit_prowler", __name__)


@api_cloud_audit_prowler_bp.route("/api/tools/prowler", methods=["POST"])
def prowler():
    """Execute Prowler for AWS security assessment"""
    try:
        params = request.json
        provider = params.get("provider", "aws")
        profile = params.get("profile", "default")
        region = params.get("region", "")
        checks = params.get("checks", "")
        output_dir = params.get("output_dir", "/tmp/prowler_output")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        command = f"prowler {provider}"

        if profile:
            command += f" --profile {profile}"

        if region:
            command += f" --region {region}"

        if checks:
            command += f" --checks {checks}"

        command += f" --output-directory {output_dir}"
        command += f" --output-format {output_format}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Prowler {provider} security assessment")
        result = execute_command(command)
        result["output_directory"] = output_dir
        logger.info("Prowler assessment completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in prowler endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
