"""
Pytest configuration and shared fixtures for HexStrike test suite.

The Flask app is imported once and a test client is provided to every test
via the `client` fixture.  No real external tools are invoked — the
`mock_execute_command` fixture patches `server_core.command_executor.execute_command`
so that tool endpoints can be exercised without any binaries being present on the host.
"""

import pytest
import sys
import os

# Ensure the repo root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask app object *after* path setup
import hexstrike_server as _server
import server_core.command_executor as _command_executor

APP = _server.app


@pytest.fixture(scope="session")
def app():
    """Return the Flask application configured for testing."""
    APP.config.update({
        "TESTING": True,
        # Disable token auth for tests unless overridden per-test
        "HEXSTRIKE_API_TOKEN": None,
    })
    # Make sure token auth is off during tests
    _server.API_TOKEN = None
    yield APP


@pytest.fixture()
def client(app):
    """Flask test client — no real HTTP server is started."""
    return app.test_client()


@pytest.fixture()
def mock_execute_command(monkeypatch):
    """
    Replace server_core.command_executor.execute_command with a lightweight stub
    that returns a successful result without running any real subprocess.

    Individual tests can customise the return value via the returned helper:

        def test_something(client, mock_execute_command):
            mock_execute_command.set_result({"success": False, "stdout": "", "stderr": "fail"})
            ...
    """
    class _MockExecute:
        def __init__(self):
            self._result = {
                "success": True,
                "stdout": "mocked output",
                "stderr": "",
                "command": "mocked",
                "execution_time": 0.01,
                "cached": False,
            }

        def set_result(self, result: dict):
            self._result = result

        def __call__(self, command: str, use_cache: bool = True, cache=None, timeout: int = 300):
            return dict(self._result, command=command)

    stub = _MockExecute()
    monkeypatch.setattr(_command_executor, "execute_command", stub)
    return stub
