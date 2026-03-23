from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_binary_analysis_libc_database_bp = Blueprint("api_binary_analysis_libc_database", __name__)


@api_binary_analysis_libc_database_bp.route("/api/tools/libc-database", methods=["POST"])
def libc_database():
    """Execute libc-database for libc identification and offset lookup"""
    try:
        params = request.json
        action = params.get("action", "find")  # find, dump, download
        symbols = params.get("symbols", "")  # format: "symbol1:offset1 symbol2:offset2"
        libc_id = params.get("libc_id", "")
        additional_args = params.get("additional_args", "")

        if action == "find" and not symbols:
            logger.warning("🔧 libc-database find called without symbols")
            return jsonify({"error": "Symbols parameter is required for find action"}), 400

        if action in ["dump", "download"] and not libc_id:
            logger.warning("🔧 libc-database called without libc_id for dump/download")
            return jsonify({"error": "libc_id parameter is required for dump/download actions"}), 400

        # Navigate to libc-database directory (assuming it's installed)
        base_command = "cd /opt/libc-database 2>/dev/null || cd ~/libc-database 2>/dev/null || echo 'libc-database not found'"

        if action == "find":
            command = f"{base_command} && ./find {symbols}"
        elif action == "dump":
            command = f"{base_command} && ./dump {libc_id}"
        elif action == "download":
            command = f"{base_command} && ./download {libc_id}"
        else:
            return jsonify({"error": f"Invalid action: {action}"}), 400

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting libc-database {action}: {symbols or libc_id}")
        result = execute_command(command)
        logger.info(f"📊 libc-database {action} completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in libc-database endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
