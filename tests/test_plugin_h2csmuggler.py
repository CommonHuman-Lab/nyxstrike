"""
tests/test_plugin_h2csmuggler.py

Validation and command-builder tests for the h2csmuggler plugin endpoint.

These tests run against the Flask app test client and patch the dynamically
loaded plugin module's local execute_command reference so no real tool runs.
"""

import os
import sys
from unittest.mock import patch

import pytest


_MOCK_RESULT = {
    "success": True,
    "stdout": "mocked",
    "stderr": "",
    "return_code": 0,
    "execution_time": 0.01,
}


@pytest.fixture(scope="module")
def app():
    os.environ.setdefault("NYXSTRIKE_API_TOKEN", "")
    from nyxstrike_server import app as _app

    _app.config["TESTING"] = True
    return _app


@pytest.fixture()
def client(app):
    return app.test_client()


def _post(client, payload):
    return client.post(
        "/api/plugins/h2csmuggler",
        json=payload,
        content_type="application/json",
    )


def _plugin_module():
    mod = sys.modules.get("_plugin_tool_server_api_h2csmuggler")
    assert mod is not None, "h2csmuggler plugin module not loaded"
    return mod


class TestH2csmugglerValidation:
    def test_missing_proxy_returns_400(self, client):
        r = _post(client, {})
        assert r.status_code == 400
        assert r.get_json()["error"] == "Missing required parameter: proxy"

    def test_proxy_scheme_required(self, client):
        r = _post(client, {"proxy": "localhost:8102", "test": True})
        assert r.status_code == 400
        assert "proxy must start with http:// or https://" in r.get_json()["error"]

    def test_exploit_mode_requires_target_url(self, client):
        r = _post(client, {"proxy": "https://localhost:8102"})
        assert r.status_code == 400
        assert r.get_json()["error"] == "target_url is required in exploit mode"

    def test_target_url_scheme_required_in_exploit_mode(self, client):
        r = _post(
            client,
            {"proxy": "https://localhost:8102", "target_url": "localhost/flag"},
        )
        assert r.status_code == 400
        assert "target_url must start with http:// or https://" in r.get_json()["error"]

    def test_scan_list_file_must_exist(self, client):
        r = _post(
            client,
            {"proxy": "https://localhost:8102", "scan_list": "/tmp/opencode/does-not-exist"},
        )
        assert r.status_code == 400
        assert r.get_json()["error"] == "scan_list file not found"

    def test_scan_and_test_conflict_rejected(self, client):
        r = _post(
            client,
            {
                "proxy": "https://localhost:8102",
                "scan_list": "/etc/hosts",
                "test": True,
            },
        )
        assert r.status_code == 400
        assert r.get_json()["error"] == "scan_list mode cannot be combined with test=true"


class TestH2csmugglerCommandBuilder:
    def test_test_mode_builds_t_flag(self, client):
        with patch.object(_plugin_module(), "execute_command", return_value=_MOCK_RESULT) as mock_exec:
            r = _post(client, {"proxy": "https://localhost:8102", "test": True})
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "python3" in cmd
            assert "h2csmuggler.py" in cmd
            assert "-x" in cmd and "https://localhost:8102" in cmd
            assert " -t" in cmd

    def test_scan_mode_builds_scan_flags_and_clamps_threads(self, client):
        with patch.object(_plugin_module(), "execute_command", return_value=_MOCK_RESULT) as mock_exec:
            r = _post(
                client,
                {
                    "proxy": "https://localhost:8102",
                    "scan_list": "/etc/hosts",
                    "threads": 999,
                },
            )
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "--scan-list" in cmd
            assert "/etc/hosts" in cmd
            assert "--threads 50" in cmd

    def test_exploit_mode_builds_request_headers_and_data(self, client):
        with patch.object(_plugin_module(), "execute_command", return_value=_MOCK_RESULT) as mock_exec:
            r = _post(
                client,
                {
                    "proxy": "https://localhost:8102",
                    "target_url": "http://localhost/flag",
                    "request": "post",
                    "data": '{"x":1}',
                    "headers": "X-Test: 1; X-Forwarded-For: 127.0.0.1",
                    "wordlist": "/tmp/paths.txt",
                    "verbose": True,
                    "upgrade_only": True,
                    "additional_args": "--foo bar",
                },
            )
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-X POST" in cmd
            assert "-d" in cmd and '{"x":1}' in cmd
            assert "-H 'X-Test: 1'" in cmd
            assert "-H 'X-Forwarded-For: 127.0.0.1'" in cmd
            assert "-i /tmp/paths.txt" in cmd
            assert "--upgrade-only" in cmd
            assert " -v" in cmd
            assert "http://localhost/flag" in cmd
            assert "--foo" in cmd and "bar" in cmd

    def test_max_time_is_clamped(self, client):
        with patch.object(_plugin_module(), "execute_command", return_value=_MOCK_RESULT) as mock_exec:
            r = _post(
                client,
                {
                    "proxy": "https://localhost:8102",
                    "target_url": "http://localhost/",
                    "max_time": 999,
                },
            )
            assert r.status_code == 200
            cmd = mock_exec.call_args[0][0]
            assert "-m 120" in cmd
