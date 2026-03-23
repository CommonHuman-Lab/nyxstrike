from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_smb_enum_enum4linux_ng_bp = Blueprint("api_smb_enum_enum4linux_ng", __name__)


@api_smb_enum_enum4linux_ng_bp.route("/api/tools/enum4linux-ng", methods=["POST"])
def enum4linux_ng():
    """Execute Enum4linux-ng for advanced SMB enumeration with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        username = params.get("username", "")
        password = params.get("password", "")
        domain = params.get("domain", "")
        shares = params.get("shares", True)
        users = params.get("users", True)
        groups = params.get("groups", True)
        policy = params.get("policy", True)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Enum4linux-ng called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"enum4linux-ng {target}"

        if username:
            command += f" -u {username}"

        if password:
            command += f" -p {password}"

        if domain:
            command += f" -d {domain}"

        # Add specific enumeration options
        enum_options = []
        if shares:
            enum_options.append("S")
        if users:
            enum_options.append("U")
        if groups:
            enum_options.append("G")
        if policy:
            enum_options.append("P")

        if enum_options:
            command += f" -A {','.join(enum_options)}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Enum4linux-ng: {target}")
        result = execute_command(command)
        logger.info(f"📊 Enum4linux-ng completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in enum4linux-ng endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
