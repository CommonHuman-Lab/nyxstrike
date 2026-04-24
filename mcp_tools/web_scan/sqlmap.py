# mcp_tools/web_scan/sqlmap.py

from typing import Dict, Any
import asyncio

def register_sqlmap_tool(mcp, api_client, logger):
    @mcp.tool()
    async def sqlmap_scan(url: str, data: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute SQLMap for SQL injection testing with enhanced logging.

        Args:
            url: The target URL
            data: POST data for testing
            additional_args: Additional SQLMap arguments

        Returns:
            SQL injection test results
        """
        data_payload = {
            "url": url,
            "data": data,
            "additional_args": additional_args
        }
        logger.info(f"💉 Starting SQLMap scan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/sqlmap", data_payload)
        )
        if result.get("success"):
            logger.info(f"✅ SQLMap scan completed for {url}")
        else:
            logger.error(f"❌ SQLMap scan failed for {url}")
        return result