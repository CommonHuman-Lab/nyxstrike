# mcp_tools/gadget_search/one_gadget.py

from typing import Dict, Any
import asyncio

def register_one_gadget_tool(mcp, api_client, logger):

    @mcp.tool()
    async def one_gadget_search(libc_path: str, level: int = 1, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute one_gadget to find one-shot RCE gadgets in libc.

        Args:
            libc_path: Path to libc binary
            level: Constraint level (0, 1, 2)
            additional_args: Additional one_gadget arguments

        Returns:
            One-shot RCE gadget search results
        """
        data = {
            "libc_path": libc_path,
            "level": level,
            "additional_args": additional_args
        }
        logger.info(f"🔧 Starting one_gadget analysis: {libc_path}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/one-gadget", data)
        )
        if result.get("success"):
            logger.info(f"✅ one_gadget analysis completed")
        else:
            logger.error(f"❌ one_gadget analysis failed")
        return result