from flask import Blueprint, request, jsonify
import os
from server_core.command_executor import execute_command
import logging

logger = logging.getLogger(__name__)

api_password_cracking_ophcrack_bp = Blueprint("api_password_cracking_ophcrack", __name__)

@api_password_cracking_ophcrack_bp.route("/api/tools/password-cracking/ophcrack", methods=["POST"])
def ophcrack_crack():
    """
    API endpoint to execute Ophcrack for Windows hash cracking.

    Parameters (JSON body):
      - hash_file (str): Path to the hash file (pwdump/session). Required.
      - tables_dir (str): Path to rainbow tables directory (optional).
      - tables (str): Table set string for -t (optional).
      - additional_args (str): Extra ophcrack CLI arguments (optional).

    Returns:
      - JSON result from Ophcrack execution, or error message with HTTP 400/500 status.
    """
    try:
        params = request.json
        hash_file = params.get("hash_file", "")
        tables_dir = params.get("tables_dir", "")
        tables = params.get("tables", "")
        additional_args = params.get("additional_args", "")

        if not hash_file:
            logger.warning("Ophcrack called without hash_file")
            return jsonify({"error": "hash_file is required"}), 400

        if not os.path.isfile(hash_file):
            return jsonify({"error": f"Hash file not found: {hash_file}"}), 404

        command = "ophcrack -g"

        if tables_dir:
            if not os.path.isdir(tables_dir):
                return jsonify({"error": f"tables_dir not found: {tables_dir}"}), 400
            command += f" -d {tables_dir}"

        if tables:
            command += f" -t {tables}"

        command += f" -f {hash_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"Starting Ophcrack: {command}")
        result = execute_command(command, tool="ophcrack")
        logger.info("Ophcrack completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing Ophcrack: {str(e)}")
        return jsonify({"error": str(e)}), 500
