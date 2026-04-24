# mcp_tools/recon/theharvester.py

from typing import Dict, Any
import asyncio

def register_theharvester_tool(mcp, api_client, logger):
    @mcp.tool()
    async def theharvester_scan(domain: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute TheHarvester for passive information gathering with enhanced logging.

        Args:
            domain <string, required> : The target domain
            additional_args <string, optional> : Additional TheHarvester arguments

        Returns:
            Passive information gathering results
        """
        data = {
            "domain": domain,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting TheHarvester: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/recon/theharvester", data)
        )
        if result.get("success"):
            logger.info(f"✅ TheHarvester completed for {domain}")
        else:
            logger.error(f"❌ TheHarvester failed for {domain}")
        return result