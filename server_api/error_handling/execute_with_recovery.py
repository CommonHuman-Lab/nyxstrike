"""
Execute command with intelligent error handling and recovery API endpoint.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from server_core.recovery_executor import execute_command_with_recovery as _execute_command_with_recovery
from server_core.command_params import rebuild_command_with_params as _rebuild_command_with_params
from server_core.operation_types import determine_operation_type as _determine_operation_type

logger = logging.getLogger(__name__)

api_error_handling_execute_with_recovery_bp = Blueprint(
    "api_error_handling_execute_with_recovery", __name__
)


def execute_command_with_recovery(
    tool_name: str,
    command: str,
    parameters: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
) -> Dict[str, Any]:
    parameters = parameters or {}
    full_command = _rebuild_command_with_params(tool_name, command, parameters)
    return _execute_command_with_recovery(
        full_command,
        use_cache=use_cache,
        tool=tool_name,
        params=parameters,
        target=parameters.get("target", ""),
    )


@api_error_handling_execute_with_recovery_bp.route(
    "/api/error-handling/execute-with-recovery", methods=["POST"]
)
def execute_with_recovery_endpoint():
    """Execute a command with intelligent error handling and recovery"""
    try:
        data = request.get_json()
        tool_name = data.get("tool_name", "")
        command = data.get("command", "")
        parameters = data.get("parameters", {})
        use_cache = data.get("use_cache", True)

        if not tool_name or not command:
            return jsonify({"error": "tool_name and command are required"}), 400

        result = execute_command_with_recovery(
            tool_name=tool_name,
            command=command,
            parameters=parameters,
            use_cache=use_cache,
        )

        return jsonify({
            "success": result.get("success", False),
            "result": result,
            "operation_type": _determine_operation_type(tool_name),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error executing command with recovery: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
