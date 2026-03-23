from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_smb_enum_rpcclient_bp = Blueprint("api_smb_enum_rpcclient", __name__)


@api_smb_enum_rpcclient_bp.route("/api/tools/rpcclient", methods=["POST"])
def rpcclient():
    """Execute rpcclient for RPC enumeration with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        username = params.get("username", "")
        password = params.get("password", "")
        domain = params.get("domain", "")
        commands = params.get("commands", "enumdomusers;enumdomgroups;querydominfo")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 rpcclient called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        # Build authentication string
        auth_string = ""
        if username and password:
            auth_string = f"-U {username}%{password}"
        elif username:
            auth_string = f"-U {username}"
        else:
            auth_string = "-U ''"  # Anonymous

        if domain:
            auth_string += f" -W {domain}"

        # Create command sequence
        command_sequence = commands.replace(";", "\n")

        command = f"echo -e '{command_sequence}' | rpcclient {auth_string} {target}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting rpcclient: {target}")
        result = execute_command(command)
        logger.info(f"📊 rpcclient completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in rpcclient endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
