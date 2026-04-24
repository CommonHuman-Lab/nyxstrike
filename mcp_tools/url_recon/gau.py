# mcp_tools/url_recon/gau.py

from typing import Dict, Any
import asyncio

def register_gau_tool(mcp, api_client, logger):
    @mcp.tool()
    async def gau_discovery(domain: str, providers: str = "wayback,commoncrawl,otx,urlscan",
                     include_subs: bool = True, blacklist: str = "png,jpg,gif,jpeg,swf,woff,svg,pdf,css,ico",
                     additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Gau (Get All URLs) for URL discovery from multiple sources with enhanced logging.

        Args:
            domain: The target domain
            providers: Data providers to use
            include_subs: Include subdomains
            blacklist: File extensions to blacklist
            additional_args: Additional Gau arguments

        Returns:
            Comprehensive URL discovery results from multiple sources
        """
        data = {
            "domain": domain,
            "providers": providers,
            "include_subs": include_subs,
            "blacklist": blacklist,
            "additional_args": additional_args
        }
        logger.info(f"📡 Starting Gau URL discovery: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/gau", data)
        )
        if result.get("success"):
            logger.info(f"✅ Gau URL discovery completed for {domain}")
        else:
            logger.error(f"❌ Gau URL discovery failed for {domain}")
        return result