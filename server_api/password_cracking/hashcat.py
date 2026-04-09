from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command
from server_core.singletons import ROCKYOU_PATH

logger = logging.getLogger(__name__)

api_password_cracking_hashcat_bp = Blueprint("api_password_cracking_hashcat", __name__)


@api_password_cracking_hashcat_bp.route("/api/tools/hashcat", methods=["POST"])
def hashcat():
    """Execute Hashcat for password cracking with enhanced logging"""
    try:
        params = request.json
        hash_file = params.get("hash_file", "")
        hash_type = params.get("hash_type", "")
        attack_mode = params.get("attack_mode", "0")
        wordlist = params.get("wordlist", ROCKYOU_PATH)
        mask = params.get("mask", "")
        additional_args = params.get("additional_args", "")

        if not hash_file:
            logger.warning("🔐 Hashcat called without hash_file parameter")
            return jsonify({
                "error": "Hash file parameter is required"
            }), 400

        if not hash_type:
            logger.warning("🔐 Hashcat called without hash_type parameter")
            return jsonify({
                "error": "Hash type parameter is required"
            }), 400

        command = f"hashcat -m {hash_type} -a {attack_mode} {hash_file}"

        if attack_mode == "0" and wordlist:
            command += f" {wordlist}"
        elif attack_mode == "3" and mask:
            command += f" {mask}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔐 Starting Hashcat attack: mode {attack_mode}")
        result = execute_command(command, tool="hashcat")
        logger.info(f"📊 Hashcat attack completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in hashcat endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
