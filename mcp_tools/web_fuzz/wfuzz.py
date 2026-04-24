# mcp_tools/web_fuzz/wfuzz.py

from typing import Dict, Any
import asyncio

def register_wfuzz_tool(mcp, api_client, logger):

    @mcp.tool()
    async def wfuzz_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Wfuzz for web application fuzzing with enhanced logging.

        Args:
            url: The target URL (use FUZZ where you want to inject payloads)
            wordlist: Wordlist file to use
            additional_args: Additional Wfuzz arguments

        Returns:
            Web application fuzzing results
        """
        data = {
            "url": url,
            "wordlist": wordlist,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Wfuzz scan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/wfuzz", data)
        )
        if result.get("success"):
            logger.info(f"✅ Wfuzz scan completed for {url}")
        else:
            logger.error(f"❌ Wfuzz scan failed for {url}")
        return result
