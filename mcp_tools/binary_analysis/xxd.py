# mcp_tools/binary_analysis/xxd.py

from typing import Dict, Any
import asyncio

def register_xxd_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def xxd_hexdump(file_path: str, offset: str = "0", length: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Create a hex dump of a file using xxd with enhanced logging.

        Args:
            file_path: Path to the file
            offset: Offset to start reading from
            length: Number of bytes to read
            additional_args: Additional xxd arguments

        Returns:
            Hex dump results
        """
        data = {
            "file_path": file_path,
            "offset": offset,
            "length": length,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting XXD hex dump: {file_path}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/xxd", data)
        )
        if result.get("success"):
            logger.info(f"✅ XXD hex dump completed for {file_path}")
        else:
            logger.error(f"❌ XXD hex dump failed for {file_path}")
        return result