# mcp_tools/web_fuzz/dirb.py

from typing import Dict, Any
import asyncio

def register_dirb_tool(mcp, api_client, logger):
    @mcp.tool()
    async def dirb_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Dirb for directory brute forcing with enhanced logging.

        Args:
            url: The target URL
            wordlist: Path to wordlist file
            additional_args: Additional Dirb arguments

        Returns:
            Scan results with enhanced telemetry
        """
        data = {
            "url": url,
            "wordlist": wordlist,
            "additional_args": additional_args
        }
        logger.info(f"📁 Starting Dirb scan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/dirb", data)
        )
        if result.get("success"):
            logger.info(f"✅ Dirb scan completed for {url}")
        else:
            logger.error(f"❌ Dirb scan failed for {url}")
        return result