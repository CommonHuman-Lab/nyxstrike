"""
tests/test_auth_middleware.py

Tests for the optional bearer-token auth enforced in nyxstrike_server.py
via the ``optional_bearer_auth`` before_request hook.

Safety guarantee
────────────────
The Flask test client never fires any real tool; execute_command is patched
at the session level by conftest.py.
"""

import os
import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# App factory helpers
# ---------------------------------------------------------------------------

def _make_client(token):
    """
    Return a Flask test client configured with the given API token.
    PROPAGATE_EXCEPTIONS=False ensures abort() becomes an HTTP response,
    not an unhandled exception in test mode.
    """
    from nyxstrike_server import app
    app.config["TESTING"] = True
    app.config["PROPAGATE_EXCEPTIONS"] = False

    with patch("nyxstrike_server.API_TOKEN", token):
        yield app.test_client()


@pytest.fixture()
def client_no_token():
    yield from _make_client(None)


@pytest.fixture()
def client_with_token():
    yield from _make_client("supersecret")


# ---------------------------------------------------------------------------
# No token configured — all requests pass through
# ---------------------------------------------------------------------------

class TestNoTokenConfigured:
    def test_get_health_without_auth_header(self, client_no_token):
        r = client_no_token.get("/api/health")
        assert r.status_code != 401

    def test_post_without_auth_header_allowed(self, client_no_token):
        with patch("server_api.net_scan.nmap.execute_command",
                   return_value={"success": True, "output": "ok", "returncode": 0}):
            r = client_no_token.post(
                "/api/tools/nmap",
                json={"target": "10.0.0.1"},
                content_type="application/json",
            )
        # Not 401 — unauthenticated requests are allowed when no token is set
        assert r.status_code != 401

    def test_any_bearer_token_ignored(self, client_no_token):
        r = client_no_token.get(
            "/api/health",
            headers={"Authorization": "Bearer wrong_token"},
        )
        assert r.status_code != 401


# ---------------------------------------------------------------------------
# Token configured — authentication enforced
# ---------------------------------------------------------------------------

class TestTokenConfigured:
    def test_missing_auth_header_returns_401(self, client_with_token):
        r = client_with_token.get("/api/health")
        assert r.status_code == 401

    def test_wrong_token_returns_401(self, client_with_token):
        r = client_with_token.get(
            "/api/health",
            headers={"Authorization": "Bearer wrongtoken"},
        )
        assert r.status_code == 401

    def test_correct_token_returns_non_401(self, client_with_token):
        r = client_with_token.get(
            "/api/health",
            headers={"Authorization": "Bearer supersecret"},
        )
        assert r.status_code != 401

    def test_token_without_bearer_prefix_returns_401(self, client_with_token):
        r = client_with_token.get(
            "/api/health",
            headers={"Authorization": "supersecret"},  # missing "Bearer " prefix
        )
        assert r.status_code == 401

    def test_post_with_correct_token_allowed(self, client_with_token):
        with patch("server_api.net_scan.nmap.execute_command",
                   return_value={"success": True, "output": "ok", "returncode": 0}):
            r = client_with_token.post(
                "/api/tools/nmap",
                json={"target": "10.0.0.1"},
                content_type="application/json",
                headers={"Authorization": "Bearer supersecret"},
            )
        assert r.status_code != 401

    def test_post_with_wrong_token_returns_401(self, client_with_token):
        r = client_with_token.post(
            "/api/tools/nmap",
            json={"target": "10.0.0.1"},
            content_type="application/json",
            headers={"Authorization": "Bearer badtoken"},
        )
        assert r.status_code == 401

    def test_timing_safe_comparison_used(self):
        """
        Verify that token comparison goes through hmac.compare_digest, not ==.
        This is a structural check rather than a timing attack test.
        """
        import inspect
        import nyxstrike_server as srv
        source = inspect.getsource(srv.optional_bearer_auth)
        assert "hmac.compare_digest" in source, (
            "Token comparison must use hmac.compare_digest to prevent timing attacks"
        )


# ---------------------------------------------------------------------------
# JSON enforcement middleware
# ---------------------------------------------------------------------------

class TestRequireJsonMiddleware:
    def test_post_with_invalid_json_body_does_not_return_2xx(self, client_no_token):
        """Malformed JSON with application/json content-type should not succeed."""
        r = client_no_token.post(
            "/api/tools/nmap",
            data="not json at all",
            content_type="application/json",
        )
        # Either 400 (middleware catches it) or 500 (unhandled — a bug worth knowing about)
        # The critical assertion is it never returns 2xx (success)
        assert r.status_code not in (200, 201, 204)

    def test_post_missing_content_type_is_handled(self, client_no_token):
        """Non-JSON content types should not cause a 2xx success on a JSON endpoint."""
        r = client_no_token.post("/api/tools/nmap", data="some data")
        assert r.status_code not in (200, 201, 204)
