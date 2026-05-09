"""
Plugin: ssh_client — MCP tool (clean + aligned with Flask SSH executor)
"""

from typing import Dict, Any


def register(mcp, api_client, logger):

    @mcp.tool()
    def ssh(
        host: str,
        port: int = 22,
        username: str = "",
        password: str = "",
        command: str = "",
        disconnect: bool = False,
    ) -> Dict[str, Any]:

        try:
            payload = {
                "host": host,
                "port": port,
                "username": username,
                "password": password,
                "command": command,
                "disconnect": disconnect
            }

            logger.warning(f"[MCP SSH REQUEST] {payload}")

            resp = api_client.safe_post(
                "api/plugins/ssh",
                payload
            )

            logger.warning(f"[MCP SSH RESPONSE] {resp}")

            return resp

        except Exception as e:
            logger.error("SSH MCP tool failed: %s", e)
            return {"success": False, "error": str(e)}