"""
server_api/burp_agent

Flask blueprint providing the agent loop API consumed by the NyxStrike
Burp Suite extension.

Endpoints:
  POST /api/burp/agent/start              Start an autonomous pentest agent session
  GET  /api/burp/agent/<id>/stream        SSE stream of agent progress and events
  POST /api/burp/agent/<id>/confirm       Approve or reject a pending tool call
  POST /api/burp/agent/<id>/cancel        Cancel a running agent session
"""

from .routes import api_burp_agent_bp

__all__ = ["api_burp_agent_bp"]
