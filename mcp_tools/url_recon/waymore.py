# mcp_tools/url_recon/waymore.py

from typing import Dict, Any
import asyncio

def register_waymore_tool(mcp, api_client, logger):
    @mcp.tool()
    async def waymore_discovery(input: str, mode: str = "U",
                                output_urls: str = "", output_responses: str = "",
                                additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Waymore for URL and response discovery from multiple archive sources.

        Args:
            input: Target domain or URL to search
            mode: Discovery mode — U (URLs only), R (responses only), or B (both)
            output_urls: File path to write discovered URLs to (optional)
            output_responses: Directory path to write responses to (optional)
            additional_args: Additional waymore arguments

        Returns:
            Discovered URLs and/or responses from archive sources
        """
        data = {
            "input": input,
            "mode": mode,
            "output_urls": output_urls,
            "output_responses": output_responses,
            "additional_args": additional_args,
        }
        logger.info(f"🕸️  Starting Waymore discovery: {input} (mode={mode})")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/waymore", data)
        )
        if result.get("success"):
            logger.info(f"✅ Waymore discovery completed for {input}")
        else:
            logger.error(f"❌ Waymore discovery failed for {input}")
        return result
