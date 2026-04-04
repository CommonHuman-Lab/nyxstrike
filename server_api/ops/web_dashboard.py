import time
import logging
import re
import threading
from datetime import datetime, timezone
from flask import Blueprint, jsonify, Response, stream_with_context
import server_core.config_core as config_core
from server_core.singletons import cache, telemetry, enhanced_process_manager
import server_api.ops.system_monitoring as _sm
from server_api.ops.system_monitoring import _get_tool_availability
from server_core.tool_constants import HEALTH_TOOL_CATEGORIES
import json
from urllib.request import urlopen

logger = logging.getLogger(__name__)

api_web_dashboard_bp = Blueprint("api_web_dashboard", __name__)

REMOTE_MASTER_CONFIG_URL = "https://raw.githubusercontent.com/CommonHuman-Lab/hexstrike-ai-community-edition/master/config.py"
_update_cache_lock = threading.Lock()
_update_cache = {
    "for_version": None,
    "result": None,
}
_startup_update_check_done = False


def _extract_numeric_version(value: str):
    if not value:
        return ()
    match = re.search(r"\d+(?:\.\d+)+", value)
    if not match:
        return ()
    return tuple(int(part) for part in match.group(0).split("."))


def _is_remote_newer(local_version: str, remote_version: str) -> bool:
    local_parts = _extract_numeric_version(local_version)
    remote_parts = _extract_numeric_version(remote_version)
    if not local_parts or not remote_parts:
        return False

    width = max(len(local_parts), len(remote_parts))
    local_parts = local_parts + (0,) * (width - len(local_parts))
    remote_parts = remote_parts + (0,) * (width - len(remote_parts))
    return remote_parts > local_parts


def _parse_remote_config_version(config_text: str):
    match = re.search(r'["\']VERSION["\']\s*:\s*["\']([^"\']+)["\']', config_text)
    return match.group(1).strip() if match else None


def _fetch_master_version():
    with urlopen(REMOTE_MASTER_CONFIG_URL, timeout=4) as response:
        config_text = response.read().decode("utf-8", errors="replace")
    return _parse_remote_config_version(config_text)


def _run_update_check(local_version: str):
    result = {
        "current_version": local_version,
        "latest_version": local_version,
        "update_available": False,
        "checked_at": datetime.now(timezone.utc).isoformat() + "Z",
        "source": "github-master-startup",
        "error": None,
    }

    try:
        latest = _fetch_master_version()
        if latest:
            result["latest_version"] = latest
            result["update_available"] = _is_remote_newer(local_version, latest)
        else:
            result["error"] = "Could not parse remote version"
    except Exception as e:
        result["error"] = str(e)
        logger.debug("Version check failed: %s", e)

    with _update_cache_lock:
        _update_cache["for_version"] = local_version
        _update_cache["result"] = result

    return result


def _get_update_status(local_version: str):
    with _update_cache_lock:
        cached_result = _update_cache.get("result")
        cached_for_version = _update_cache.get("for_version")
        if cached_result is not None and cached_for_version == local_version:
            return cached_result

    return {
        "current_version": local_version,
        "latest_version": local_version,
        "update_available": False,
        "checked_at": None,
        "source": "startup-not-run",
        "error": "Version check has not run yet",
    }


def initialize_update_status_check():
    global _startup_update_check_done
    with _update_cache_lock:
        if _startup_update_check_done:
            return
        _startup_update_check_done = True

    local_version = config_core.get("VERSION", "unknown")
    status = _run_update_check(local_version)
    if status.get("error"):
        logger.warning("Version update check failed at startup: %s", status.get("error"))
        return

    if status.get("update_available"):
        logger.info(
            "Update available: local=%s latest=%s",
            status.get("current_version"),
            status.get("latest_version"),
        )
    else:
        logger.info("Version check complete: up to date (%s)", status.get("current_version"))

def build_dashboard_data():
  tools_status = _get_tool_availability()
  essential_tools = HEALTH_TOOL_CATEGORIES["essential"]
  all_essential_available = all(tools_status.get(t, False) for t in essential_tools)
  category_stats = {
    cat: {
      "total": len(tools),
      "available": sum(1 for t in tools if tools_status.get(t, False)),
    }
    for cat, tools in HEALTH_TOOL_CATEGORIES.items()
  }
  current_usage = enhanced_process_manager.resource_monitor.get_current_usage()
  version = config_core.get("VERSION", "unknown")
  return {
      # Server identity
      "status": "healthy",
      "version": version,
      "update": _get_update_status(version),
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
      "resources_timestamp": datetime.now(timezone.utc).isoformat() + "Z",

      # Cache stats
      "cache_stats": cache.get_stats(),
  }

@api_web_dashboard_bp.route("/web-dashboard", methods=["GET"])
def web_dashboard():
  """Combined endpoint for the web dashboard UI — merges health and resource usage data."""
  try:
    return jsonify(build_dashboard_data())
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
                dashboard = build_dashboard_data()
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
