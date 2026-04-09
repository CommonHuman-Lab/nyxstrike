# server_api/password_cracking/medusa.py

from flask import Blueprint, request, jsonify
from server_core.command_executor import execute_command
import logging

logger = logging.getLogger(__name__)

api_password_cracking_medusa_bp = Blueprint("api_password_cracking_medusa", __name__)

@api_password_cracking_medusa_bp.route("/api/tools/medusa", methods=["POST"])
def medusa_attack():
    """
    Execute Medusa for password brute forcing with enhanced logging.

    Endpoint: POST /api/tools/medusa

    Description:
        Runs the Medusa password brute force tool against a specified target and service/module.
        Supports single username/password or files for bulk testing. Additional Medusa CLI options
        can be passed via 'additional_args'.

    Parameters (JSON body):
        target (str): Target hostname or IP address (maps to -h)
        module (str): Medusa module/service to attack (maps to -M)
        username (str, optional): Single username to test (maps to -u)
        username_file (str, optional): File with usernames (maps to -U)
        password (str, optional): Single password to test (maps to -p)
        password_file (str, optional): File with passwords (maps to -P)
        additional_args (str, optional): Extra Medusa CLI flags

    Returns:
        JSON result from command execution, including success/error and output.

    Example:
        {
            "target": "192.168.1.10",
            "module": "ssh",
            "username": "admin",
            "password_file": "/path/to/passwords.txt",
            "additional_args": "-t 10 -s"
        }
    """
    try:
        params = request.json
        target = params.get("target", "")
        module = params.get("module", "")
        username = params.get("username", "")
        username_file = params.get("username_file", "")
        password = params.get("password", "")
        password_file = params.get("password_file", "")
        additional_args = params.get("additional_args", "")

        if not target or not module:
            logger.warning("🔑 Medusa called without target or module parameter")
            return jsonify({
                "error": "Target and module parameters are required"
            }), 400

        command = f"medusa -h {target} -M {module}"

        if username:
            command += f" -u {username}"
        elif username_file:
            command += f" -U {username_file}"

        if password:
            command += f" -p {password}"
        elif password_file:
            command += f" -P {password_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔑 Starting Medusa attack: {target}:{module}")
        result = execute_command(command, tool="medusa")
        logger.info(f"📊 Medusa attack completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in medusa endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
