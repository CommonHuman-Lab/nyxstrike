"""
tests/test_recovery_executor.py

Unit tests for server_core/error_handling.RecoveryExecutor.

Safety guarantee
────────────────
execute_fn is always a plain Python MagicMock — no real subprocess is ever called.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from server_core.error_handling import (
    RecoveryExecutor,
    IntelligentErrorHandler,
    RecoveryAction,
    RecoveryStrategy,
    ErrorType,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_strategy(action: RecoveryAction, **kwargs) -> RecoveryStrategy:
    return RecoveryStrategy(
        action=action,
        parameters=kwargs.get("parameters", {}),
        max_attempts=kwargs.get("max_attempts", 3),
        backoff_multiplier=kwargs.get("backoff_multiplier", 1.0),
        success_probability=kwargs.get("success_probability", 0.5),
        estimated_time=kwargs.get("estimated_time", 10),
    )


def _success_result(**extra):
    return {"success": True, "stdout": "ok", "stderr": "", **extra}


def _failure_result(**extra):
    return {"success": False, "stdout": "", "stderr": "error", **extra}


def _make_executor(strategy: RecoveryStrategy = None):
    """Build a RecoveryExecutor whose IntelligentErrorHandler always returns ``strategy``."""
    handler = MagicMock(spec=IntelligentErrorHandler)
    if strategy is not None:
        handler.handle_tool_failure.return_value = strategy
        handler.classify_error.return_value = ErrorType.UNKNOWN
    else:
        # Default: abort immediately so tests don't loop
        handler.handle_tool_failure.return_value = _make_strategy(RecoveryAction.ABORT_OPERATION)
        handler.classify_error.return_value = ErrorType.UNKNOWN
    return RecoveryExecutor(error_handler=handler)


# ---------------------------------------------------------------------------
# Happy path — first attempt succeeds
# ---------------------------------------------------------------------------

class TestNoRecoveryNeeded:
    def test_returns_result_on_first_success(self):
        executor = _make_executor()
        execute_fn = MagicMock(return_value=_success_result())
        result = executor.run(execute_fn, "nmap -sCV 10.0.0.1")
        assert result["success"] is True

    def test_recovery_meta_not_applied_on_success(self):
        executor = _make_executor()
        execute_fn = MagicMock(return_value=_success_result())
        result = executor.run(execute_fn, "nmap -sCV 10.0.0.1")
        assert result["recovery"]["applied"] is False
        assert result["recovery"]["attempts"] == 0

    def test_execute_fn_called_exactly_once_on_success(self):
        executor = _make_executor()
        execute_fn = MagicMock(return_value=_success_result())
        executor.run(execute_fn, "cmd")
        execute_fn.assert_called_once()

    def test_recovery_key_always_present(self):
        executor = _make_executor()
        execute_fn = MagicMock(return_value=_success_result())
        result = executor.run(execute_fn, "cmd")
        assert "recovery" in result


# ---------------------------------------------------------------------------
# Retry with backoff
# ---------------------------------------------------------------------------

class TestRetryWithBackoff:
    def test_retries_and_succeeds(self):
        strategy = _make_strategy(
            RecoveryAction.RETRY_WITH_BACKOFF,
            parameters={"initial_delay": 0, "max_delay": 0},
            backoff_multiplier=1.0,
        )
        executor = _make_executor(strategy)

        # Fail on first call, succeed on second
        execute_fn = MagicMock(side_effect=[_failure_result(), _success_result()])
        with patch("time.sleep"):  # don't actually sleep
            result = executor.run(execute_fn, "nmap 10.0.0.1", context={"tool": "nmap"})

        assert result["success"] is True
        assert result["recovery"]["applied"] is True
        assert result["recovery"]["succeeded"] is True

    def test_recovery_action_recorded(self):
        strategy = _make_strategy(
            RecoveryAction.RETRY_WITH_BACKOFF,
            parameters={"initial_delay": 0, "max_delay": 0},
        )
        executor = _make_executor(strategy)
        execute_fn = MagicMock(side_effect=[_failure_result(), _success_result()])
        with patch("time.sleep"):
            result = executor.run(execute_fn, "cmd", context={"tool": "nmap"})
        assert result["recovery"]["action"] == RecoveryAction.RETRY_WITH_BACKOFF.value

    def test_max_attempts_not_exceeded(self):
        strategy = _make_strategy(
            RecoveryAction.RETRY_WITH_BACKOFF,
            parameters={"initial_delay": 0, "max_delay": 0},
        )
        executor = _make_executor(strategy)
        # Always fail
        execute_fn = MagicMock(return_value=_failure_result())
        with patch("time.sleep"):
            result = executor.run(execute_fn, "cmd", context={"tool": "nmap"})

        # Initial call + at most MAX_RECOVERY_ATTEMPTS retries
        assert execute_fn.call_count <= RecoveryExecutor.MAX_RECOVERY_ATTEMPTS + 1
        assert result["recovery"]["succeeded"] is False


# ---------------------------------------------------------------------------
# Retry with reduced scope
# ---------------------------------------------------------------------------

class TestRetryWithReducedScope:
    def test_reduces_thread_count_in_command(self):
        strategy = _make_strategy(
            RecoveryAction.RETRY_WITH_REDUCED_SCOPE,
            parameters={"reduce_threads": True},
        )
        executor = _make_executor(strategy)
        execute_fn = MagicMock(side_effect=[_failure_result(), _success_result()])
        result = executor.run(execute_fn, "nmap -T4 10.0.0.1", context={"tool": "nmap"})

        # The second call should have a modified command (e.g. -T2)
        second_call_cmd = execute_fn.call_args_list[1][0][0]
        assert "-T4" not in second_call_cmd or "-T2" in second_call_cmd

    def test_reduces_scope_static_helper(self):
        reduced = RecoveryExecutor._reduce_scope(
            "nmap -T4 --threads 20 10.0.0.1",
            {"reduce_threads": True}
        )
        assert "-T4" not in reduced
        assert "-T2" in reduced
        assert "--threads 5" in reduced


# ---------------------------------------------------------------------------
# Switch to alternative tool
# ---------------------------------------------------------------------------

class TestSwitchToAlternativeTool:
    def test_alternative_tool_used(self):
        strategy = _make_strategy(RecoveryAction.SWITCH_TO_ALTERNATIVE_TOOL)
        handler = MagicMock(spec=IntelligentErrorHandler)
        handler.handle_tool_failure.return_value = strategy
        handler.classify_error.return_value = ErrorType.TOOL_NOT_FOUND
        handler.get_alternative_tool.return_value = "rustscan"

        executor = RecoveryExecutor(error_handler=handler)
        execute_fn = MagicMock(side_effect=[_failure_result(), _success_result()])
        result = executor.run(execute_fn, "nmap 10.0.0.1", context={"tool": "nmap"})

        second_cmd = execute_fn.call_args_list[1][0][0]
        assert "rustscan" in second_cmd
        assert result["recovery"]["alternative_tool"] == "rustscan"

    def test_no_alternative_stops_recovery(self):
        strategy = _make_strategy(RecoveryAction.SWITCH_TO_ALTERNATIVE_TOOL)
        handler = MagicMock(spec=IntelligentErrorHandler)
        handler.handle_tool_failure.return_value = strategy
        handler.classify_error.return_value = ErrorType.TOOL_NOT_FOUND
        handler.get_alternative_tool.return_value = None  # no alternative

        executor = RecoveryExecutor(error_handler=handler)
        execute_fn = MagicMock(return_value=_failure_result())
        result = executor.run(execute_fn, "nmap 10.0.0.1", context={"tool": "nmap"})

        # Should stop after first failure — no extra calls
        assert execute_fn.call_count == 1
        assert result["recovery"]["alternative_tool"] is None


# ---------------------------------------------------------------------------
# Abort / escalate actions
# ---------------------------------------------------------------------------

class TestAbortAndEscalate:
    @pytest.mark.parametrize("action", [
        RecoveryAction.ABORT_OPERATION,
        RecoveryAction.ESCALATE_TO_HUMAN,
    ])
    def test_stops_immediately(self, action):
        strategy = _make_strategy(action)
        executor = _make_executor(strategy)
        execute_fn = MagicMock(return_value=_failure_result())
        result = executor.run(execute_fn, "cmd", context={"tool": "tool"})

        # Only the initial call, no retries
        assert execute_fn.call_count == 1
        assert result["recovery"]["succeeded"] is False


# ---------------------------------------------------------------------------
# _substitute_tool helper
# ---------------------------------------------------------------------------

class TestSubstituteTool:
    def test_replaces_binary(self):
        result = RecoveryExecutor._substitute_tool("nmap -sCV 10.0.0.1", "rustscan")
        assert result.startswith("rustscan")
        assert "10.0.0.1" in result

    def test_handles_empty_command(self):
        result = RecoveryExecutor._substitute_tool("", "rustscan")
        assert result == ""

    def test_handles_single_token(self):
        result = RecoveryExecutor._substitute_tool("nmap", "rustscan")
        assert result == "rustscan"
