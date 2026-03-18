from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_url_recon_waybackurls_bp = Blueprint("api_url_recon_waybackurls", __name__)


@api_url_recon_waybackurls_bp.route("/api/tools/waybackurls", methods=["POST"])
def waybackurls():
    """Execute Waybackurls for historical URL discovery with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        get_versions = params.get("get_versions", False)
        no_subs = params.get("no_subs", False)
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 Waybackurls called without domain parameter")
            return jsonify({"error": "Domain parameter is required"}), 400

        command = f"waybackurls {domain}"

        if get_versions:
            command += " --get-versions"

        if no_subs:
            command += " --no-subs"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🕰️  Starting Waybackurls discovery: {domain}")
        result = execute_command(command)
        logger.info(f"📊 Waybackurls discovery completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in waybackurls endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
