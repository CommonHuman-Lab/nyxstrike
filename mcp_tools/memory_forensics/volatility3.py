# mcp_tools/memory_forensics/volatility3.py

from typing import Dict, Any
import asyncio

def register_volatility3(mcp, api_client, logger):
    
    @mcp.tool()
    async def volatility3_analyze(memory_file: str, plugin: str, output_file: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Volatility3 for advanced memory forensics with enhanced logging.

        Args:
            memory_file: Path to memory dump file
            plugin: Volatility3 plugin to execute
            output_file: Output file path
            additional_args: Additional Volatility3 arguments

        Returns:
            Advanced memory forensics results
        """
        data = {
            "memory_file": memory_file,
            "plugin": plugin,
            "output_file": output_file,
            "additional_args": additional_args
        }
        logger.info(f"🧠 Starting Volatility3 analysis: {plugin}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/volatility3", data)
        )
        if result.get("success"):
            logger.info(f"✅ Volatility3 analysis completed")
        else:
            logger.error(f"❌ Volatility3 analysis failed")
        return result
