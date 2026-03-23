from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_container_scan_docker_bench_bp = Blueprint("api_container_scan_docker_bench", __name__)


@api_container_scan_docker_bench_bp.route("/api/tools/docker-bench-security", methods=["POST"])
def docker_bench_security():
    """Execute Docker Bench for Security for Docker security assessment"""
    try:
        params = request.json
        checks = params.get("checks", "")
        exclude = params.get("exclude", "")
        output_file = params.get("output_file", "/tmp/docker-bench-results.json")
        additional_args = params.get("additional_args", "")

        command = "docker-bench-security"

        if checks:
            command += f" -c {checks}"

        if exclude:
            command += f" -e {exclude}"

        if output_file:
            command += f" -l {output_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info("Starting Docker Bench Security assessment")
        result = execute_command(command)
        result["output_file"] = output_file
        logger.info("Docker Bench Security completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in docker-bench-security endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
