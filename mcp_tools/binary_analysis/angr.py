# mcp_tools/binary_analysis/angr.py

from typing import Dict, Any
import asyncio

def register_angr_tools(mcp, api_client, logger):
    
    @mcp.tool()
    async def angr_symbolic_execution(binary: str, script_content: str = "",
                               find_address: str = "", avoid_addresses: str = "",
                               analysis_type: str = "symbolic", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute angr for symbolic execution and binary analysis.

        Args:
            binary: Binary to analyze
            script_content: Custom angr script content
            find_address: Address to find during symbolic execution
            avoid_addresses: Comma-separated addresses to avoid
            analysis_type: Type of analysis (symbolic, cfg, static)
            additional_args: Additional arguments

        Returns:
            Symbolic execution and binary analysis results
        """
        data = {
            "binary": binary,
            "script_content": script_content,
            "find_address": find_address,
            "avoid_addresses": avoid_addresses,
            "analysis_type": analysis_type,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting angr analysis: {binary}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/angr", data)
        )
        if result.get("success"):
            logger.info(f"✅ angr analysis completed")
        else:
            logger.error(f"❌ angr analysis failed")
        return result
