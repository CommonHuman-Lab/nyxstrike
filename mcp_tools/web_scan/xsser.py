# mcp_tools/web_scan/xsser.py

from typing import Dict, Any
import asyncio

def register_xsser_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def xsser_scan(url: str, params: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute XSSer for XSS vulnerability testing with enhanced logging.

        Args:
            url: The target URL
            params: Parameters to test
            additional_args: Additional XSSer arguments

        Returns:
            XSS vulnerability test results
        """
        data = {
            "url": url,
            "params": params,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting XSSer scan: {url}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/xsser", data)
        )
        if result.get("success"):
            logger.info(f"✅ XSSer scan completed for {url}")
        else:
            logger.error(f"❌ XSSer scan failed for {url}")
        return result