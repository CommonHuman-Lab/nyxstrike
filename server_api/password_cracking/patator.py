from flask import Blueprint, request, jsonify
import os
from server_core.command_executor import execute_command
import logging

logger = logging.getLogger(__name__)

api_password_cracking_patator_bp = Blueprint("api_password_cracking_patator", __name__)

@api_password_cracking_patator_bp.route("/api/tools/patator", methods=["POST"])
def patator_attack():
    """
    API endpoint to execute Patator for password brute forcing.

    This endpoint allows clients to initiate a password brute force attack using the Patator tool.
    It supports multiple modules (e.g., ssh, ftp, http) and flexible input for usernames and passwords,
    including single values or files containing lists. Enhanced logging is provided for audit and debugging.

    Parameters (JSON body):
      - module (str): Patator module to use (e.g., 'ssh_login', 'ftp_login'). Required.
      - target (str): Target host or address for the attack. Required.
      - username (str): Single username to test (optional).
      - username_file (str): Path to file containing usernames (optional, mutually exclusive with 'username').
      - password (str): Single password to test (optional).
      - password_file (str): Path to file containing passwords (optional, mutually exclusive with 'password').
      - additional_args (str): Extra Patator command-line arguments (optional).

    Returns:
      - JSON result from Patator execution, or error message with HTTP 400/500 status.
    """
    try:
        params = request.json
        module = params.get("module", "")
        target = params.get("target", "")
        username = params.get("username", "")
        username_file = params.get("username_file", "")
        password = params.get("password", "")
        password_file = params.get("password_file", "")
        additional_args = params.get("additional_args", "")

        if not module or not target:
            logger.warning("Patator called without module or target")
            return jsonify({"error": "module and target are required"}), 400

        # Enforce mutual exclusivity for username/username_file and password/password_file
        if username and username_file:
            return jsonify({"error": "Specify only one of username or username_file"}), 400
        if password and password_file:
            return jsonify({"error": "Specify only one of password or password_file"}), 400

        # Build Patator command based on module syntax
        command = f"patator {module} host={target}"

        if username:
            command += f" user={username}"
        elif username_file:
            if not os.path.isfile(username_file):
                return jsonify({"error": f"username_file not found: {username_file}"}), 400
            command += f" user=FILE:{username_file}"

        if password:
            command += f" password={password}"
        elif password_file:
            if not os.path.isfile(password_file):
                return jsonify({"error": f"password_file not found: {password_file}"}), 400
            command += f" password=FILE:{password_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Patator attack: {command}")
        result = execute_command(command, tool="patator")
        logger.info("Patator attack completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing Patator attack: {str(e)}")
        return jsonify({"error": str(e)}), 500
