# mcp_tools/vuln_intel/vulnx.py

from typing import Dict, Any
import asyncio

def register_vulnx_tool(mcp, api_client, logger):

    @mcp.tool()
    async def vulnx(
        cve_id: str = "",
        search: str = "",
        auth_key: str = ""
    ) -> Dict[str, Any]:
        """
        CVE vulnerability intelligence and analysis using vulnx.

        Args:
            cve_id: CVE identifier (optional)
            search: Search string (optional)
            auth_key: API authentication key (optional)
        Notes:
            At least one of cve_id or search must be provided
        Returns:
            Vulnerability intelligence results
        """
        data = {
            "cve_id": cve_id,
            "search": search,
            "auth_key": auth_key
        }
        logger.info(f"🔎 Starting vulnx analysis: cve_id={cve_id}, search={search}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/vuln-intel/vulnx", data)
        )
        if not result.get("error"):
            logger.info("✅ vulnx analysis completed")
        else:
            logger.error(f"❌ vulnx analysis failed: {result.get('error')}")
        return result