"""
tests/test_error_handling.py

Pure-Python unit tests for IntelligentErrorHandler.classify_error().

No subprocess, no Flask, no server calls.
"""

import pytest

from server_core.error_handling import ErrorType, IntelligentErrorHandler


@pytest.fixture(scope="module")
def handler():
    return IntelligentErrorHandler()


# ---------------------------------------------------------------------------
# classify_error — exception-type dispatch (takes priority over regex)
# ---------------------------------------------------------------------------

class TestClassifyErrorByExceptionType:
    def test_timeout_exception(self, handler):
        assert handler.classify_error("something timed", TimeoutError()) == ErrorType.TIMEOUT

    def test_permission_exception(self, handler):
        assert handler.classify_error("denied", PermissionError()) == ErrorType.PERMISSION_DENIED

    def test_connection_exception(self, handler):
        assert handler.classify_error("unreachable", ConnectionError()) == ErrorType.NETWORK_UNREACHABLE

    def test_file_not_found_exception(self, handler):
        assert handler.classify_error("not found", FileNotFoundError()) == ErrorType.TOOL_NOT_FOUND

    def test_exception_type_wins_over_message(self, handler):
        # Message says "permission denied" but exception says timeout — exception wins.
        assert handler.classify_error("permission denied", TimeoutError()) == ErrorType.TIMEOUT


# ---------------------------------------------------------------------------
# classify_error — regex pattern dispatch (no exception)
# ---------------------------------------------------------------------------

class TestClassifyErrorByMessage:
    @pytest.mark.parametrize("message,expected", [
        # TIMEOUT
        ("connection timeout occurred", ErrorType.TIMEOUT),
        ("operation timed out after 30s", ErrorType.TIMEOUT),
        ("command timeout", ErrorType.TIMEOUT),
        # PERMISSION_DENIED
        ("permission denied: /etc/shadow", ErrorType.PERMISSION_DENIED),
        ("access denied to resource", ErrorType.PERMISSION_DENIED),
        ("sudo required to run this tool", ErrorType.PERMISSION_DENIED),
        ("insufficient privileges", ErrorType.PERMISSION_DENIED),
        # NETWORK_UNREACHABLE
        ("network unreachable", ErrorType.NETWORK_UNREACHABLE),
        ("no route to host", ErrorType.NETWORK_UNREACHABLE),
        ("connection refused on port 80", ErrorType.NETWORK_UNREACHABLE),
        ("connection reset by peer", ErrorType.NETWORK_UNREACHABLE),
        # RATE_LIMITED
        ("rate limit exceeded", ErrorType.RATE_LIMITED),
        ("too many requests (429)", ErrorType.RATE_LIMITED),
        ("request limit exceeded", ErrorType.RATE_LIMITED),
        ("quota exceeded for API key", ErrorType.RATE_LIMITED),
        # TOOL_NOT_FOUND
        ("command not found: nmap", ErrorType.TOOL_NOT_FOUND),
        ("no such file or directory", ErrorType.TOOL_NOT_FOUND),
        ("executable not found", ErrorType.TOOL_NOT_FOUND),
        # INVALID_PARAMETERS
        ("invalid argument: --threads", ErrorType.INVALID_PARAMETERS),
        ("unknown option -x", ErrorType.INVALID_PARAMETERS),
        ("bad parameter: target", ErrorType.INVALID_PARAMETERS),
        ("syntax error near unexpected token", ErrorType.INVALID_PARAMETERS),
        # RESOURCE_EXHAUSTED
        ("out of memory", ErrorType.RESOURCE_EXHAUSTED),
        ("disk full: no space left on device", ErrorType.RESOURCE_EXHAUSTED),
        ("too many open files", ErrorType.RESOURCE_EXHAUSTED),
        # AUTHENTICATION_FAILED
        ("authentication failed for user admin", ErrorType.AUTHENTICATION_FAILED),
        ("login failed: invalid credentials", ErrorType.AUTHENTICATION_FAILED),
        ("unauthorized: invalid token", ErrorType.AUTHENTICATION_FAILED),
        ("expired token", ErrorType.AUTHENTICATION_FAILED),
        # TARGET_UNREACHABLE
        # Note: "host not found" matches TOOL_NOT_FOUND first ("not found" pattern)
        # Use messages that only match TARGET_UNREACHABLE patterns.
        ("target unreachable", ErrorType.TARGET_UNREACHABLE),
        ("target not responding", ErrorType.TARGET_UNREACHABLE),
        ("target down", ErrorType.TARGET_UNREACHABLE),
        ("dns resolution failed for example.com", ErrorType.TARGET_UNREACHABLE),
        # PARSING_ERROR
        ("parse error at line 42", ErrorType.PARSING_ERROR),
        ("json decode error: unexpected token", ErrorType.PARSING_ERROR),
        ("invalid format: expected xml", ErrorType.PARSING_ERROR),
        ("malformed response from server", ErrorType.PARSING_ERROR),
    ])
    def test_message_classification(self, handler, message, expected):
        assert handler.classify_error(message) == expected

    def test_unknown_message_returns_unknown(self, handler):
        assert handler.classify_error("something totally unrecognised xyz123") == ErrorType.UNKNOWN

    def test_empty_message_returns_unknown(self, handler):
        assert handler.classify_error("") == ErrorType.UNKNOWN

    def test_case_insensitive_matching(self, handler):
        assert handler.classify_error("TIMEOUT OCCURRED") == ErrorType.TIMEOUT
        assert handler.classify_error("Permission Denied") == ErrorType.PERMISSION_DENIED
