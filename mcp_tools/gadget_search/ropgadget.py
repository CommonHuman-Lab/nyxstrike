# mcp_tools/gadget_search/ropgadget.py

from typing import Dict, Any
import asyncio

def register_ropgadget_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def ropgadget_search(binary: str, gadget_type: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Search for ROP gadgets in a binary using ROPgadget with enhanced logging.

        Args:
            binary: Path to the binary file
            gadget_type: Type of gadgets to search for
            additional_args: Additional ROPgadget arguments

        Returns:
            ROP gadget search results
        """
        data = {
            "binary": binary,
            "gadget_type": gadget_type,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting ROPgadget search: {binary}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/ropgadget", data)
        )
        if result.get("success"):
            logger.info(f"✅ ROPgadget search completed for {binary}")
        else:
            logger.error(f"❌ ROPgadget search failed for {binary}")
        return result
