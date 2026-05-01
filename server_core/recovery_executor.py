"""
server_core/recovery_executor.py

Thin re-export shim so that existing imports of
``execute_command_with_recovery`` from this module continue to work.

The canonical implementation now lives in ``command_executor.py`` and is
backed by the ``RecoveryExecutor`` class in ``error_handling.py``.
"""

from server_core.command_executor import execute_command_with_recovery  # noqa: F401

__all__ = ["execute_command_with_recovery"]
