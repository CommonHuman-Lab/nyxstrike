"""
Tests for security tool endpoints.

All tests use the `mock_execute_command` fixture so no real external tools
are required.  Each test class covers:
  - Happy path: valid params → 200 + mocked success result forwarded
  - Validation: missing required params → 400 with an error message
  - Error propagation: mock returns failure → response still 200 but
    success=False (the server forwards the result as-is)

Tools covered:
  nmap, gobuster, nikto, sqlmap, hydra, subfinder, checksec
"""

import json
import pytest


def _post(client, url, payload):
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def assert_tool_success(response, mock_stub):
    """Assert 200 and that the mocked result was forwarded."""
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True


def assert_tool_missing_param(response):
    """Assert 400 and an error key in the body."""
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


# ---------------------------------------------------------------------------
# /api/tools/nmap
# ---------------------------------------------------------------------------

class TestNmap:
    def test_nmap_valid_target(self, client, mock_execute_command):
        response = _post(client, "/api/tools/nmap", {"target": "127.0.0.1"})
        assert_tool_success(response, mock_execute_command)

    def test_nmap_missing_target_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/nmap", {})
        assert_tool_missing_param(response)

    def test_nmap_empty_target_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/nmap", {"target": ""})
        assert_tool_missing_param(response)

    def test_nmap_forwards_failure(self, client, mock_execute_command):
        mock_execute_command.set_result({
            "success": False, "stdout": "", "stderr": "nmap not found",
            "command": "", "execution_time": 0.0, "cached": False,
        })
        response = _post(client, "/api/tools/nmap",
                         {"target": "127.0.0.1", "use_recovery": False})
        assert response.status_code == 200
        assert response.get_json()["success"] is False

    def test_nmap_accepts_optional_params(self, client, mock_execute_command):
        response = _post(client, "/api/tools/nmap", {
            "target": "127.0.0.1",
            "scan_type": "-sV",
            "ports": "80,443",
            "additional_args": "-T3",
        })
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# /api/tools/gobuster
# ---------------------------------------------------------------------------

class TestGobuster:
    def test_gobuster_valid_url(self, client, mock_execute_command):
        response = _post(client, "/api/tools/gobuster",
                         {"url": "http://localhost"})
        assert_tool_success(response, mock_execute_command)

    def test_gobuster_missing_url_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/gobuster", {})
        assert_tool_missing_param(response)

    def test_gobuster_invalid_mode_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/gobuster",
                         {"url": "http://localhost", "mode": "invalid"})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "mode" in data["error"].lower() or "invalid" in data["error"].lower()

    def test_gobuster_valid_modes(self, client, mock_execute_command):
        for mode in ["dir", "dns", "fuzz", "vhost"]:
            response = _post(client, "/api/tools/gobuster",
                             {"url": "http://localhost", "mode": mode})
            assert response.status_code == 200, f"Mode {mode!r} should be accepted"

    def test_gobuster_forwards_failure(self, client, mock_execute_command):
        mock_execute_command.set_result({
            "success": False, "stdout": "", "stderr": "gobuster not found",
            "command": "", "execution_time": 0.0, "cached": False,
        })
        response = _post(client, "/api/tools/gobuster",
                         {"url": "http://localhost", "use_recovery": False})
        assert response.get_json()["success"] is False


# ---------------------------------------------------------------------------
# /api/tools/nikto
# ---------------------------------------------------------------------------

class TestNikto:
    def test_nikto_valid_target(self, client, mock_execute_command):
        response = _post(client, "/api/tools/nikto", {"target": "http://localhost"})
        assert_tool_success(response, mock_execute_command)

    def test_nikto_missing_target_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/nikto", {})
        assert_tool_missing_param(response)

    def test_nikto_accepts_additional_args(self, client, mock_execute_command):
        response = _post(client, "/api/tools/nikto",
                         {"target": "http://localhost", "additional_args": "-Tuning 9"})
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# /api/tools/sqlmap
# ---------------------------------------------------------------------------

