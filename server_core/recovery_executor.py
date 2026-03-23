from datetime import datetime
from typing import Any, Callable, Dict, Optional
import time

def execute_command_with_recovery(
  tool_name: str,
  command: str,
  parameters: Optional[Dict[str, Any]] = None,
  use_cache: bool = True,
  max_attempts: int = 3,
  *,
  execute_command_fn: Callable[[str, bool], Dict[str, Any]],
  error_handler: Any,
  degradation_manager: Any,
  rebuild_command_with_params_fn: Callable[[str, str, Dict[str, Any]], str],
  determine_operation_type_fn: Callable[[str], str],
  recovery_action_enum: Any,
  logger: Any,
) -> Dict[str, Any]:
  if parameters is None:
    parameters = {}

  attempt_count = 0
  last_error = None
  recovery_history = []

  while attempt_count < max_attempts:
    attempt_count += 1

    try:
      result = execute_command_fn(command, use_cache)

      if result.get("success", False):
        return {
          "success": True,
          "tool_name": tool_name,
          "command": command,
          "result": result,
          "recovery_info": {
            "attempts_made": attempt_count,
            "recovery_applied": attempt_count > 1,
            "recovery_history": recovery_history,
          },
        }

      error_message = result.get("stderr", "Unknown error")
      exception = Exception(error_message)

      context = {
        "target": parameters.get("target", "unknown"),
        "parameters": parameters,
        "attempt_count": attempt_count,
        "command": command,
      }

      recovery_strategy = error_handler.handle_tool_failure(tool_name, exception, context)
      recovery_history.append({
        "attempt": attempt_count,
        "error": error_message,
        "recovery_action": recovery_strategy.action.value,
        "timestamp": datetime.now().isoformat(),
      })

      if recovery_strategy.action == recovery_action_enum.RETRY_WITH_BACKOFF:
        delay = getattr(recovery_strategy, "backoff_multiplier", 2)
        logger.warning(f"⏳ Retrying {tool_name} after {delay}s backoff")
        time.sleep(delay)
        continue

      elif recovery_strategy.action == recovery_action_enum.RETRY_WITH_REDUCED_SCOPE:
        reduced_params = getattr(recovery_strategy, "adjusted_parameters", {}) or {}
        command = rebuild_command_with_params_fn(tool_name, command, reduced_params)
        logger.warning(f"🔧 Retrying {tool_name} with reduced scope")
        continue

      elif recovery_strategy.action == recovery_action_enum.SWITCH_TO_ALTERNATIVE_TOOL:
        alt_tool = getattr(recovery_strategy, "alternative_tool", None)
        if alt_tool:
          op_type = determine_operation_type_fn(tool_name)
          fallback_chain = degradation_manager.create_fallback_chain(op_type, tool_name)
          fallback = fallback_chain[0] if fallback_chain else None
          if fallback:
            tool_name = fallback
            logger.warning(f"🔄 Switching from {tool_name} to fallback tool {fallback}")
            continue

      elif recovery_strategy.action == recovery_action_enum.ADJUST_PARAMETERS:
        adjusted = getattr(recovery_strategy, "adjusted_parameters", {}) or {}
        command = rebuild_command_with_params_fn(tool_name, command, adjusted)
        logger.warning(f"⚙️ Retrying {tool_name} with adjusted parameters")
        continue

      elif recovery_strategy.action == recovery_action_enum.ESCALATE_TO_HUMAN:
        return {
          "success": False,
          "error": f"Escalated to human: {error_message}",
          "recovery_info": {
            "attempts_made": attempt_count,
            "recovery_applied": True,
            "recovery_history": recovery_history,
            "final_action": "escalate_to_human",
          },
        }

      elif recovery_strategy.action == recovery_action_enum.GRACEFUL_DEGRADATION:
        return {
          "success": False,
          "error": f"Graceful degradation applied: {error_message}",
          "recovery_info": {
            "attempts_made": attempt_count,
            "recovery_applied": True,
            "recovery_history": recovery_history,
            "final_action": "graceful_degradation",
          },
        }

      elif recovery_strategy.action == recovery_action_enum.ABORT_OPERATION:
        return {
          "success": False,
          "error": f"Operation aborted: {error_message}",
          "recovery_info": {
            "attempts_made": attempt_count,
            "recovery_applied": True,
            "recovery_history": recovery_history,
            "final_action": "abort_operation",
          },
        }

      last_error = exception

    except Exception as e:
      last_error = e
      logger.error(f"💥 Unexpected error in recovery attempt {attempt_count}: {str(e)}")

  logger.error(f"🚫 All recovery attempts exhausted for {tool_name}")
  return {
    "success": False,
    "error": f"All recovery attempts exhausted: {str(last_error)}",
    "recovery_info": {
      "attempts_made": attempt_count,
      "recovery_applied": True,
      "recovery_history": recovery_history,
      "final_action": "all_attempts_exhausted",
    },
  }