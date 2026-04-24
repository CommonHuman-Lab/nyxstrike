# mcp_tools/web_fuzz/dotdotpwn.py

from typing import Dict, Any
import asyncio

def register_dotdotpwn_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def dotdotpwn_scan(target: str, module: str = "http", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute DotDotPwn for directory traversal testing with enhanced logging.

        Args:
            target: The target hostname or IP
            module: Module to use (http, ftp, tftp, etc.)
            additional_args: Additional DotDotPwn arguments

        Returns:
            Directory traversal test results
        """
        data = {
            "target": target,
            "module": module,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting DotDotPwn scan: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/dotdotpwn", data)
        )
        if result.get("success"):
            logger.info(f"✅ DotDotPwn scan completed for {target}")
        else:
            logger.error(f"❌ DotDotPwn scan failed for {target}")
        return result
