# mcp_tools/smb_enum/netexec.py

from typing import Dict, Any
import asyncio

def register_netexec_tool(mcp, api_client, logger):
    @mcp.tool()
    async def netexec_scan(target: str, protocol: str = "smb", username: str = "", password: str = "", hash_value: str = "", module: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute NetExec (formerly CrackMapExec) for network enumeration with enhanced logging.

        Args:
            target: The target IP or network
            protocol: Protocol to use (smb, ssh, winrm, etc.)
            username: Username for authentication
            password: Password for authentication
            hash_value: Hash for pass-the-hash attacks
            module: NetExec module to execute
            additional_args: Additional NetExec arguments

        Returns:
            Network enumeration results
        """
        data = {
            "target": target,
            "protocol": protocol,
            "username": username,
            "password": password,
            "hash": hash_value,
            "module": module,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting NetExec {protocol} scan: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/netexec", data)
        )
        if result.get("success"):
            logger.info(f"✅ NetExec scan completed for {target}")
        else:
            logger.error(f"❌ NetExec scan failed for {target}")
        return result
