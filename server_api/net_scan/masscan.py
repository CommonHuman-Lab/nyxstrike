from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_net_scan_masscan_bp = Blueprint("api_net_scan_masscan", __name__)


@api_net_scan_masscan_bp.route("/api/tools/masscan", methods=["POST"])
def masscan():
    """Execute Masscan for high-speed Internet-scale port scanning with intelligent rate limiting"""
    try:
        params = request.json
        target = params.get("target", "")
        ports = params.get("ports", "1-65535")
        rate = params.get("rate", 1000)
        interface = params.get("interface", "")
        router_mac = params.get("router_mac", "")
        source_ip = params.get("source_ip", "")
        banners = params.get("banners", False)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Masscan called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"masscan {target} -p{ports} --rate={rate}"

        if interface:
            command += f" -e {interface}"

        if router_mac:
            command += f" --router-mac {router_mac}"

        if source_ip:
            command += f" --source-ip {source_ip}"

        if banners:
            command += " --banners"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🚀 Starting Masscan: {target} at rate {rate}")
        result = execute_command(command)
        logger.info(f"📊 Masscan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in masscan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
