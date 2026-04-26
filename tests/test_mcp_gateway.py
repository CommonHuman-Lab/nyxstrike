"""
tests/test_mcp_gateway.py

Unit tests for mcp_tools/gateway.py — the two MCP tools:
  • classify_task  — calls api_client.safe_post("/api/intelligence/classify-task")
  • run_tool       — validates params, fills defaults, calls api_client.safe_post(endpoint)

No real HTTP calls are made; api_client is a MagicMock throughout.
No real tool processes are spawned (conftest.py session patches).
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run(coro):
    """Run an async coroutine synchronously inside tests."""
    return asyncio.run(coro)


def _make_gateway():
    """
    Build a fresh MCP mock + api_client mock and register gateway tools,
    then return (mcp_mock, api_client_mock).
    """
    api_client = MagicMock()
    api_client.safe_post.return_value = {"success": True, "data": "ok"}

    # mcp mock: @mcp.tool() is a decorator factory — collect registered functions
    registered = {}

    def tool_decorator():
        def inner(fn):
            registered[fn.__name__] = fn
            return fn
        return inner

    mcp = MagicMock()
    mcp.tool = tool_decorator

    from mcp_tools.gateway import register_gateway_tools
    register_gateway_tools(mcp, api_client)

    return registered, api_client


# ---------------------------------------------------------------------------
# classify_task
# ---------------------------------------------------------------------------

class TestClassifyTask:
    def setup_method(self):
        self.fns, self.api = _make_gateway()
        self.classify = self.fns["classify_task"]

    def test_calls_correct_endpoint(self):
        self.api.safe_post.return_value = {"success": True}
        _run(self.classify("scan open ports on 10.0.0.1"))
        self.api.safe_post.assert_called_once()
        endpoint, payload = self.api.safe_post.call_args[0]
        assert "classify-task" in endpoint
        assert payload["description"] == "scan open ports on 10.0.0.1"

    def test_injects_usage_hint_on_success(self):
        self.api.safe_post.return_value = {"success": True, "tools": ["nmap"]}
        result = _run(self.classify("anything"))
        assert "usage" in result
        assert "run_tool" in result["usage"]

    def test_no_usage_hint_on_failure(self):
        self.api.safe_post.return_value = {"success": False, "error": "oops"}
        result = _run(self.classify("anything"))
        assert "usage" not in result

    def test_returns_api_response(self):
        self.api.safe_post.return_value = {"success": True, "category": "recon"}
        result = _run(self.classify("recon task"))
        assert result["category"] == "recon"


# ---------------------------------------------------------------------------
# run_tool — valid calls
# ---------------------------------------------------------------------------

class TestRunToolValidCalls:
    def setup_method(self):
        self.fns, self.api = _make_gateway()
        self.run_tool = self.fns["run_tool"]

    def test_known_tool_calls_endpoint(self):
        """nmap is in the registry; run_tool must hit its endpoint."""
        self.api.safe_post.return_value = {"success": True, "output": "scan result"}
        result = _run(self.run_tool("nmap", json.dumps({"target": "10.0.0.1"})))
        assert self.api.safe_post.called
        endpoint = self.api.safe_post.call_args[0][0]
        assert "nmap" in endpoint

    def test_params_forwarded(self):
        self.api.safe_post.return_value = {"success": True}
        _run(self.run_tool("nmap", json.dumps({"target": "192.168.1.1"})))
        _, body = self.api.safe_post.call_args[0]
        assert body["target"] == "192.168.1.1"

    def test_optional_defaults_filled(self):
        """Any optional params not supplied by caller should be filled from registry."""
        from tool_registry import get_tool
        tool_def = get_tool("nmap")
        if not tool_def or not tool_def.get("optional"):
            pytest.skip("nmap has no optional params in registry")

        self.api.safe_post.return_value = {"success": True}
        _run(self.run_tool("nmap", json.dumps({"target": "10.0.0.1"})))
        _, body = self.api.safe_post.call_args[0]
        for k, v in tool_def["optional"].items():
            assert k in body

    def test_accepts_dict_params(self):
        """params may already be a dict (not a JSON string)."""
        self.api.safe_post.return_value = {"success": True}
        result = _run(self.run_tool("nmap", {"target": "10.0.0.1"}))
        assert result.get("success") is True


# ---------------------------------------------------------------------------
# run_tool — error cases
# ---------------------------------------------------------------------------

class TestRunToolErrors:
    def setup_method(self):
        self.fns, self.api = _make_gateway()
        self.run_tool = self.fns["run_tool"]

    def test_unknown_tool_returns_error(self):
        result = _run(self.run_tool("totally_fake_tool_xyz", "{}"))
        assert result["success"] is False
        assert "Unknown tool" in result["error"]

    def test_invalid_json_params_returns_error(self):
        result = _run(self.run_tool("nmap", "{not valid json"))
        assert result["success"] is False
        assert "Invalid params JSON" in result["error"]

    def test_missing_required_param_returns_error(self):
        """nmap requires 'target'; omitting it must be rejected before any HTTP call."""
        result = _run(self.run_tool("nmap", "{}"))
        assert result["success"] is False
        assert "Missing required param" in result["error"]
        self.api.safe_post.assert_not_called()

    def test_no_subprocess_side_effect(self):
        """run_tool must never import or call subprocess directly."""
        import subprocess as _subprocess_module
        original_popen = _subprocess_module.Popen
        with patch.object(_subprocess_module, "Popen", wraps=original_popen) as mock_popen:
            _run(self.run_tool("totally_fake_tool_xyz", "{}"))
            mock_popen.assert_not_called()
