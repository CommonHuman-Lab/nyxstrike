from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_scan_wpscan_bp = Blueprint("api_web_scan_wpscan", __name__)


@api_web_scan_wpscan_bp.route("/api/tools/wpscan", methods=["POST"])
def wpscan():
    """Execute wpscan with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 WPScan called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"wpscan --url {url}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting WPScan: {url}")
        result = execute_command(command)
        logger.info(f"📊 WPScan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in wpscan endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
