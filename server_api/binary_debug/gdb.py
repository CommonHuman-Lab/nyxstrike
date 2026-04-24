from flask import Blueprint, request, jsonify
import logging
import os

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_binary_debug_gdb_bp = Blueprint("api_binary_debug_gdb", __name__)


@api_binary_debug_gdb_bp.route("/api/tools/gdb", methods=["POST"])
def gdb():
    """Execute GDB for binary analysis and debugging with enhanced logging"""
    try:
        params = request.json
        binary = params.get("binary", "")
        commands = params.get("commands", "")
        script_file = params.get("script_file", "")
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 GDB called without binary parameter")
            return jsonify({
                "error": "Binary parameter is required"
            }), 400

        command = f"gdb {binary}"

        if script_file:
            command += f" -x {script_file}"

        if commands:
            temp_script = "/tmp/gdb_commands.txt"
            with open(temp_script, "w") as f:
                f.write(commands)
            command += f" -x {temp_script}"

        if additional_args:
            command += f" {additional_args}"

        command += " -batch"

        logger.info(f"🔧 Starting GDB analysis: {binary}")
        result = execute_command(command)

        if commands and os.path.exists("/tmp/gdb_commands.txt"):
            try:
                os.remove("/tmp/gdb_commands.txt")
            except OSError:
                pass

        logger.info(f"📊 GDB analysis completed for {binary}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in gdb endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
