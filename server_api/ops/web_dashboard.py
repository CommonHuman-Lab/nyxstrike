import time
import logging
from datetime import datetime
from flask import Blueprint, jsonify, Response, stream_with_context
import server_core.config_core as config_core
from server_core.singletons import cache, telemetry, enhanced_process_manager
import server_api.ops.system_monitoring as _sm
from server_api.ops.system_monitoring import _get_tool_availability, _HEALTH_TOOL_CATEGORIES
import json

logger = logging.getLogger(__name__)

api_web_dashboard_bp = Blueprint("api_web_dashboard", __name__)

@api_web_dashboard_bp.route("/web-dashboard", methods=["GET"])
def web_dashboard():
  """Combined endpoint for the web dashboard UI — merges health and resource usage data."""
  try:
    # ── Tool availability (health) ────────────────────────────────────────
    tools_status = _get_tool_availability()
    essential_tools = _HEALTH_TOOL_CATEGORIES["essential"]
    all_essential_available = all(tools_status.get(t, False) for t in essential_tools)

    category_stats = {
      cat: {
        "total": len(tools),
        "available": sum(1 for t in tools if tools_status.get(t, False)),
      }
      for cat, tools in _HEALTH_TOOL_CATEGORIES.items()
    }

    # ── System resources ──────────────────────────────────────────────────
    current_usage = enhanced_process_manager.resource_monitor.get_current_usage()

    return jsonify({
      # Server identity
      "status": "healthy",
      "version": config_core.get("VERSION", "unknown"),
      "uptime": time.time() - telemetry.stats["start_time"],

      # Telemetry / commands
      "telemetry": telemetry.get_stats(),

      # Tool availability
      "tools_status": tools_status,
      "all_essential_tools_available": all_essential_available,
      "total_tools_available": sum(1 for v in tools_status.values() if v),
      "total_tools_count": len(tools_status),
      "category_stats": category_stats,
      "tool_availability_age_seconds": round(time.time() - _sm._tool_availability_last_refresh, 1) if _sm._tool_availability_last_refresh > 0 else None,

      # System resources
      "resources": current_usage,
      "resources_timestamp": datetime.now().isoformat(),

      # Cache stats
      "cache_stats": cache.get_stats(),
    })

  except Exception as e:
    logger.error(f"Error building web dashboard response: {e}")
    return jsonify({"error": f"Server error: {str(e)}"}), 500

# ── Streaming dashboard SSE endpoint ─────────────
@api_web_dashboard_bp.route("/web-dashboard/stream", methods=["GET"])
def stream_dashboard():
    """SSE endpoint — streams the latest dashboard state every 2 seconds"""
    def generate():
        last_json = None
        while True:
            try:
                tools_status = _get_tool_availability()
                essential_tools = _HEALTH_TOOL_CATEGORIES["essential"]
                all_essential_available = all(tools_status.get(t, False) for t in essential_tools)
                category_stats = {
                    cat: {
                        "total": len(tools),
                        "available": sum(1 for t in tools if tools_status.get(t, False)),
                    }
                    for cat, tools in _HEALTH_TOOL_CATEGORIES.items()
                }
                current_usage = enhanced_process_manager.resource_monitor.get_current_usage()
                dashboard = {
                    "status": "healthy",
                    "version": config_core.get("VERSION", "unknown"),
                    "uptime": time.time() - telemetry.stats["start_time"],
                    "telemetry": telemetry.get_stats(),
                    "tools_status": tools_status,
                    "all_essential_tools_available": all_essential_available,
                    "total_tools_available": sum(1 for v in tools_status.values() if v),
                    "total_tools_count": len(tools_status),
                    "category_stats": category_stats,
                    "tool_availability_age_seconds": round(time.time() - _sm._tool_availability_last_refresh, 1) if _sm._tool_availability_last_refresh > 0 else None,
                    "resources": current_usage,
                    "resources_timestamp": datetime.now().isoformat(),
                    "cache_stats": cache.get_stats(),
                }
                js = json.dumps(dashboard, separators=(",", ":"))
                if js != last_json:
                    yield f"data: {js}\n\n"
                    last_json = js
                else:
                    # Keepalive if nothing new
                    yield ": keepalive\n\n"
            except Exception as e:
                yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
            time.sleep(2)
    return Response(stream_with_context(generate()), mimetype="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

