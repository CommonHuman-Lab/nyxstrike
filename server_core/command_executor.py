from typing import Any, Dict, Optional
from server_core import config_core
from server_core.enhanced_command_executor import EnhancedCommandExecutor
from server_core.singletons import cache as _cache

COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # Default to 5 minutes if not set

# Reuse a single executor instance rather than constructing one per call.
# EnhancedCommandExecutor stores per-execution state only in instance variables
# that are reset inside execute(), so sharing the instance across calls is safe.
_executor = EnhancedCommandExecutor("", timeout=COMMAND_TIMEOUT)

def execute_command(
  command: str,
  use_cache: bool = True,
  cache=None,
  timeout: int = COMMAND_TIMEOUT,
  tool: Optional[str] = None,
  endpoint: Optional[str] = None,
  params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """
  Execute a shell command with enhanced features.

  Args:
      command:    The command to execute
      use_cache:  Whether to use caching for this command
      cache:      Optional cache instance (falls back to the module-level singleton)
      timeout:    Command execution timeout in seconds
      tool:       Reserved — tool name (unused; recording is done in the after_request hook)
      endpoint:   Reserved — API endpoint (unused; recording is done in the after_request hook)
      params:     Reserved — request params (unused; recording is done in the after_request hook)

  Returns:
      A dictionary containing the stdout, stderr, return code, and metadata
  """
  active_cache = cache if cache is not None else (_cache if use_cache else None)

  if active_cache is not None:
    cached_result = active_cache.get(command, {})
    if cached_result:
      return cached_result

  _executor.command = command
  _executor.timeout = timeout
  result = _executor.execute()

  if active_cache is not None and result.get("success", False):
    active_cache.set(command, {}, result)

  return result