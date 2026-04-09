# mcp_tools/cloud_visual/cloudmapper.py

from typing import Dict, Any
import asyncio

def register_cloudmapper_tool(mcp, api_client, logger):
    @mcp.tool()
    async def cloudmapper_analysis(action: str = "collect", account: str = "",
                            config: str = "config.json", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute CloudMapper for AWS network visualization and security analysis.

        Args:
            action: Action to perform (collect, prepare, webserver, find_admins, etc.)
            account: AWS account to analyze
            config: Configuration file path
            additional_args: Additional CloudMapper arguments

        Returns:
            AWS network visualization and security analysis results
        """
        data = {
            "action": action,
            "account": account,
            "config": config,
            "additional_args": additional_args
        }
        logger.info(f"☁️  Starting CloudMapper {action}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/cloudmapper", data)
        )
        if result.get("success"):
            logger.info(f"✅ CloudMapper {action} completed")
        else:
            logger.error(f"❌ CloudMapper {action} failed")
        return result
