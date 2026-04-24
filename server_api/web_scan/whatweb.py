from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_web_scan_whatweb_bp = Blueprint("api_web_scan_whatweb", __name__)

@api_web_scan_whatweb_bp.route("/api/tools/web_recon/whatweb", methods=["POST"])
def whatweb():
    """Execute whatweb with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")

        if not url:
            logger.warning("🌐 WhatWeb called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"whatweb -v -a 3 {url}"

        logger.info(f"🔍 Starting WhatWeb: {url}")
        result = execute_command(command)
        logger.info(f"📊 WhatWeb completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in whatweb endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500