from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_runtime_monitor_falco_bp = Blueprint("api_runtime_monitor_falco", __name__)


@api_runtime_monitor_falco_bp.route("/api/tools/falco", methods=["POST"])
def falco():
    """Execute Falco for runtime security monitoring"""
    try:
        params = request.json
        config_file = params.get("config_file", "/etc/falco/falco.yaml")
        rules_file = params.get("rules_file", "")
        output_format = params.get("output_format", "json")
        duration = params.get("duration", 60)  # seconds
        additional_args = params.get("additional_args", "")

        command = f"timeout {duration} falco"

        if config_file:
            command += f" --config {config_file}"

        if rules_file:
            command += f" --rules {rules_file}"

        if output_format == "json":
            command += " --json"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Falco runtime monitoring for {duration}s")
        result = execute_command(command)
        logger.info("Falco monitoring completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in falco endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
