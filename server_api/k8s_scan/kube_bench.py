from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_k8s_scan_kube_bench_bp = Blueprint("api_k8s_scan_kube_bench", __name__)


@api_k8s_scan_kube_bench_bp.route("/api/tools/kube-bench", methods=["POST"])
def kube_bench():
    """Execute kube-bench for CIS Kubernetes benchmark checks"""
    try:
        params = request.json
        targets = params.get("targets", "")  # master, node, etcd, policies
        version = params.get("version", "")
        config_dir = params.get("config_dir", "")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        command = "kube-bench"

        if targets:
            command += f" --targets {targets}"

        if version:
            command += f" --version {version}"

        if config_dir:
            command += f" --config-dir {config_dir}"

        if output_format:
            command += f" --outputfile /tmp/kube-bench-results.{output_format} --json"

        if additional_args:
            command += f" {additional_args}"

        logger.info("Starting kube-bench CIS benchmark")
        result = execute_command(command)
        logger.info("kube-bench benchmark completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in kube-bench endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
