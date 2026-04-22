"""
server_core/internal_api_client.py

Lightweight HTTP client for in-process calls back to the NyxStrike REST API.

Used by the chat tool-calling layer so the embedded LLM can execute security
tools via the same endpoints that the MCP client and the web UI use.  All
requests go to 127.0.0.1:{NYXSTRIKE_PORT} — never to an external host.

Usage:
  from server_core.internal_api_client import internal_api
  result = internal_api.run_tool("nmap", {"target": "10.0.0.1"})
  classification = internal_api.classify_task("port scan 10.0.0.1")
"""

import logging
import os
from typing import Any, Dict

import requests

import server_core.config_core as config_core

logger = logging.getLogger(__name__)


def _server_url() -> str:
  host = os.environ.get("NYXSTRIKE_HOST") or config_core.get("NYXSTRIKE_HOST", "127.0.0.1")
  port = os.environ.get("NYXSTRIKE_PORT") or config_core.get("NYXSTRIKE_PORT", "8888")
  return f"http://{host}:{port}"


def _auth_headers() -> Dict[str, str]:
  token = os.environ.get("NYXSTRIKE_API_TOKEN") or config_core.get("NYXSTRIKE_API_TOKEN", "")
  if token:
    return {"Authorization": f"Bearer {token}"}
  return {}


class _InternalApiClient:
  """Singleton HTTP client pointing at localhost NyxStrike API."""

  def __init__(self) -> None:
    self._session = requests.Session()
    # Reuse connection pool; no background thread needed since we're in-process
    self._session.headers.update({"Content-Type": "application/json"})

  def _post(self, endpoint: str, data: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    url = f"{_server_url()}/{endpoint.lstrip('/')}"
    headers = _auth_headers()
    try:
      resp = self._session.post(url, json=data, headers=headers, timeout=timeout)
      resp.raise_for_status()
      return resp.json()
    except requests.exceptions.ConnectionError as exc:
      logger.error("internal_api: connection error to %s: %s", url, exc)
      return {"success": False, "error": f"Connection error: {exc}"}
    except requests.exceptions.Timeout:
      logger.error("internal_api: timeout calling %s", url)
      return {"success": False, "error": "Request timed out"}
    except Exception as exc:
      logger.error("internal_api: error calling %s: %s", url, exc)
      return {"success": False, "error": str(exc)}

  def classify_task(self, description: str) -> Dict[str, Any]:
    """Call /api/intelligence/classify-task and return the response dict.

    Returns keys: category, confidence, tools (list), tool_summary (str).
    """
    return self._post("api/intelligence/classify-task", {"description": description})

  def run_tool(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """POST to a tool endpoint and return the result.

    Args:
      endpoint: The tool's REST endpoint path, e.g. "/api/tools/nmap".
      params:   The parameter dict to pass as JSON body.
    """
    return self._post(endpoint, params, timeout=300)


# Module-level singleton — import and use directly
internal_api = _InternalApiClient()
