from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_dns_enum_dnsenum_bp = Blueprint("api_dns_enum_dnsenum", __name__)


@api_dns_enum_dnsenum_bp.route("/api/tools/dnsenum", methods=["POST"])
def dnsenum():
    """Execute dnsenum for DNS enumeration with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        dns_server = params.get("dns_server", "")
        wordlist = params.get("wordlist", "")
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 DNSenum called without domain parameter")
            return jsonify({
                "error": "Domain parameter is required"
            }), 400

        command = f"dnsenum {domain}"

        if dns_server:
            command += f" --dnsserver {dns_server}"

        if wordlist:
            command += f" --file {wordlist}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting DNSenum: {domain}")
        result = execute_command(command)
        logger.info(f"📊 DNSenum completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in dnsenum endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
