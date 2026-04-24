# mcp_tools/recon/amass.py

from typing import Dict, Any
import asyncio

def register_amass_tool(mcp, api_client, logger):
    @mcp.tool()
    async def amass_scan(domain: str, mode: str = "enum", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Amass for subdomain enumeration with enhanced logging.

        Args:
            domain: The target domain
            mode: Amass mode (enum, intel, viz)
            additional_args: Additional Amass arguments

        Returns:
            Subdomain enumeration results
        """
        data = {
            "domain": domain,
            "mode": mode,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Amass {mode}: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/amass", data)
        )
        if result.get("success"):
            logger.info(f"✅ Amass completed for {domain}")
        else:
            logger.error(f"❌ Amass failed for {domain}")
        return result
