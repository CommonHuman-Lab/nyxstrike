# mcp_tools/binary_analysis/binwalk.py

from typing import Dict, Any
import asyncio

def register_binwalk_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def binwalk_analyze(file_path: str, extract: bool = False, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Binwalk for firmware and file analysis with enhanced logging.

        Args:
            file_path: Path to the file to analyze
            extract: Whether to extract discovered files
            additional_args: Additional Binwalk arguments

        Returns:
            Firmware analysis results
        """
        data = {
            "file_path": file_path,
            "extract": extract,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting Binwalk analysis: {file_path}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/binwalk", data)
        )
        if result.get("success"):
            logger.info(f"✅ Binwalk analysis completed for {file_path}")
        else:
            logger.error(f"❌ Binwalk analysis failed for {file_path}")
        return result