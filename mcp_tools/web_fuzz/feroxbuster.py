# mcp_tools/web_fuzz/feroxbuster.py

from typing import Dict, Any
import asyncio

def register_feroxbuster_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def feroxbuster_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", threads: int = 10, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Feroxbuster for recursive content discovery with enhanced logging.

        Args:
            url: The target URL
            wordlist: Wordlist file to use
            threads: Number of threads
            additional_args: Additional Feroxbuster arguments

        Returns:
            Content discovery results
        """
        data = {
            "url": url,
            "wordlist": wordlist,
            "threads": threads,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Feroxbuster scan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/feroxbuster", data)
        )
        if result.get("success"):
            logger.info(f"✅ Feroxbuster scan completed for {url}")
        else:
            logger.error(f"❌ Feroxbuster scan failed for {url}")
        return result
