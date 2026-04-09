# mcp_tools/binary_debug/radare2.py

from typing import Dict, Any
import asyncio

def register_radare2_tools(mcp, api_client, logger):
    
    @mcp.tool()
    async def radare2_analyze(binary: str, commands: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Radare2 for binary analysis and reverse engineering with enhanced logging.

        Args:
            binary: Path to the binary file
            commands: Radare2 commands to execute
            additional_args: Additional Radare2 arguments

        Returns:
            Binary analysis results
        """
        data = {
            "binary": binary,
            "commands": commands,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting Radare2 analysis: {binary}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/radare2", data)
        )
        if result.get("success"):
            logger.info(f"✅ Radare2 analysis completed for {binary}")
        else:
            logger.error(f"❌ Radare2 analysis failed for {binary}")
        return result