"""
Tests for core infrastructure endpoints:
  GET  /health
  GET  /ping
  GET  /api/cache/stats
  POST /api/cache/clear
  GET  /api/telemetry
  POST /api/command  (generic command execution)
"""

import json
import pytest


# ---------------------------------------------------------------------------
# /ping
# ---------------------------------------------------------------------------

class TestPing:
    def test_ping_returns_200(self, client):
        response = client.get("/ping")
        assert response.status_code == 200

    def test_ping_response_shape(self, client):
        data = response = client.get("/ping").get_json()
        assert data["success"] is True
        assert "message" in data
        assert "timestamp" in data

    def test_ping_message_content(self, client):
        data = client.get("/ping").get_json()
        assert "HexStrike" in data["message"]


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_returns_200(self, client, mock_execute_command):
        """
        /health probes tools via execute_command; mock it to avoid spawning
        real subprocesses.
        """
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_shape(self, client, mock_execute_command):
        data = client.get("/health").get_json()
        required_keys = [
            "status",
            "message",
            "version",
            "tools_status",
            "all_essential_tools_available",
            "total_tools_available",
            "total_tools_count",
            "category_stats",
            "cache_stats",
            "telemetry",
            "uptime",
        ]
        for key in required_keys:
            assert key in data, f"Missing key: {key}"

    def test_health_status_value(self, client, mock_execute_command):
        data = client.get("/health").get_json()
        assert data["status"] == "healthy"

    def test_health_category_stats_present(self, client, mock_execute_command):
        data = client.get("/health").get_json()
        stats = data["category_stats"]
        assert isinstance(stats, dict)
        for cat, info in stats.items():
            assert "total" in info
            assert "available" in info

    def test_health_uptime_positive(self, client, mock_execute_command):
        data = client.get("/health").get_json()
        assert data["uptime"] >= 0


# ---------------------------------------------------------------------------
# /api/cache/stats  and  /api/cache/clear
# ---------------------------------------------------------------------------

class TestCache:
    def test_cache_stats_returns_200(self, client):
        response = client.get("/api/cache/stats")
        assert response.status_code == 200

    def test_cache_stats_response_shape(self, client):
        data = client.get("/api/cache/stats").get_json()
        # Cache stats should be a dict (exact keys depend on HexStrikeCache)
        assert isinstance(data, dict)

    def test_cache_clear_returns_success(self, client):
        response = client.post("/api/cache/clear")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True

    def test_cache_clear_message(self, client):
        data = client.post("/api/cache/clear").get_json()
        assert "message" in data


# ---------------------------------------------------------------------------
# /api/telemetry
# ---------------------------------------------------------------------------

class TestTelemetry:
    def test_telemetry_returns_200(self, client):
        response = client.get("/api/telemetry")
        assert response.status_code == 200

    def test_telemetry_response_is_dict(self, client):
        data = client.get("/api/telemetry").get_json()
        assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# /api/command  (generic command execution)
# ---------------------------------------------------------------------------

class TestGenericCommand:
    def test_command_missing_body_returns_400(self, client):
        response = client.post(
            "/api/command",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_command_empty_command_returns_400(self, client):
        response = client.post(
            "/api/command",
            data=json.dumps({"command": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_command_error_message(self, client):
        data = client.post(
            "/api/command",
            data=json.dumps({"command": ""}),
            content_type="application/json",
        ).get_json()
        assert "error" in data

    def test_command_executes_with_mock(self, client, mock_execute_command):
        response = client.post(
            "/api/command",
            data=json.dumps({"command": "echo hello", "use_cache": False}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        # The mock always returns success=True
        assert data["success"] is True

    def test_command_failure_is_forwarded(self, client, mock_execute_command):
        mock_execute_command.set_result({
            "success": False,
            "stdout": "",
            "stderr": "command not found",
            "command": "",
            "execution_time": 0.01,
            "cached": False,
        })
        response = client.post(
            "/api/command",
            data=json.dumps({"command": "nonexistent_tool --version"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is False


# ---------------------------------------------------------------------------
# Auth — verify Bearer token enforcement when token IS configured
# ---------------------------------------------------------------------------

class TestAuth:
    def test_no_token_allows_request(self, client):
        """Default test setup: no token → all requests pass."""
        response = client.get("/ping")
        assert response.status_code == 200

    def test_wrong_token_returns_401(self, app, client):
        """When API_TOKEN is set, wrong token must be rejected."""
        import hexstrike_server as srv
        original = srv.API_TOKEN
        try:
            srv.API_TOKEN = "supersecret"
            response = client.get(
                "/ping",
                headers={"Authorization": "Bearer wrongtoken"},
            )
            assert response.status_code == 401
        finally:
            srv.API_TOKEN = original

    def test_correct_token_allows_request(self, app, client):
        """When API_TOKEN is set, correct token must be accepted."""
        import hexstrike_server as srv
        original = srv.API_TOKEN
        try:
            srv.API_TOKEN = "supersecret"
            response = client.get(
                "/ping",
                headers={"Authorization": "Bearer supersecret"},
            )
            assert response.status_code == 200
        finally:
            srv.API_TOKEN = original

    def test_missing_auth_header_returns_401(self, app, client):
        """When API_TOKEN is set, a request without any header is rejected."""
        import hexstrike_server as srv
        original = srv.API_TOKEN
        try:
            srv.API_TOKEN = "supersecret"
            response = client.get("/ping")
            assert response.status_code == 401
        finally:
            srv.API_TOKEN = original
