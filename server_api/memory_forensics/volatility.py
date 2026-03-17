from flask import Blueprint, request, jsonify
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_memory_forensics_volatility_bp = Blueprint("api_memory_forensics_volatility", __name__)


@api_memory_forensics_volatility_bp.route("/api/tools/volatility", methods=["POST"])
def volatility():
    """Execute Volatility for memory forensics with enhanced logging"""
    try:
        params = request.json
        memory_file = params.get("memory_file", "")
        plugin = params.get("plugin", "")
        profile = params.get("profile", "")
        additional_args = params.get("additional_args", "")

        if not memory_file:
            logger.warning("🧠 Volatility called without memory_file parameter")
            return jsonify({
                "error": "Memory file parameter is required"
            }), 400

        if not plugin:
            logger.warning("🧠 Volatility called without plugin parameter")
            return jsonify({
                "error": "Plugin parameter is required"
            }), 400

        command = f"volatility -f {memory_file}"

        if profile:
            command += f" --profile={profile}"

        command += f" {plugin}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🧠 Starting Volatility analysis: {plugin}")
        result = execute_command(command)
        logger.info(f"📊 Volatility analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in volatility endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
