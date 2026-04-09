# mcp_tools/url_filter/uro.py

from typing import Dict, Any
import asyncio

def register_uro_tool(mcp, api_client, logger):
    @mcp.tool()
    async def uro_url_filtering(urls: str, whitelist: str = "", blacklist: str = "",
                         additional_args: str = "") -> Dict[str, Any]:
        """
        Execute uro for filtering out similar URLs.

        Args:
            urls: URLs to filter
            whitelist: Whitelist patterns
            blacklist: Blacklist patterns
            additional_args: Additional uro arguments

        Returns:
            Filtered URL results with duplicates removed
        """
        data = {
            "urls": urls,
            "whitelist": whitelist,
            "blacklist": blacklist,
            "additional_args": additional_args
        }
        logger.info("🔍 Starting uro URL filtering")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/uro", data)
        )
        if result.get("success"):
            logger.info("✅ uro URL filtering completed")
        else:
            logger.error("❌ uro URL filtering failed")
        return result
