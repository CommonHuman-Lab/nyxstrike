# mcp_tools/web_fuzz/ffuf.py

from typing import Dict, Any
import asyncio

def register_ffuf_tool(mcp, api_client, logger):
    @mcp.tool()
    async def ffuf_scan(url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt", mode: str = "directory", match_codes: str = "200,204,301,302,307,401,403", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute FFuf for web fuzzing with enhanced logging.

        Args:
            url: The target URL
            wordlist: Wordlist file to use
            mode: Fuzzing mode (directory, vhost, parameter)
            match_codes: HTTP status codes to match
            additional_args: Additional FFuf arguments

        Returns:
            Web fuzzing results
        """
        data = {
            "url": url,
            "wordlist": wordlist,
            "mode": mode,
            "match_codes": match_codes,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting FFuf {mode} fuzzing: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/ffuf", data)
        )
        if result.get("success"):
            logger.info(f"✅ FFuf fuzzing completed for {url}")
        else:
            logger.error(f"❌ FFuf fuzzing failed for {url}")
        return result
