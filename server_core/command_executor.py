import os
import shlex
import psutil
from typing import Any, Dict, Optional
from server_core import config_core
from server_core.enhanced_command_executor import EnhancedCommandExecutor
from server_core.singletons import cache as _cache

# CPU threshold above which tool commands are niced down.
_CPU_NICE_THRESHOLD = config_core.get("CPU_NICE_THRESHOLD", 85)

COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # Default to 5 minutes if not set


def _normalize_timeout(raw_timeout: Any) -> Optional[int]:
  """Normalize timeout values where <=0 means no hard timeout."""
  if raw_timeout is None:
    return None
  try:
    parsed = int(raw_timeout)
  except (ValueError, TypeError):
    return None
  if parsed <= 0:
    return None
  return parsed


def _is_unlimited_timeout(raw_timeout: Any) -> bool:
  try:
    return int(raw_timeout) <= 0
  except (ValueError, TypeError):
    return False


def _detect_tool_key(command: str, explicit_tool: Optional[str]) -> str:
  if explicit_tool and isinstance(explicit_tool, str):
    return explicit_tool.strip().lower()
  if not isinstance(command, str) or not command.strip():
    return ""
  try:
    parts = shlex.split(command)
  except ValueError:
    parts = command.strip().split()
  if not parts:
    return ""
  return os.path.basename(parts[0]).strip().lower()


def _resolve_timeout(command: str, tool: Optional[str], requested_timeout: Optional[int]) -> Optional[int]:
  requested = _normalize_timeout(requested_timeout)
  if requested is not None or _is_unlimited_timeout(requested_timeout):
    return requested

  tool_key = _detect_tool_key(command, tool)
  overrides = config_core.get("TOOL_TIMEOUT_OVERRIDES", {})
  if isinstance(overrides, dict):
    candidates = [tool_key]
    if "-" in tool_key:
      candidates.append(tool_key.replace("-", "_"))
    if "_" in tool_key:
      candidates.append(tool_key.replace("_", "-"))
    for key in candidates:
      if key and key in overrides:
        return _normalize_timeout(overrides.get(key))

  return _normalize_timeout(config_core.get("COMMAND_TIMEOUT", COMMAND_TIMEOUT))

def execute_command(
  command: str,
  use_cache: bool = True,
  cache=None,
  timeout: Optional[int] = None,
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
      timeout:    Command execution timeout in seconds (<=0 means no hard timeout)
      tool:       Reserved — tool name (unused; recording is done in the after_request hook)
      endpoint:   Reserved — API endpoint (unused; recording is done in the after_request hook)
      params:     Reserved — request params (unused; recording is done in the after_request hook)

  Returns:
      A dictionary containing the stdout, stderr, return code, and metadata
  """
  active_cache = cache if cache is not None else (_cache if use_cache else None)

  # Cache key always uses the original command — before any runtime adjustments.
  if active_cache is not None:
    cached_result = active_cache.get(command, {})
    if cached_result:
      return cached_result

  effective_timeout = _resolve_timeout(command, tool, timeout)

  # Apply CPU niceness after the cache check so the cache key is unaffected.
  # interval=None is non-blocking — uses CPU% measured since the last psutil call.
  exec_command = command
  try:
    if psutil.cpu_percent(interval=None) > _CPU_NICE_THRESHOLD:
      if not exec_command.startswith("nice "):
        exec_command = f"nice -n 10 {exec_command}"
  except Exception:
    pass  # never let a psutil hiccup block a tool call

  _executor = EnhancedCommandExecutor(exec_command, timeout=effective_timeout)
  result = _executor.execute()

  if active_cache is not None and result.get("success", False):
    active_cache.set(command, {}, result)

  # Record into the performance dashboard (lazy — wakes EnhancedProcessManager)
  try:
    from server_core.singletons import enhanced_process_manager as _epm
    _epm.performance_dashboard.record_execution(exec_command, result)
  except Exception:
    pass  # dashboard recording must never break a tool call

  return result


def execute_command_with_recovery(
  command: str,
  use_cache: bool = True,
  cache=None,
  timeout: Optional[int] = None,
  tool: Optional[str] = None,
  endpoint: Optional[str] = None,
  params: Optional[Dict[str, Any]] = None,
  target: Optional[str] = None,
) -> Dict[str, Any]:
  """Like ``execute_command`` but applies automatic error recovery on failure.

  On a failed execution, consults the ``RecoveryExecutor`` singleton to retry,
  reduce scope, or switch to an alternative tool.  The returned dict always
  contains a ``recovery`` key with metadata about any recovery actions taken:

    {
      "stdout": "...",
      "stderr": "...",
      "success": true|false,
      ...
      "recovery": {
        "applied": true,
        "attempts": 1,
        "action": "retry_with_backoff",
        "error_type": "timeout",
        "alternative_tool": null,
        "succeeded": true
      }
    }

  Args:
      command:   The command to execute.
      target:    Optional target string forwarded to the error handler for context.
      (all other args are identical to ``execute_command``)
  """
  from server_core.singletons import recovery_executor as _recovery_executor

  ctx: Dict[str, Any] = {
    "tool": tool or _detect_tool_key(command, tool),
    "target": target or "",
    "parameters": params or {},
  }

  result = _recovery_executor.run(
    execute_fn=execute_command,
    command=command,
    context=ctx,
    use_cache=use_cache,
    cache=cache,
    timeout=timeout,
    tool=tool,
    endpoint=endpoint,
    params=params,
  )
  return result
