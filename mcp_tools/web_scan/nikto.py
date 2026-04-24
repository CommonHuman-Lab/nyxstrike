# mcp_tools/web_scan/nikto.py

from typing import Dict, Any
import asyncio

def register_nikto_tool(mcp, api_client, logger):
    @mcp.tool()
    async def nikto_scan(target: str, additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Nikto web vulnerability scanner with enhanced logging.

        Args:
            target: The target URL or IP
            additional_args: Additional Nikto arguments

        Returns:
            Scan results with discovered vulnerabilities
        """
        data = {
            "target": target,
            "additional_args": additional_args
        }
        logger.info(f"🔬 Starting Nikto scan: {target}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/nikto", data)
        )
        if result.get("success"):
            logger.info(f"✅ Nikto scan completed for {target}")
        else:
            logger.error(f"❌ Nikto scan failed for {target}")
        return result