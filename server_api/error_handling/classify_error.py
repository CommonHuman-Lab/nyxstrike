"""
Error classification API endpoint.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging

from server_core.singletons import error_handler

logger = logging.getLogger(__name__)

api_error_handling_classify_error_bp = Blueprint("api_error_handling_classify_error", __name__)


@api_error_handling_classify_error_bp.route("/api/error-handling/classify-error", methods=["POST"])
def classify_error_endpoint():
    """Classify an error message"""
    try:
        data = request.get_json()
        error_message = data.get("error_message", "")

        if not error_message:
            return jsonify({"error": "error_message is required"}), 400

        error_type = error_handler.classify_error(error_message)
        recovery_strategies = error_handler.recovery_strategies.get(error_type, [])

        return jsonify({
            "success": True,
            "error_type": error_type.value,
            "recovery_strategies": [
                {
                    "action": strategy.action.value,
                    "parameters": strategy.parameters,
                    "success_probability": strategy.success_probability,
                    "estimated_time": strategy.estimated_time
                }
                for strategy in recovery_strategies
            ],
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error classifying error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
