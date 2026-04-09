# mcp_tools/binary_analysis/strings.py

from typing import Dict, Any
import asyncio

def register_strings_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def strings_extract(file_path: str, min_len: int = 4, additional_args: str = "") -> Dict[str, Any]:
        """
        Extract strings from a binary file with enhanced logging.

        Args:
            file_path: Path to the file
            min_len: Minimum string length
            additional_args: Additional strings arguments

        Returns:
            String extraction results
        """
        data = {
            "file_path": file_path,
            "min_len": min_len,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting Strings extraction: {file_path}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/strings", data)
        )
        if result.get("success"):
            logger.info(f"✅ Strings extraction completed for {file_path}")
        else:
            logger.error(f"❌ Strings extraction failed for {file_path}")
        return result