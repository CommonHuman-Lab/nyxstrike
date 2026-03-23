from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_smb_enum_nbtscan_bp = Blueprint("api_smb_enum_nbtscan", __name__)


@api_smb_enum_nbtscan_bp.route("/api/tools/nbtscan", methods=["POST"])
def nbtscan():
    """Execute nbtscan for NetBIOS name scanning with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        verbose = params.get("verbose", False)
        timeout = params.get("timeout", 2)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 nbtscan called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"nbtscan -t {timeout}"

        if verbose:
            command += " -v"

        command += f" {target}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting nbtscan: {target}")
        result = execute_command(command)
        logger.info(f"📊 nbtscan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in nbtscan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
