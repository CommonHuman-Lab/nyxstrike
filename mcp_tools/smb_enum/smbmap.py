# mcp_tools/smb_enum/smbmap.py

from typing import Dict, Any
import asyncio

def register_smbmap_tool(mcp, api_client, logger):
    @mcp.tool()
    async def smbmap_scan(target: str, username: str = "", password: str = "", domain: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute SMBMap for SMB share enumeration with enhanced logging.

        Args:
            target: The target IP address
            username: Username for authentication
            password: Password for authentication
            domain: Domain for authentication
            additional_args: Additional SMBMap arguments

        Returns:
            SMB share enumeration results
        """
        data = {
            "target": target,
            "username": username,
            "password": password,
            "domain": domain,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting SMBMap: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/smbmap", data)
        )
        if result.get("success"):
            logger.info(f"✅ SMBMap completed for {target}")
        else:
            logger.error(f"❌ SMBMap failed for {target}")
        return result
