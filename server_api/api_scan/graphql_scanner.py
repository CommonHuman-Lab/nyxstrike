from flask import Blueprint, request, jsonify
import json
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_api_scan_graphql_scanner_bp = Blueprint("api_api_scan_graphql_scanner", __name__)


@api_api_scan_graphql_scanner_bp.route("/api/tools/graphql_scanner", methods=["POST"])
def graphql_scanner():
    """Advanced GraphQL security scanning and introspection"""
    try:
        params = request.json
        endpoint = params.get("endpoint", "")
        introspection = params.get("introspection", True)
        query_depth = params.get("query_depth", 10)
        mutations = params.get("test_mutations", True)

        if not endpoint:
            logger.warning("🌐 GraphQL Scanner called without endpoint parameter")
            return jsonify({
                "error": "GraphQL endpoint parameter is required"
            }), 400

        logger.info(f"🔍 Starting GraphQL security scan: {endpoint}")

        results = {
            "endpoint": endpoint,
            "tests_performed": [],
            "vulnerabilities": [],
            "recommendations": []
        }

        # Test 1: Introspection query
        if introspection:
            introspection_query = '''
            {
                __schema {
                    types {
                        name
                        fields {
                            name
                            type {
                                name
                            }
                        }
                    }
                }
            }
            '''

            clean_query = introspection_query.replace('\n', ' ').replace('  ', ' ').strip()
            command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{{\"query\":\"{clean_query}\"}}' '{endpoint}'"
            result = execute_command(command, use_cache=False)

            results["tests_performed"].append("introspection_query")

            if "data" in result.get("stdout", ""):
                results["vulnerabilities"].append({
                    "type": "introspection_enabled",
                    "severity": "MEDIUM",
                    "description": "GraphQL introspection is enabled"
                })

        # Test 2: Query depth analysis
        deep_query = "{ " * query_depth + "field" + " }" * query_depth
        command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{{\"query\":\"{deep_query}\"}}' {endpoint}"
        depth_result = execute_command(command, use_cache=False)

        results["tests_performed"].append("query_depth_analysis")

        if "error" not in depth_result.get("stdout", "").lower():
            results["vulnerabilities"].append({
                "type": "no_query_depth_limit",
                "severity": "HIGH",
                "description": f"No query depth limiting detected (tested depth: {query_depth})"
            })

        # Test 3: Batch query testing
        batch_query = '[' + ','.join(['{\"query\":\"{field}\"}' for _ in range(10)]) + ']'
        command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{batch_query}' {endpoint}"
        batch_result = execute_command(command, use_cache=False)

        results["tests_performed"].append("batch_query_testing")

        if "data" in batch_result.get("stdout", "") and batch_result.get("success"):
            results["vulnerabilities"].append({
                "type": "batch_queries_allowed",
                "severity": "MEDIUM",
                "description": "Batch queries are allowed without rate limiting"
            })

        # Generate recommendations
        if results["vulnerabilities"]:
            results["recommendations"] = [
                "Disable introspection in production",
                "Implement query depth limiting",
                "Add rate limiting for batch queries",
                "Implement query complexity analysis",
                "Add authentication for sensitive operations"
            ]

        logger.info(f"📊 GraphQL scan completed | Vulnerabilities found: {len(results['vulnerabilities'])}")

        return jsonify({
            "success": True,
            "graphql_scan_results": results
        })

    except Exception as e:
        logger.error(f"💥 Error in GraphQL scanner: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
