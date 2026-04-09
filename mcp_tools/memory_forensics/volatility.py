# mcp_tools/memory_forensics/volatility.py

from typing import Dict, Any
import asyncio

def register_volatility_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def volatility_analyze(memory_file: str, plugin: str, profile: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Volatility for memory forensics analysis with enhanced logging.

        Args:
            memory_file: Path to memory dump file
            plugin: Volatility plugin to use
            profile: Memory profile to use
            additional_args: Additional Volatility arguments

        Returns:
            Memory forensics analysis results
        """
        data = {
            "memory_file": memory_file,
            "plugin": plugin,
            "profile": profile,
            "additional_args": additional_args
        }
        logger.info(f"🧠 Starting Volatility analysis: {plugin}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/volatility", data)
        )
        if result.get("success"):
            logger.info(f"✅ Volatility analysis completed")
        else:
            logger.error(f"❌ Volatility analysis failed")
        return result