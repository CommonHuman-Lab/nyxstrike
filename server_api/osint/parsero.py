from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_osint_parsero_bp = Blueprint("api_osint_parsero", __name__)

@api_osint_parsero_bp.route("/api/tools/osint/parsero", methods=["POST"])

def parsero():
    """Execute Parsero for OSINT parsing and extraction"""
    try:
        params = request.json
        target = params.get("target", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🔍 Parsero called without target")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"parsero -u {target} {additional_args}"
        logger.info(f"🚀 Executing Parsero: {command}")
        result = execute_command(command, use_recovery=True)
        logger.info(f"✅ Parsero execution completed for {target}")
        return jsonify({"success": True, "output": result})
    except Exception as e:
        logger.error(f"❌ Parsero execution failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500