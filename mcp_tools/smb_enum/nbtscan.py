# mcp_tools/smb_enum/nbtscan.py

from typing import Dict, Any
import asyncio

def register_nbtscan_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def nbtscan_netbios(target: str, verbose: bool = False, timeout: int = 2,
                       additional_args: str = "") -> Dict[str, Any]:
        """
        Execute nbtscan for NetBIOS name scanning with enhanced logging.

        Args:
            target: The target IP address or range
            verbose: Enable verbose output
            timeout: Timeout in seconds
            additional_args: Additional nbtscan arguments

        Returns:
            NetBIOS name scanning results
        """
        data = {
            "target": target,
            "verbose": verbose,
            "timeout": timeout,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting nbtscan: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/nbtscan", data)
        )
        if result.get("success"):
            logger.info(f"✅ nbtscan completed for {target}")
        else:
            logger.error(f"❌ nbtscan failed for {target}")
        return result


