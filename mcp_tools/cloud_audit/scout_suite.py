# mcp_tools/cloud_audit/scout_suite.py

from typing import Dict, Any
import asyncio

def register_scout_suite_tool(mcp, api_client, logger):
    @mcp.tool()
    async def scout_suite_assessment(provider: str = "aws", profile: str = "default",
                              report_dir: str = "/tmp/scout-suite", services: str = "",
                              exceptions: str = "", additional_args: str = "") -> Dict[str, Any]:
        """
        Execute Scout Suite for multi-cloud security assessment.

        Args:
            provider: Cloud provider (aws, azure, gcp, aliyun, oci)
            profile: AWS profile to use
            report_dir: Directory to save reports
            services: Specific services to assess
            exceptions: Exceptions file path
            additional_args: Additional Scout Suite arguments

        Returns:
            Multi-cloud security assessment results
        """
        data = {
            "provider": provider,
            "profile": profile,
            "report_dir": report_dir,
            "services": services,
            "exceptions": exceptions,
            "additional_args": additional_args
        }
        logger.info(f"☁️  Starting Scout Suite {provider} assessment")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/scout-suite", data)
        )
        if result.get("success"):
            logger.info(f"✅ Scout Suite assessment completed")
        else:
            logger.error(f"❌ Scout Suite assessment failed")
        return result
