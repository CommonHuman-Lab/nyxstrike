# mcp_tools/binary_analysis/autopsy.py

from typing import Dict, Any
import asyncio

def register_autopsy_tools(mcp, api_client, logger):
    
    @mcp.tool()
    async def autopsy_analysis() -> Dict[str, Any]:
        """
        Launch the Autopsy digital forensics web server and provide access instructions.

        Returns:
            dict: A dictionary containing connection details or error information for accessing the Autopsy web interface.
        """

        logger.info("🔍 Launching Autopsy web server")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/binary_analysis/autopsy", {})
        )
        if result.get("success"):
            logger.info(f"✅ Autopsy analysis completed")
        else:
            logger.error(f"❌ Autopsy analysis failed")
        return result