# mcp_tools/api_audit/comprehensive_api_audit.py

from typing import Dict, Any
import time
import asyncio

def register_comprehensive_api_audit_tool(mcp, api_client, logger):
    
    @mcp.tool()
    async def comprehensive_api_audit(base_url: str, schema_url: str = "", jwt_token: str = "", graphql_endpoint: str = "") -> Dict[str, Any]:
        """
        Comprehensive API security audit combining multiple testing techniques.

        Args:
            base_url: Base URL of the API
            schema_url: Optional API schema URL
            jwt_token: Optional JWT token for analysis
            graphql_endpoint: Optional GraphQL endpoint

        Returns:
            Comprehensive audit results with all API security tests
        """

        audit_results = {
            "base_url": base_url,
            "audit_timestamp": time.time(),
            "tests_performed": [],
            "total_vulnerabilities": 0,
            "summary": {},
            "recommendations": []
        }

        logger.info(f"🚀 Starting comprehensive API security audit: {base_url}")

        # 1. API Endpoint Fuzzing
        if hasattr(mcp, "has_tool") and not mcp.has_tool("api_fuzzer"):
            logger.warning("api_fuzzer tool is not registered or available.")
        else:
            logger.info("🔍 Phase 1: API endpoint discovery and fuzzing")
            fuzz_result = mcp.run_tool("api_fuzzer", {"base_url": base_url})
            if fuzz_result.get("success"):
                audit_results["tests_performed"].append("api_fuzzing")
                audit_results["api_fuzzing"] = fuzz_result

        # 2. Schema Analysis (if provided)
        if schema_url:
            if hasattr(mcp, "has_tool") and not mcp.has_tool("api_schema_analyzer"):
                logger.warning("api_schema_analyzer tool is not registered or available.")
            else:
                logger.info("🔍 Phase 2: API schema analysis")
                schema_result = mcp.run_tool("api_schema_analyzer", {"schema_url": schema_url})
                if schema_result.get("success"):
                    audit_results["tests_performed"].append("schema_analysis")
                    audit_results["schema_analysis"] = schema_result

                    schema_data = schema_result.get("schema_analysis_results", {})
                    audit_results["total_vulnerabilities"] += len(schema_data.get("security_issues", []))

        # 3. JWT Analysis (if provided)
        if jwt_token:
            if hasattr(mcp, "has_tool") and not mcp.has_tool("jwt_analyzer"):
                logger.warning("jwt_analyzer tool is not registered or available.")
            else:
                logger.info("🔍 Phase 3: JWT token analysis")
                jwt_result = mcp.run_tool("jwt_analyzer", {"jwt_token": jwt_token, "target_url": base_url})
                if jwt_result.get("success"):
                    audit_results["tests_performed"].append("jwt_analysis")
                    audit_results["jwt_analysis"] = jwt_result

                    jwt_data = jwt_result.get("jwt_analysis_results", {})
                    audit_results["total_vulnerabilities"] += len(jwt_data.get("vulnerabilities", []))

        # 4. GraphQL Testing (if provided)
        if graphql_endpoint:
            if hasattr(mcp, "has_tool") and not mcp.has_tool("graphql_scanner"):
                logger.warning("graphql_scanner tool is not registered or available.")
            else:
                logger.info("🔍 Phase 4: GraphQL security scanning")
                graphql_result = mcp.run_tool("graphql_scanner", {"endpoint": graphql_endpoint})
                if graphql_result.get("success"):
                    audit_results["tests_performed"].append("graphql_scanning")
                    audit_results["graphql_scanning"] = graphql_result

                    graphql_data = graphql_result.get("graphql_scan_results", {})
                    audit_results["total_vulnerabilities"] += len(graphql_data.get("vulnerabilities", []))

        # Generate comprehensive recommendations
        audit_results["recommendations"] = [
            "Implement proper authentication and authorization",
            "Use HTTPS for all API communications",
            "Validate and sanitize all input parameters",
            "Implement rate limiting and request throttling",
            "Add comprehensive logging and monitoring",
            "Regular security testing and code reviews",
            "Keep API documentation updated and secure",
            "Implement proper error handling"
        ]

        # Summary
        audit_results["summary"] = {
            "tests_performed": len(audit_results["tests_performed"]),
            "total_vulnerabilities": audit_results["total_vulnerabilities"],
            "audit_coverage": "comprehensive" if len(audit_results["tests_performed"]) >= 3 else "partial"
        }

        logger.info(f"✅ Comprehensive API audit completed:")
        logger.info(f"   ├─ Tests performed: {audit_results['summary']['tests_performed']}")
        logger.info(f"   ├─ Total vulnerabilities: {audit_results['summary']['total_vulnerabilities']}")
        logger.info(f"   └─ Coverage: {audit_results['summary']['audit_coverage']}")

        return {
            "success": True,
            "comprehensive_audit": audit_results
        }
