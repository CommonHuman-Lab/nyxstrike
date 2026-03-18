from flask import Blueprint, request, jsonify
import logging
from pathlib import Path

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_memory_forensics_volatility3_bp = Blueprint("api_memory_forensics_volatility3", __name__)


@api_memory_forensics_volatility3_bp.route("/api/tools/volatility3", methods=["POST"])
def volatility3():
    """Execute Volatility3 for advanced memory forensics with enhanced logging"""
    try:
        params = request.json
        memory_file = params.get("memory_file", "")
        plugin = params.get("plugin", "")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not memory_file:
            logger.warning("🧠 Volatility3 called without memory_file parameter")
            return jsonify({
                "error": "Memory file parameter is required"
            }), 400

        if not plugin:
            logger.warning("🧠 Volatility3 called without plugin parameter")
            return jsonify({
                "error": "Plugin parameter is required"
            }), 400

        command = f"vol -f {memory_file} {plugin}"

        if output_file:
            command += f" -o {output_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🧠 Starting Volatility3 analysis: {plugin}")
        result = execute_command(command)
        logger.info(f"📊 Volatility3 analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in volatility3 endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
