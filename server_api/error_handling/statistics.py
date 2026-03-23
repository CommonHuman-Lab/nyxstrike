"""
Error handling statistics API endpoint.
"""

from flask import Blueprint, jsonify
from datetime import datetime
import logging

from server_core.singletons import error_handler

logger = logging.getLogger(__name__)

api_error_handling_statistics_bp = Blueprint("api_error_handling_statistics", __name__)


@api_error_handling_statistics_bp.route("/api/error-handling/statistics", methods=["GET"])
def get_error_statistics():
    """Get error handling statistics"""
    try:
        stats = error_handler.get_error_statistics()
        return jsonify({
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting error statistics: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
