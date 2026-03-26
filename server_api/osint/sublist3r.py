from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_osint_sublist3r_bp = Blueprint("api_osint_sublist3r", __name__)
@api_osint_sublist3r_bp.route("/api/tools/osint/sublist3r", methods=["POST"])
def sublist3r():
    """Execute Sublist3r for subdomain enumeration"""
    try:
        params = request.json
        domain = params.get("domain", "")
        threads = params.get("threads", 3)
        engine = params.get("engine", "")

        if not domain:
            logger.warning("🔍 Sublist3r called without domain")
            return jsonify({"error": "Domain parameter is required"}), 400

        command = f"sublist3r -d {domain} -t {threads}"
        if engine:
            command += f" -e {engine}"
        
        logger.info(f"🚀 Executing Sublist3r: {command}")
        result = execute_command(command)
        logger.info(f"✅ Sublist3r execution completed for {domain}")
        return jsonify({"success": True, "output": result})
    except Exception as e:
        logger.error(f"❌ Sublist3r execution failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500