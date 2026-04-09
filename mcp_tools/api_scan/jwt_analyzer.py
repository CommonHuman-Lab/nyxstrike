# mcp_tools/api_scan/jwt_analyzer.py

from typing import Dict, Any
import asyncio

def register_jwt_analyzer_tool(mcp, api_client, logger):

    @mcp.tool()
    async def jwt_analyzer(jwt_token: str, target_url: str = "") -> Dict[str, Any]:
        """
        Advanced JWT token analysis and vulnerability testing.

        Args:
            jwt_token: JWT token to analyze
            target_url: Optional target URL for testing token manipulation

        Returns:
            JWT analysis results with vulnerability assessment and attack vectors
        """
        data = {
            "jwt_token": jwt_token,
            "target_url": target_url
        }

        logger.info(f"🔍 Starting JWT security analysis")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/jwt_analyzer", data)
        )

        if result.get("success"):
            analysis = result.get("jwt_analysis_results", {})
            vuln_count = len(analysis.get("vulnerabilities", []))
            algorithm = analysis.get("token_info", {}).get("algorithm", "unknown")

            logger.info(f"✅ JWT analysis completed: {vuln_count} vulnerabilities found")
            logger.info(f"🔐 Token algorithm: {algorithm}")

            if vuln_count > 0:
                logger.warning(f"⚠️  Found {vuln_count} JWT vulnerabilities!")
                for vuln in analysis.get("vulnerabilities", [])[:3]:  # Show first 3
                    severity = vuln.get("severity", "UNKNOWN")
                    vuln_type = vuln.get("type", "unknown")
                    logger.warning(f"   ├─ [{severity}] {vuln_type}")
        else:
            logger.error("❌ JWT analysis failed")

        return result
