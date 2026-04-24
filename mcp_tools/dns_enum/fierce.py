# mcp_tools/dns_enum/fierce.py

from typing import Dict, Any
import asyncio

def register_fierce_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def fierce_scan(domain: str, dns_server: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute fierce for DNS reconnaissance with enhanced logging.

        Args:
            domain: Target domain
            dns_server: DNS server to use
            additional_args: Additional fierce arguments

        Returns:
            DNS reconnaissance results
        """
        data = {
            "domain": domain,
            "dns_server": dns_server,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Fierce DNS recon: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/fierce", data)
        )
        if result.get("success"):
            logger.info(f"✅ Fierce completed for {domain}")
        else:
            logger.error(f"❌ Fierce failed for {domain}")
        return result