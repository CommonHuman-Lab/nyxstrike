"""
Plugin: telnet — MCP tool aligned with the Flask Telnet executor.
"""

from typing import Any, Dict


def register(mcp, api_client, logger):

    @mcp.tool()
    def telnet(
        host: str,
        port: int = 23,
        username: str = "",
        password: str = "",
        command: str = "",
        terminal_disconnect: bool = False,
        timeout: int = 30,
    ) -> Dict[str, Any]:

        try:
            payload = {
                "host": host,
                "port": port,
                "username": username,
                "password": password,
                "command": command,
                "terminal_disconnect": terminal_disconnect,
                "timeout": timeout,
            }

            logger.warning("[MCP TELNET REQUEST] %s", payload)

            resp = api_client.safe_post(
                "api/plugins/telnet",
                payload,
            )

            logger.warning("[MCP TELNET RESPONSE] %s", resp)

            return resp

        except Exception as e:
            logger.error("Telnet MCP tool failed: %s", e)
            return {"success": False, "error": str(e)}
