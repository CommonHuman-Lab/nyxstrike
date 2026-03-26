from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_scan_joomscan_bp = Blueprint("api_web_scan_joomscan", __name__)

@api_web_scan_joomscan_bp.route("/api/tools/web_recon/joomscan", methods=["POST"])
def joomscan():
    """Execute joomscan with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Joomscan called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"joomscan --url {url}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Joomscan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Joomscan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in joomscan endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500