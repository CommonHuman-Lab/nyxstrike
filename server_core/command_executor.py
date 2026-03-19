from typing import Dict, Any
from server_core import config_core
from server_core.enhanced_command_executor import EnhancedCommandExecutor
from server_core.cache import HexStrikeCache

COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # Default to 5 minutes if not set

# Module-level cache singleton — shared across all blueprint calls
_cache = HexStrikeCache()

def execute_command(command: str, use_cache: bool = True, cache=None, timeout: int = COMMAND_TIMEOUT) -> Dict[str, Any]:
    """
    Execute a shell command with enhanced features

    Args:
        command: The command to execute
        use_cache: Whether to use caching for this command
        cache: Optional cache instance (falls back to the module-level singleton)
        timeout: Command execution timeout in seconds

    Returns:
        A dictionary containing the stdout, stderr, return code, and metadata
    """
    active_cache = cache if cache is not None else (_cache if use_cache else None)

    if active_cache is not None:
        cached_result = active_cache.get(command, {})
        if cached_result:
            return cached_result

    executor = EnhancedCommandExecutor(command, timeout=timeout)
    result = executor.execute()

    if active_cache is not None and result.get("success", False):
        active_cache.set(command, {}, result)

    return result