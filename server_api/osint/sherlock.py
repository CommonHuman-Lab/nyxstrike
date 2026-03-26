from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_osint_sherlock_bp = Blueprint("api_osint_sherlock", __name__)

@api_osint_sherlock_bp.route("/api/tools/osint/sherlock", methods=["POST"])
def sherlock():
    """Execute Sherlock for username investigation across social networks"""
    try:
        params = request.json
        username = params.get("username", "")

        if not username:
            logger.warning("🔍 Sherlock called without username")
            return jsonify({"error": "Username is required"}), 400

        command = f"sherlock {username} --output sherlock_results/{username}.json --json"
        logger.info(f"🚀 Executing Sherlock: {command}")
        result = execute_command(command)
        logger.info(f"✅ Sherlock execution completed for {username}")
        return jsonify({"success": True, "output": result})
    except Exception as e:
        logger.error(f"❌ Sherlock execution failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500