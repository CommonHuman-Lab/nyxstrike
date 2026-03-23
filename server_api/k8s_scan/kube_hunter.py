from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_k8s_scan_kube_hunter_bp = Blueprint("api_k8s_scan_kube_hunter", __name__)


@api_k8s_scan_kube_hunter_bp.route("/api/tools/kube-hunter", methods=["POST"])
def kube_hunter():
    """Execute kube-hunter for Kubernetes penetration testing"""
    try:
        params = request.json
        target = params.get("target", "")
        remote = params.get("remote", "")
        cidr = params.get("cidr", "")
        interface = params.get("interface", "")
        active = params.get("active", False)
        report = params.get("report", "json")
        additional_args = params.get("additional_args", "")

        command = "kube-hunter"

        if target:
            command += f" --remote {target}"
        elif remote:
            command += f" --remote {remote}"
        elif cidr:
            command += f" --cidr {cidr}"
        elif interface:
            command += f" --interface {interface}"
        else:
            command += " --pod"

        if active:
            command += " --active"

        if report:
            command += f" --report {report}"

        if additional_args:
            command += f" {additional_args}"

        logger.info("Starting kube-hunter Kubernetes scan")
        result = execute_command(command)
        logger.info("kube-hunter scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in kube-hunter endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
