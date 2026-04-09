from typing import Dict, Any
import asyncio

def register_osint_spiderfoot_tool(mcp, api_client, logger):
    @mcp.tool()
    async def spiderfoot(target: str) -> Dict[str, Any]:
        """
        Execute SpiderFoot for OSINT automation with enhanced logging.

        Args:
            target: The target domain or IP for SpiderFoot analysis

        Returns:
            SpiderFoot analysis results
        """
        data = {
            "target": target
            
        }
        logger.info(f"🔍 Starting SpiderFoot: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/osint/spiderfoot", data)
        )
        if result.get("success"):
            logger.info(f"✅ SpiderFoot completed for {target}")
        else:
            logger.error(f"❌ SpiderFoot failed for {target}")
        return result