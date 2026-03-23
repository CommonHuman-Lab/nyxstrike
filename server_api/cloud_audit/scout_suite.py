from flask import Blueprint, request, jsonify
from pathlib import Path
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_cloud_audit_scout_suite_bp = Blueprint("api_cloud_audit_scout_suite", __name__)


@api_cloud_audit_scout_suite_bp.route("/api/tools/scout-suite", methods=["POST"])
def scout_suite():
    """Execute Scout Suite for multi-cloud security assessment"""
    try:
        params = request.json
        provider = params.get("provider", "aws")  # aws, azure, gcp, aliyun, oci
        profile = params.get("profile", "default")
        report_dir = params.get("report_dir", "/tmp/scout-suite")
        services = params.get("services", "")
        exceptions = params.get("exceptions", "")
        additional_args = params.get("additional_args", "")

        Path(report_dir).mkdir(parents=True, exist_ok=True)

        command = f"scout {provider}"

        if profile and provider == "aws":
            command += f" --profile {profile}"

        if services:
            command += f" --services {services}"

        if exceptions:
            command += f" --exceptions {exceptions}"

        command += f" --report-dir {report_dir}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Scout Suite {provider} assessment")
        result = execute_command(command)
        result["report_directory"] = report_dir
        logger.info("Scout Suite assessment completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in scout-suite endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
