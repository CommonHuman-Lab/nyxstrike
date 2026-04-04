from flask import Blueprint, request, jsonify
import logging
from datetime import datetime

from server_core.singletons import enhanced_process_manager, cache

logger = logging.getLogger(__name__)

api_process_clear_cache_bp = Blueprint("api_process_clear_cache", __name__)


@api_process_clear_cache_bp.route("/api/process/clear-cache", methods=["POST"])
def clear_process_cache():
    """Clear the advanced cache"""
    try:
        # Clear both process-level cache and global tool cache
        enhanced_process_manager.cache.clear()
        cache.clear()

        logger.info("🧹 Process cache cleared")
        return jsonify({
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error clearing cache: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
