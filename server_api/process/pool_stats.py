from flask import Blueprint, jsonify, Response, stream_with_context
import json
import time
import logging
from datetime import datetime

from server_core.singletons import enhanced_process_manager

logger = logging.getLogger(__name__)

api_process_pool_stats_bp = Blueprint("api_process_pool_stats", __name__)


@api_process_pool_stats_bp.route("/api/process/pool-stats", methods=["GET"])
def get_process_pool_stats():
    """Get process pool statistics and performance metrics"""
    try:
        stats = enhanced_process_manager.get_comprehensive_stats()
        logger.info(f"📊 Process pool stats retrieved | Active workers: {stats['process_pool']['active_workers']}")
        return jsonify({
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"💥 Error getting pool stats: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# --- STREAMING ENDPOINTS ---
@api_process_pool_stats_bp.route("/api/process/pool-stats/stream", methods=["GET"])
def stream_process_pool_stats():
    """
    SSE endpoint — streams process pool stats every 2 seconds.
    """
    def generate():
        last_json = None
        while True:
            try:
                stats = enhanced_process_manager.get_comprehensive_stats()
                data = {
                    "success": True,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                }
                js = json.dumps(data, separators=(",", ":"))
                if js != last_json:
                    yield f"data: {js}\n\n"
                    last_json = js
                else:
                    yield ": keepalive\n\n"
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            time.sleep(2)
    return Response(stream_with_context(generate()), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})