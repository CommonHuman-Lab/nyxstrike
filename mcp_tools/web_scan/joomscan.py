from typing import Dict, Any
import asyncio

def register_osint_joomscan_tool(mcp, api_client, logger):
    @mcp.tool()
    async def joomscan_analyze(url: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Joomscan for Joomla vulnerability scanning with enhanced logging.

        Args:
            url: The Joomla site URL
            additional_args: Additional Joomscan arguments

        Returns:
            Joomla vulnerability scan results
        """
        data = {
            "url": url,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Joomscan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/web_recon/joomscan", data)
        )
        if result.get("success"):
            logger.info(f"✅ Joomscan completed for {url}")
        else:
            logger.error(f"❌ Joomscan failed for {url}")
        return result