class TestSqlmap:
    def test_sqlmap_valid_url(self, client, mock_execute_command):
        response = _post(client, "/api/tools/sqlmap",
                         {"url": "http://localhost/page?id=1"})
        assert_tool_success(response, mock_execute_command)

    def test_sqlmap_missing_url_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/sqlmap", {})
        assert_tool_missing_param(response)

    def test_sqlmap_accepts_post_data(self, client, mock_execute_command):
        response = _post(client, "/api/tools/sqlmap", {
            "url": "http://localhost/login",
            "data": "user=admin&pass=test",
        })
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# /api/tools/hydra
# ---------------------------------------------------------------------------

class TestHydra:
    def _valid_payload(self):
        return {
            "target": "192.168.1.1",
            "service": "ssh",
            "username": "admin",
            "password_file": "/usr/share/wordlists/rockyou.txt",
        }

    def test_hydra_valid_params(self, client, mock_execute_command):
        response = _post(client, "/api/tools/hydra", self._valid_payload())
        assert_tool_success(response, mock_execute_command)

    def test_hydra_missing_target_returns_400(self, client, mock_execute_command):
        payload = self._valid_payload()
        del payload["target"]
        response = _post(client, "/api/tools/hydra", payload)
        assert_tool_missing_param(response)

    def test_hydra_missing_service_returns_400(self, client, mock_execute_command):
        payload = self._valid_payload()
        del payload["service"]
        response = _post(client, "/api/tools/hydra", payload)
        assert_tool_missing_param(response)

    def test_hydra_missing_credentials_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/hydra", {
            "target": "192.168.1.1",
            "service": "ssh",
        })
        assert_tool_missing_param(response)

    def test_hydra_username_file_accepted(self, client, mock_execute_command):
        response = _post(client, "/api/tools/hydra", {
            "target": "192.168.1.1",
            "service": "ftp",
            "username_file": "/tmp/users.txt",
            "password_file": "/tmp/passwords.txt",
        })
        assert response.status_code == 200

    def test_hydra_plain_password_accepted(self, client, mock_execute_command):
        response = _post(client, "/api/tools/hydra", {
            "target": "192.168.1.1",
            "service": "ssh",
            "username": "root",
            "password": "password123",
        })
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# /api/tools/subfinder
# ---------------------------------------------------------------------------

class TestSubfinder:
    def test_subfinder_valid_domain(self, client, mock_execute_command):
        response = _post(client, "/api/tools/subfinder",
                         {"domain": "example.com"})
        assert_tool_success(response, mock_execute_command)

    def test_subfinder_missing_domain_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/subfinder", {})
        assert_tool_missing_param(response)


# ---------------------------------------------------------------------------
# /api/tools/checksec
# ---------------------------------------------------------------------------

class TestChecksec:
    def test_checksec_valid_binary(self, client, mock_execute_command):
        response = _post(client, "/api/tools/checksec",
                         {"binary": "/bin/ls"})
        assert_tool_success(response, mock_execute_command)

    def test_checksec_missing_binary_returns_400(self, client, mock_execute_command):
        response = _post(client, "/api/tools/checksec", {})
        assert_tool_missing_param(response)


# ---------------------------------------------------------------------------
# Cross-cutting: response shape for all tool endpoints
# ---------------------------------------------------------------------------

class TestToolResponseShape:
    """
    All tool endpoints should forward the execute_command result dict as JSON.
    The mock always returns success=True with 'stdout', 'stderr', 'command',
    'execution_time', 'cached' keys.
    """

    ENDPOINTS_AND_PAYLOADS = [
        ("/api/tools/nmap",       {"target": "127.0.0.1"}),
        ("/api/tools/gobuster",   {"url": "http://localhost"}),
        ("/api/tools/nikto",      {"target": "http://localhost"}),
        ("/api/tools/sqlmap",     {"url": "http://localhost/page?id=1"}),
        ("/api/tools/checksec",   {"binary": "/bin/ls"}),
        ("/api/tools/subfinder",  {"domain": "example.com"}),
    ]

    @pytest.mark.parametrize("endpoint,payload", ENDPOINTS_AND_PAYLOADS)
    def test_response_contains_success_key(self, client, mock_execute_command,
                                           endpoint, payload):
        data = _post(client, endpoint, payload).get_json()
        assert "success" in data

    @pytest.mark.parametrize("endpoint,payload", ENDPOINTS_AND_PAYLOADS)
    def test_response_contains_stdout(self, client, mock_execute_command,
                                      endpoint, payload):
        data = _post(client, endpoint, payload).get_json()
        assert "stdout" in data
