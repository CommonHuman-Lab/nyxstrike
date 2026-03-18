from flask import Blueprint, request, jsonify
import json
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_api_scan_api_schema_analyzer_bp = Blueprint("api_api_scan_api_schema_analyzer", __name__)


@api_api_scan_api_schema_analyzer_bp.route("/api/tools/api_schema_analyzer", methods=["POST"])
def api_schema_analyzer():
    """Analyze API schemas and identify potential security issues"""
    try:
        params = request.json
        schema_url = params.get("schema_url", "")
        schema_type = params.get("schema_type", "openapi")  # openapi, swagger, graphql

        if not schema_url:
            logger.warning("📋 API Schema Analyzer called without schema_url parameter")
            return jsonify({
                "error": "Schema URL parameter is required"
            }), 400

        logger.info(f"🔍 Starting API schema analysis: {schema_url}")

        # Fetch schema
        command = f"curl -s '{schema_url}'"
        result = execute_command(command, use_cache=True)

        if not result.get("success"):
            return jsonify({
                "error": "Failed to fetch API schema"
            }), 400

        schema_content = result.get("stdout", "")

        analysis_results = {
            "schema_url": schema_url,
            "schema_type": schema_type,
            "endpoints_found": [],
            "security_issues": [],
            "recommendations": []
        }

        # Parse schema based on type
        try:
            schema_data = json.loads(schema_content)
            if schema_type.lower() in ["openapi", "swagger"]:
                # OpenAPI/Swagger analysis
                paths = schema_data.get("paths", {})

                for path, methods in paths.items():
                    for method, details in methods.items():
                        if isinstance(details, dict):
                            endpoint_info = {
                                "path": path,
                                "method": method.upper(),
                                "summary": details.get("summary", ""),
                                "parameters": details.get("parameters", []),
                                "security": details.get("security", [])
                            }
                            analysis_results["endpoints_found"].append(endpoint_info)

                            # Check for security issues
                            if not endpoint_info["security"]:
                                analysis_results["security_issues"].append({
                                    "endpoint": f"{method.upper()} {path}",
                                    "issue": "no_authentication",
                                    "severity": "MEDIUM",
                                    "description": "Endpoint has no authentication requirements"
                                })

                            # Check for sensitive data in parameters
                            for param in endpoint_info["parameters"]:
                                param_name = param.get("name", "").lower()
                                if any(sensitive in param_name for sensitive in ["password", "token", "key", "secret"]):
                                    analysis_results["security_issues"].append({
                                        "endpoint": f"{method.upper()} {path}",
                                        "issue": "sensitive_parameter",
                                        "severity": "HIGH",
                                        "description": f"Sensitive parameter detected: {param_name}"
                                    })

            # Generate recommendations
            if analysis_results["security_issues"]:
                analysis_results["recommendations"] = [
                    "Implement authentication for all endpoints",
                    "Use HTTPS for all API communications",
                    "Validate and sanitize all input parameters",
                    "Implement rate limiting",
                    "Add proper error handling",
                    "Use secure headers (CORS, CSP, etc.)"
                ]

        except json.JSONDecodeError:
            analysis_results["security_issues"].append({
                "endpoint": "schema",
                "issue": "invalid_json",
                "severity": "HIGH",
                "description": "Schema is not valid JSON"
            })

        logger.info(f"📊 Schema analysis completed | Issues found: {len(analysis_results['security_issues'])}")

        return jsonify({
            "success": True,
            "schema_analysis_results": analysis_results
        })

    except Exception as e:
        logger.error(f"💥 Error in API schema analyzer: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
