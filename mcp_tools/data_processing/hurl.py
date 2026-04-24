# mcp_tools/data_processing/hurl.py

from typing import Dict, Any
import asyncio


def register_hurl_tool(mcp, api_client, logger):
    @mcp.tool()
    async def hurl_request(
        input: str,
        mode: str = "base64_encode",
        suppress: bool = True,
        additional_args: str = "",
    ) -> Dict[str, Any]:
        """
        Execute hURL for string encoding, decoding, and hashing transformations.

        Args:
            input: Input string value to transform
            mode: Transformation mode (default: base64_encode)
            suppress: Return result only by adding -s (default: True)
            additional_args: Additional hURL arguments

        Returns:
            hURL execution results
        """
        data = {
            "input": input,
            "mode": mode,
            "suppress": suppress,
            "additional_args": additional_args,
        }
        logger.info(f"🧪 Starting hURL request (mode={mode}): {input}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/data_processing/hurl", data)
        )
        if result.get("success"):
            logger.info(f"✅ hURL request completed (mode={mode})")
        else:
            logger.error(f"❌ hURL request failed (mode={mode})")
        return result
