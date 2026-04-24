# mcp_tools/gadget_search/ropper.py

from typing import Dict, Any
import asyncio

def register_ropper_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def ropper_gadget_search(binary: str, gadget_type: str = "rop", quality: int = 1,
                            arch: str = "", search_string: str = "",
                            additional_args: str = "") -> Dict[str, Any]:
        """
        Execute ropper for advanced ROP/JOP gadget searching.

        Args:
            binary: Binary to search for gadgets
            gadget_type: Type of gadgets (rop, jop, sys, all)
            quality: Gadget quality level (1-5)
            arch: Target architecture (x86, x86_64, arm, etc.)
            search_string: Specific gadget pattern to search for
            additional_args: Additional ropper arguments

        Returns:
            Advanced ROP/JOP gadget search results
        """
        data = {
            "binary": binary,
            "gadget_type": gadget_type,
            "quality": quality,
            "arch": arch,
            "search_string": search_string,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting ropper analysis: {binary}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/ropper", data)
        )
        if result.get("success"):
            logger.info(f"✅ ropper analysis completed")
        else:
            logger.error(f"❌ ropper analysis failed")
        return result
