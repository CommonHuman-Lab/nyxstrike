from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_recon_assetfinder_bp = Blueprint("api_recon_assetfinder", __name__)


@api_recon_assetfinder_bp.route("/api/tools/assetfinder", methods=["POST"])
def assetfinder():
    """Execute Assetfinder for passive subdomain enumeration."""
    try:
        params = request.json
        domain = params.get("domain", "")
        only_subdomains = params.get("only_subdomains", True)
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 Assetfinder called without domain parameter")
            return jsonify({"error": "Domain parameter is required"}), 400

        command = "assetfinder"
        if only_subdomains:
            command += " --subs-only"
        command += f" {domain}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Assetfinder: {domain}")
        result = execute_command(command)
        logger.info(f"📊 Assetfinder completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in assetfinder endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
