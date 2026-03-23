from flask import Blueprint, request, jsonify
import logging
import os

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_binary_debug_gdb_peda_bp = Blueprint("api_binary_debug_gdb_peda", __name__)


@api_binary_debug_gdb_peda_bp.route("/api/tools/gdb-peda", methods=["POST"])
def gdb_peda():
    """Execute GDB with PEDA for enhanced debugging and exploitation"""
    try:
        params = request.json
        binary = params.get("binary", "")
        commands = params.get("commands", "")
        attach_pid = params.get("attach_pid", 0)
        core_file = params.get("core_file", "")
        additional_args = params.get("additional_args", "")

        if not binary and not attach_pid and not core_file:
            logger.warning("🔧 GDB-PEDA called without binary, PID, or core file")
            return jsonify({"error": "Binary, PID, or core file parameter is required"}), 400

        # Base GDB command with PEDA
        command = "gdb -q"

        if binary:
            command += f" {binary}"

        if core_file:
            command += f" {core_file}"

        if attach_pid:
            command += f" -p {attach_pid}"

        # Create command script
        if commands:
            temp_script = "/tmp/gdb_peda_commands.txt"
            peda_commands = f"""
source ~/peda/peda.py
{commands}
quit
"""
            with open(temp_script, "w") as f:
                f.write(peda_commands)
            command += f" -x {temp_script}"
        else:
            # Default PEDA initialization
            command += " -ex 'source ~/peda/peda.py' -ex 'quit'"

        if additional_args:
            command += f" {additional_args}"

        target_info = binary or f'PID {attach_pid}' or core_file
        logger.info(f"🔧 Starting GDB-PEDA analysis: {target_info}")
        result = execute_command(command)

        # Cleanup
        if commands and os.path.exists("/tmp/gdb_peda_commands.txt"):
            try:
                os.remove("/tmp/gdb_peda_commands.txt")
            except Exception:
                pass

        logger.info(f"📊 GDB-PEDA analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in gdb-peda endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
