# mcp_tools/recon/subfinder.py

from typing import Dict, Any
import asyncio

def register_subfinder_tool(mcp, api_client, logger):
    @mcp.tool()
    async def subfinder_scan(domain: str, silent: bool = True, all_sources: bool = False, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Subfinder for passive subdomain enumeration with enhanced logging.

        Args:
            domain: The target domain
            silent: Run in silent mode
            all_sources: Use all sources
            additional_args: Additional Subfinder arguments

        Returns:
            Passive subdomain enumeration results
        """
        data = {
            "domain": domain,
            "silent": silent,
            "all_sources": all_sources,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Subfinder: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/subfinder", data)
        )
        if result.get("success"):
            logger.info(f"✅ Subfinder completed for {domain}")
        else:
            logger.error(f"❌ Subfinder failed for {domain}")
        return result
