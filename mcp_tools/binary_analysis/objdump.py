# mcp_tools/binary_analysis/objdump.py

from typing import Dict, Any
import asyncio

def register_objdump_tool(mcp, api_client, logger):

    @mcp.tool()
    async def objdump_analyze(binary: str, disassemble: bool = True, additional_args: str = "") -> Dict[str, Any]:
        """
        Analyze a binary using objdump with enhanced logging.

        Args:
            binary: Path to the binary file
            disassemble: Whether to disassemble the binary
            additional_args: Additional objdump arguments

        Returns:
            Binary analysis results
        """
        data = {
            "binary": binary,
            "disassemble": disassemble,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting Objdump analysis: {binary}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/objdump", data)
        )
        if result.get("success"):
            logger.info(f"✅ Objdump analysis completed for {binary}")
        else:
            logger.error(f"❌ Objdump analysis failed for {binary}")
        return result
