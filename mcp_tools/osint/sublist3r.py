from typing import Dict, Any
import asyncio

def register_osint_sublist3r_tool(mcp, api_client, logger):
    @mcp.tool()
    async def sublist3r(domain: str, threads: int = 3, engine: str = "") -> Dict[str, Any]:
        """
        Execute Sublist3r for subdomain enumeration with enhanced logging.

        Args:
            domain: The target domain for subdomain enumeration
            threads: Number of threads to use (default: 3)
            engine: Optional search engine to use (e.g., "google", "bing")

        Returns:
            Sublist3r analysis results
        """
        data = {
            "domain": domain,
            "threads": threads,
            "engine": engine
        }
        logger.info(f"🔍 Starting Sublist3r: {domain} with {threads} threads and engine '{engine}'")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/osint/sublist3r", data)
        )
        if result.get("success"):
            logger.info(f"✅ Sublist3r completed for {domain}")
        else:
            logger.error(f"❌ Sublist3r failed for {domain}")
        return result