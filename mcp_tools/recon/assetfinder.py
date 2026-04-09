from typing import Dict, Any
import asyncio


def register_assetfinder_tool(mcp, api_client, logger):
    @mcp.tool()
    async def assetfinder_scan(domain: str, only_subdomains: bool = True, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Assetfinder for passive subdomain enumeration.

        Args:
            domain: The target domain
            only_subdomains: Use --subs-only output mode
            additional_args: Additional Assetfinder arguments

        Returns:
            Passive subdomain enumeration results
        """
        data = {
            "domain": domain,
            "only_subdomains": only_subdomains,
            "additional_args": additional_args,
        }
        logger.info(f"🔍 Starting Assetfinder: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/assetfinder", data)
        )
        if result.get("success"):
            logger.info(f"✅ Assetfinder completed for {domain}")
        else:
            logger.error(f"❌ Assetfinder failed for {domain}")
        return result
