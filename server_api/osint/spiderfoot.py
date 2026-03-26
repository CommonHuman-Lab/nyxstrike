from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_osint_spiderfoot_bp = Blueprint("api_osint_spiderfoot", __name__)

@api_osint_spiderfoot_bp.route("/api/tools/osint/spiderfoot", methods=["POST"])
def spiderfoot():
    """Execute SpiderFoot for OSINT automation"""
    try:
        params = request.json
        target = params.get("target", "")

        if not target:
            logger.warning("🔍 SpiderFoot called without target")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"spiderfoot -s {target}"
        logger.info(f"🚀 Executing SpiderFoot: {command}")
        result = execute_command(command)
        logger.info(f"✅ SpiderFoot execution completed for {target}")
        return jsonify({"success": True, "output": result})
    except Exception as e:
        logger.error(f"❌ SpiderFoot execution failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500