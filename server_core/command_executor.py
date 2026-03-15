from typing import Dict, Any
from server_core import config_core
from server_core.enhanced_command_executor import EnhancedCommandExecutor

COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # Default to 5 minutes if not set
# If you need cache, import it here or pass as argument
# from server_core.cache import HexStrikeCache

def execute_command(command: str, use_cache: bool = True, cache=None, timeout: int = COMMAND_TIMEOUT) -> Dict[str, Any]:
    """
    Execute a shell command with enhanced features

    Args:
        command: The command to execute
        use_cache: Whether to use caching for this command
        cache: Optional cache instance
        timeout: Command execution timeout in seconds

    Returns:
        A dictionary containing the stdout, stderr, return code, and metadata
    """
    if use_cache and cache is not None:
        cached_result = cache.get(command, {})
        if cached_result:
            return cached_result

    executor = EnhancedCommandExecutor(command, timeout=timeout)
    result = executor.execute()

    if use_cache and cache is not None and result.get("success", False):
        cache.set(command, {}, result)

    return result