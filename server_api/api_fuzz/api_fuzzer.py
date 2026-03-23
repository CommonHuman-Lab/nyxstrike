from flask import Blueprint, request, jsonify
import logging
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_api_fuzz_api_fuzzer_bp = Blueprint("api_api_fuzz_api_fuzzer", __name__)


# ============================================================================
# ADVANCED API TESTING TOOLS (v5.0 ENHANCEMENT)
# ============================================================================

@api_api_fuzz_api_fuzzer_bp.route("/api/tools/api_fuzzer", methods=["POST"])
def api_fuzzer():
    """Advanced API endpoint fuzzing with intelligent parameter discovery"""
    try:
        params = request.json
        base_url = params.get("base_url", "")
        endpoints = params.get("endpoints", [])
        methods = params.get("methods", ["GET", "POST", "PUT", "DELETE"])
        wordlist = params.get("wordlist", "/usr/share/wordlists/api/api-endpoints.txt")

        if not base_url:
            logger.warning("🌐 API Fuzzer called without base_url parameter")
            return jsonify({
                "error": "Base URL parameter is required"
            }), 400

        # Create comprehensive API fuzzing command
        if endpoints:
            # Test specific endpoints
            results = []
            for endpoint in endpoints:
                for method in methods:
                    test_url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                    command = f"curl -s -X {method} -w '%{{http_code}}|%{{size_download}}' '{test_url}'"
                    result = execute_command(command, use_cache=False)
                    results.append({
                        "endpoint": endpoint,
                        "method": method,
                        "result": result
                    })

            logger.info(f"🔍 API endpoint testing completed for {len(endpoints)} endpoints")
            return jsonify({
                "success": True,
                "fuzzing_type": "endpoint_testing",
                "results": results
            })
        else:
            # Discover endpoints using wordlist
            command = f"ffuf -u {base_url}/FUZZ -w {wordlist} -mc 200,201,202,204,301,302,307,401,403,405 -t 50"

            logger.info(f"🔍 Starting API endpoint discovery: {base_url}")
            result = execute_command(command)
            logger.info(f"📊 API endpoint discovery completed")

            return jsonify({
                "success": True,
                "fuzzing_type": "endpoint_discovery",
                "result": result
            })

    except Exception as e:
        logger.error(f"💥 Error in API fuzzer: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
