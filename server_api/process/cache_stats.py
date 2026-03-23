from flask import Blueprint, jsonify
import logging
from datetime import datetime

from server_core.singletons import enhanced_process_manager

logger = logging.getLogger(__name__)

api_process_cache_stats_bp = Blueprint("api_process_cache_stats", __name__)


@api_process_cache_stats_bp.route("/api/process/cache-stats", methods=["GET"])
def get_cache_stats():
    """Get advanced cache statistics"""
    try:
        cache_stats = enhanced_process_manager.cache.get_stats()

        logger.info(f"💾 Cache stats retrieved | Hit rate: {cache_stats['hit_rate']:.1f}%")
        return jsonify({
            "success": True,
            "cache_stats": cache_stats,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error getting cache stats: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
