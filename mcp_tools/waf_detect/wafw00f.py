# mcp_tools/waf_detect/wafw00f.py

from typing import Dict, Any
import asyncio

def register_wafw00f_tool(mcp, api_client, logger):

    @mcp.tool()
    async def wafw00f_scan(target: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute wafw00f to identify and fingerprint WAF products with enhanced logging.

        Args:
            target: Target URL or IP
            additional_args: Additional wafw00f arguments

        Returns:
            WAF detection results
        """
        data = {
            "target": target,
            "additional_args": additional_args
        }
        logger.info(f"🛡️ Starting Wafw00f WAF detection: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/wafw00f", data)
        )
        if result.get("success"):
            logger.info(f"✅ Wafw00f completed for {target}")
        else:
            logger.error(f"❌ Wafw00f failed for {target}")
        return result