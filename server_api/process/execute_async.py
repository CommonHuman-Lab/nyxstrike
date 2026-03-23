from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from server_core.singletons import enhanced_process_manager

logger = logging.getLogger(__name__)

api_process_execute_async_bp = Blueprint("api_process_execute_async", __name__)


@api_process_execute_async_bp.route("/api/process/execute-async", methods=["POST"])
def execute_command_async():
    """Execute command asynchronously using enhanced process management"""
    try:
        params = request.json
        command = params.get("command", "")
        context = params.get("context", {})

        if not command:
            return jsonify({"error": "Command parameter is required"}), 400

        task_id = enhanced_process_manager.execute_command_async(command, context)

        logger.info(f"🚀 Async command execution started | Task ID: {task_id}")
        return jsonify({
            "success": True,
            "task_id": task_id,
            "command": command,
            "status": "submitted",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in async command execution: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
