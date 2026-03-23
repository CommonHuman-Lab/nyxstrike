"""
Execute command with intelligent error handling and recovery API endpoint.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from server_core.error_handling import RecoveryAction
from server_core.recovery_executor import execute_command_with_recovery as _execute_command_with_recovery
from server_core.command_params import rebuild_command_with_params as _rebuild_command_with_params
from server_core.operation_types import determine_operation_type as _determine_operation_type
from server_core.command_executor import execute_command as _execute_command
from server_core.singletons import cache as _cache, error_handler, degradation_manager

logger = logging.getLogger(__name__)

api_error_handling_execute_with_recovery_bp = Blueprint(
    "api_error_handling_execute_with_recovery", __name__
)


def _run_execute_command(command: str, use_cache: bool = True, timeout: int = 300) -> Dict[str, Any]:
    return _execute_command(command, use_cache=use_cache, cache=_cache, timeout=timeout)


def execute_command_with_recovery(
    tool_name: str,
    command: str,
    parameters: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
    max_attempts: int = 3,
) -> Dict[str, Any]:
    return _execute_command_with_recovery(
        tool_name=tool_name,
        command=command,
        parameters=parameters,
        use_cache=use_cache,
        max_attempts=max_attempts,
        execute_command_fn=_run_execute_command,
        error_handler=error_handler,
        degradation_manager=degradation_manager,
        rebuild_command_with_params_fn=_rebuild_command_with_params,
        determine_operation_type_fn=_determine_operation_type,
        recovery_action_enum=RecoveryAction,
        logger=logger,
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
        max_attempts = data.get("max_attempts", 3)
        use_cache = data.get("use_cache", True)

        if not tool_name or not command:
            return jsonify({"error": "tool_name and command are required"}), 400

        result = execute_command_with_recovery(
            tool_name=tool_name,
            command=command,
            parameters=parameters,
            use_cache=use_cache,
            max_attempts=max_attempts,
        )

        return jsonify({
            "success": result.get("success", False),
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error executing command with recovery: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
