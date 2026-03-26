from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_tool_active_directory_ldapdomaindump_bp = Blueprint("api_tool_active_directory_ldapdomaindump", __name__)

@api_tool_active_directory_ldapdomaindump_bp.route("/api/tools/active_directory/ldapdomaindump", methods=["POST"])
def run_ldapdomaindump():
    data = request.json
    hostname = data.get("hostname")
    username = data.get("username", "")
    password = data.get("password", "")
    authtype = data.get("authtype", "NTLM")

    if not hostname:
        return jsonify({"error": "Hostname is required"}), 400

    # Build the command
    cmd = ["ldapdomaindump", hostname, "--authtype", authtype]
    if username and password:
        cmd.extend(["--user", username, "--password", password])

    try:
        command_str = " ".join(cmd)
        output = execute_command(command_str)
        return jsonify({"output": output})
    except Exception as e:
        logger.error(f"Error running ldapdomaindump: {e}")
        return jsonify({"error": str(e)}), 500  
    
