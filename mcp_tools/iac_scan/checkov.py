# mcp_tools/iac_scan/checkov.py

from typing import Dict, Any
import asyncio

def register_checkov_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def checkov_iac_scan(directory: str = ".", framework: str = "", check: str = "",
                        skip_check: str = "", output_format: str = "json",
                        additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Checkov for infrastructure as code security scanning.

        Args:
            directory: Directory to scan
            framework: Framework to scan (terraform, cloudformation, kubernetes, etc.)
            check: Specific check to run
            skip_check: Check to skip
            output_format: Output format (json, yaml, cli)
            additional_args: Additional Checkov arguments

        Returns:
            Infrastructure as code security scanning results
        """
        data = {
            "directory": directory,
            "framework": framework,
            "check": check,
            "skip_check": skip_check,
            "output_format": output_format,
            "additional_args": additional_args
        }
        logger.info(f"🔍 Starting Checkov IaC scan: {directory}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/checkov", data)
        )
        if result.get("success"):
            logger.info(f"✅ Checkov scan completed")
        else:
            logger.error(f"❌ Checkov scan failed")
        return result
