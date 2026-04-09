# mcp_tools/dns_enum/dnsenum.py

from typing import Dict, Any
import asyncio

def register_dnsenum_tool(mcp, api_client, logger):

    @mcp.tool()
    async def dnsenum_scan(domain: str, dns_server: str = "", wordlist: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute dnsenum for DNS enumeration with enhanced logging.

        Args:
            domain: Target domain
            dns_server: DNS server to use
            wordlist: Wordlist for brute forcing
            additional_args: Additional dnsenum arguments

        Returns:
            DNS enumeration results
        """
        data = {
            "domain": domain,
            "dns_server": dns_server,
            "wordlist": wordlist,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting DNSenum: {domain}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/dnsenum", data)
        )
        if result.get("success"):
            logger.info(f"✅ DNSenum completed for {domain}")
        else:
            logger.error(f"❌ DNSenum failed for {domain}")
        return result
