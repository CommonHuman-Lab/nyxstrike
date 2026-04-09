# mcp_tools/param_fuzz/qsreplace.py

from typing import Dict, Any
import asyncio

def register_qsreplace_tool(mcp, api_client, logger):
    @mcp.tool()
    async def qsreplace_parameter_replacement(urls: str, replacement: str = "FUZZ",
                                       additional_args: str = "") -> Dict[str, Any]:
        """
        Execute qsreplace for query string parameter replacement.

        Args:
            urls: URLs to process
            replacement: Replacement string for parameters
            additional_args: Additional qsreplace arguments

        Returns:
            Parameter replacement results for fuzzing
        """
        data = {
            "urls": urls,
            "replacement": replacement,
            "additional_args": additional_args
        }
        logger.info("🔄 Starting qsreplace parameter replacement")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/qsreplace", data)
        )
        if result.get("success"):
            logger.info("✅ qsreplace parameter replacement completed")
        else:
            logger.error("❌ qsreplace parameter replacement failed")
        return result
