# mcp_tools/file_carving/foremost.py

from typing import Dict, Any
import asyncio

def register_foremost_tool(mcp, api_client, logger):

    @mcp.tool()
    async def foremost_carving(input_file: str, output_dir: str = "/tmp/foremost_output", file_types: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Foremost for file carving with enhanced logging.

        Args:
            input_file: Input file or device to carve
            output_dir: Output directory for carved files
            file_types: File types to carve (jpg,gif,png,etc.)
            additional_args: Additional Foremost arguments

        Returns:
            File carving results
        """
        data = {
            "input_file": input_file,
            "output_dir": output_dir,
            "file_types": file_types,
            "additional_args": additional_args
        }
        logger.info(f"📁 Starting Foremost file carving: {input_file}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/foremost", data)
        )
        if result.get("success"):
            logger.info(f"✅ Foremost carving completed")
        else:
            logger.error(f"❌ Foremost carving failed")
        return result
