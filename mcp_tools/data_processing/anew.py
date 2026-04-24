# mcp_tools/data_processing/anew.py

from typing import Dict, Any
import asyncio

def register_anew_tool(mcp, api_client, logger):
    @mcp.tool()
    async def anew_data_processing(input_data: str, output_file: str = "",
                            additional_args: str = "") -> Dict[str, Any]:
        """
        Execute anew for appending new lines to files (useful for data processing).

        Args:
            input_data: Input data to process
            output_file: Output file path
            additional_args: Additional anew arguments

        Returns:
            Data processing results with unique line filtering
        """
        data = {
            "input_data": input_data,
            "output_file": output_file,
            "additional_args": additional_args
        }
        logger.info("📝 Starting anew data processing")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/anew", data)
        )
        if result.get("success"):
            logger.info("✅ anew data processing completed")
        else:
            logger.error("❌ anew data processing failed")
        return result
