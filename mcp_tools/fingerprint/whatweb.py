# mcp_tools/web_scan/whatweb.py

from typing import Dict, Any
import asyncio

def register_whatweb_tool(mcp, api_client, logger):
    @mcp.tool()
    async def whatweb_analyze(url: str) -> Dict[str, Any]:
        """
        Execute WhatWeb for web technology fingerprinting with enhanced logging.

        Args:
            url: The target website URL

        Returns:
            Web technology fingerprinting results
        """
        data = {
            "url": url
        }
        logger.info(f"🔍 Starting WhatWeb: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/web_recon/whatweb", data)
        )
        if result.get("success"):
            logger.info(f"✅ WhatWeb completed for {url}")
        else:
            logger.error(f"❌ WhatWeb failed for {url}")
        return result