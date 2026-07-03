from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_vuln_intel_vulnx_bp = Blueprint("api_vuln_intel_vulnx", __name__)

@api_vuln_intel_vulnx_bp.route("/api/vuln-intel/vulnx", methods=["POST"])
def vulnx():
    """CVE vulnerability intelligence and analysis using vulnx"""
    try:
        params = request.json or {}
        cve_id = params.get("cve_id", "")
        search = params.get("search", "")
        auth = params.get("auth_key", "")

        if not (cve_id or search):
            logger.warning("vulnx called without any parameters")
            return jsonify({
                "error": "At least one of cve_id or search must be provided"
            }), 400

        command = "vulnx"
        if cve_id:
            command += f" id {cve_id}"
        if search:
            command += f" search \"{search}\""
        if auth:
            command += f" auth --api-key \"{auth}\""
        logger.info(f"Starting vulnx analysis: cve_id={cve_id}, search={search}")

        result = execute_command(command, use_recovery=True)

        logger.info("vulnx analysis completed")
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in vulnx endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500