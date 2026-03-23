"""
Alternative tools lookup API endpoint.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from server_core.singletons import error_handler

logger = logging.getLogger(__name__)

api_error_handling_alternative_tools_bp = Blueprint(
    "api_error_handling_alternative_tools", __name__
)


@api_error_handling_alternative_tools_bp.route(
    "/api/error-handling/alternative-tools", methods=["GET"]
)
def get_alternative_tools():
    """Get alternative tools for a given tool"""
    try:
        tool_name = request.args.get("tool_name", "")

        if not tool_name:
            return jsonify({"error": "tool_name parameter is required"}), 400

        alternatives = error_handler.tool_alternatives.get(tool_name, [])

        return jsonify({
            "success": True,
            "tool_name": tool_name,
            "alternatives": alternatives,
            "has_alternatives": len(alternatives) > 0,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting alternative tools: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
