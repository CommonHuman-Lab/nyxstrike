# mcp_tools/web_scan/wpscan.py

from typing import Dict, Any
import asyncio

def register_wpscan_tool(mcp, api_client, logger):
    @mcp.tool()
    async def wpscan_analyze(url: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute WPScan for WordPress vulnerability scanning with enhanced logging.

        Args:
            url: The WordPress site URL
            additional_args: Additional WPScan arguments

        Returns:
            WordPress vulnerability scan results
        """
        data = {
            "url": url,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting WPScan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/wpscan", data)
        )
        if result.get("success"):
            logger.info(f"✅ WPScan completed for {url}")
        else:
            logger.error(f"❌ WPScan failed for {url}")
        return result