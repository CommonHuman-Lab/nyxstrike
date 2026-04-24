# mcp_tools/api_scan/graphql_scanner.py

from typing import Dict, Any
import asyncio

def register_graphql_scanner_tool(mcp, api_client, logger):

    @mcp.tool()
    async def graphql_scanner(endpoint: str, introspection: bool = True, query_depth: int = 10, test_mutations: bool = True) -> Dict[str, Any]:
        """
        Advanced GraphQL security scanning and introspection.

        Args:
            endpoint: GraphQL endpoint URL
            introspection: Test introspection queries
            query_depth: Maximum query depth to test
            test_mutations: Test mutation operations

        Returns:
            GraphQL security scan results with vulnerability assessment
        """
        data = {
            "endpoint": endpoint,
            "introspection": introspection,
            "query_depth": query_depth,
            "test_mutations": test_mutations
        }

        logger.info(f"🔍 Starting GraphQL security scan: {endpoint}")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/graphql_scanner", data)
        )

        if result.get("success"):
            scan_results = result.get("graphql_scan_results", {})
            vuln_count = len(scan_results.get("vulnerabilities", []))
            tests_count = len(scan_results.get("tests_performed", []))

            logger.info(f"✅ GraphQL scan completed: {tests_count} tests, {vuln_count} vulnerabilities")

            if vuln_count > 0:
                logger.warning(f"⚠️  Found {vuln_count} GraphQL vulnerabilities!")
                for vuln in scan_results.get("vulnerabilities", [])[:3]:  # Show first 3
                    severity = vuln.get("severity", "UNKNOWN")
                    vuln_type = vuln.get("type", "unknown")
                    logger.warning(f"   ├─ [{severity}] {vuln_type}")
        else:
            logger.error("❌ GraphQL scanning failed")

        return result
