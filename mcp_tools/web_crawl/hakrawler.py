# mcp_tools/web_crawl/hakrawler.py

from typing import Dict, Any
import asyncio

def register_hakrawler_tools(mcp, api_client, logger):

    @mcp.tool()
    async def hakrawler_crawl(url: str, depth: int = 2, forms: bool = True, robots: bool = True, sitemap: bool = True, wayback: bool = False, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Hakrawler for web endpoint discovery with enhanced logging.

        Note: Uses standard Kali Linux hakrawler (hakluke/hakrawler) with parameter mapping:
        - url: Piped via echo to stdin (not -url flag)
        - depth: Mapped to -d flag (not -depth)
        - forms: Mapped to -s flag for showing sources
        - robots/sitemap/wayback: Mapped to -subs for subdomain inclusion
        - Always includes -u for unique URLs

        Args:
            url: Target URL to crawl
            depth: Crawling depth (mapped to -d)
            forms: Include forms in crawling (mapped to -s)
            robots: Check robots.txt (mapped to -subs)
            sitemap: Check sitemap.xml (mapped to -subs)
            wayback: Use Wayback Machine (mapped to -subs)
            additional_args: Additional Hakrawler arguments

        Returns:
            Web endpoint discovery results
        """
        data = {
            "url": url,
            "depth": depth,
            "forms": forms,
            "robots": robots,
            "sitemap": sitemap,
            "wayback": wayback,
            "additional_args": additional_args
        }
        logger.info(f"🕷️ Starting Hakrawler crawling: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/hakrawler", data)
        )
        if result.get("success"):
            logger.info(f"✅ Hakrawler crawling completed")
        else:
            logger.error(f"❌ Hakrawler crawling failed")
        return result
