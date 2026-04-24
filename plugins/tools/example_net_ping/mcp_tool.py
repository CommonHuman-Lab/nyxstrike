"""
Plugin: example_net_ping — mcp_tool.py
FastMCP tool registration for the net_ping plugin.

This file is the MCP-side half of the plugin.
It must expose a module-level `register(mcp, api_client, logger)` function.
The plugin MCP loader calls it automatically during server setup.
"""

import asyncio
from typing import Dict, Any


def register(mcp, api_client, logger):
  """Register the nyxstrike_net_ping MCP tool."""

  @mcp.tool()
  async def nyxstrike_net_ping(
    target: str,
    count: int = 4,
    timeout: int = 10,
  ) -> Dict[str, Any]:
    """
    ICMP ping a host and return latency and packet-loss statistics.

    Args:
        target:  Hostname or IP address to ping
        count:   Number of ICMP packets to send (1–20, default 4)
        timeout: Per-packet timeout in seconds (1–60, default 10)

    Returns:
        Ping results including raw output, packet stats, and RTT values
    """
    try:
      loop = asyncio.get_running_loop()
      response = await loop.run_in_executor(
        None,
        lambda: api_client.safe_post(
          "api/plugins/net_ping",
          {"target": target, "count": count, "timeout": timeout},
        ),
      )
      return response
    except Exception as e:
      logger.error("nyxstrike_net_ping failed: %s", e)
      return {"error": str(e), "success": False}
