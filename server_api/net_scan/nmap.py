from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_net_scan_nmap_bp = Blueprint("api_net_scan_nmap", __name__)


@api_net_scan_nmap_bp.route("/api/tools/nmap", methods=["POST"])
def nmap():
    """Execute nmap scan with enhanced logging, caching, and intelligent error handling"""
    try:
        params = request.json
        target = params.get("target", "")
        scan_type = params.get("scan_type", "-sCV")
        ports = params.get("ports", "")
        additional_args = params.get("additional_args", "-T4 -Pn")

        if not target:
            logger.warning("Nmap called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"nmap {scan_type}"

        if ports:
            command += f" -p {ports}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {target}"

        logger.info(f"Starting Nmap scan: {target}")

        result = execute_command(command)

        logger.info(f"Nmap scan completed for {target}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in nmap endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
