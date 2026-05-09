from flask import Blueprint, request, jsonify
import logging
import os
import tempfile
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
        hash_value = params.get("hash", "")
        hash_type = params.get("hash_type", "")
        attack_mode = params.get("attack_mode", "0")
        wordlist = params.get("wordlist", ROCKYOU_PATH)
        mask = params.get("mask", "")
        additional_args = params.get("additional_args", "")

        if not hash_file and not hash_value:
            logger.warning("Hashcat called without hash_file or hash parameter")
            return jsonify({
                "error": "Either hash_file or hash parameter is required"
            }), 400

        if not hash_type:
            logger.warning("Hashcat called without hash_type parameter")
            return jsonify({
                "error": "Hash type parameter is required"
            }), 400

        tmp_file = None
        try:
            # hash_file takes priority; fall back to writing inline hash to a temp file
            if hash_file:
                target = hash_file
            else:
                tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
                tmp.write(hash_value.strip() + "\n")
                tmp.close()
                tmp_file = tmp.name
                target = tmp_file
                logger.info("Wrote inline hash to temp file for hashcat")

            command = f"hashcat -m {hash_type} -a {attack_mode} {target}"

            if attack_mode == "0" and wordlist:
                command += f" {wordlist}"
            elif attack_mode == "3" and mask:
                command += f" {mask}"

            if additional_args:
                command += f" {additional_args}"

            logger.info(f"Starting Hashcat attack: mode {attack_mode}")
            result = execute_command(command, tool="hashcat")
            logger.info("Hashcat attack completed")
            return jsonify(result)
        finally:
            if tmp_file and os.path.exists(tmp_file):
                os.unlink(tmp_file)
    except Exception as e:
        logger.error(f"💥 Error in hashcat endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
