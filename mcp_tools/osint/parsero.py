from typing import Dict, Any
import asyncio

def register_osint_parsero_tool(mcp, api_client, logger):
    @mcp.tool()
    async def parsero(target: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Parsero for Robots.txt analysis with enhanced logging.

        Args:
            target: The target URL for Parsero analysis
            additional_args: Optional additional arguments for Parsero

        Returns:
            Parsero analysis results
        """
        data = {
            "target": target,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Parsero: {target} with args: {additional_args}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/osint/parsero", data)
        )
        if result.get("success"):
            logger.info(f"✅ Parsero completed for {target}")
        else:
            logger.error(f"❌ Parsero failed for {target}")
        return result