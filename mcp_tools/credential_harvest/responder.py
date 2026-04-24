# mcp_tools/credential_harvest/responder.py

from typing import Dict, Any
import asyncio

def register_responder_tool(mcp, api_client, logger):

    @mcp.tool()
    async def responder_credential_harvest(interface: str = "eth0", analyze: bool = False,
                                   wpad: bool = True, force_wpad_auth: bool = False,
                                   fingerprint: bool = False, duration: int = 300,
                                   additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Responder for credential harvesting with enhanced logging.

        Args:
            interface: Network interface to use
            analyze: Analyze mode only
            wpad: Enable WPAD rogue proxy
            force_wpad_auth: Force WPAD authentication
            fingerprint: Fingerprint mode
            duration: Duration to run in seconds
            additional_args: Additional Responder arguments

        Returns:
            Credential harvesting results
        """
        data = {
            "interface": interface,
            "analyze": analyze,
            "wpad": wpad,
            "force_wpad_auth": force_wpad_auth,
            "fingerprint": fingerprint,
            "duration": duration,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Responder on interface: {interface}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/responder", data)
        )
        if result.get("success"):
            logger.info(f"✅ Responder completed")
        else:
            logger.error(f"❌ Responder failed")
        return result
