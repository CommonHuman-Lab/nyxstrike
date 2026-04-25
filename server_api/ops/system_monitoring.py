from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, Optional
import logging
import subprocess
import sys
import threading
import time
import traceback

import server_core.config_core as config_core
from server_core.command_executor import execute_command
from server_core.modern_visual_engine import ModernVisualEngine
from server_core.singletons import cache, telemetry

from server_core.tool_constants import (
    BUILT_IN_TOOLS, REQUIRE_DPKG_CHECK, REQUIRE_PIP_CHECK,
    REQUIRE_GEM_CHECK, REQUIRE_CARGO_CHECK, BINARY_NAME_OVERRIDES,
    HEALTH_TOOL_CATEGORIES
)

logger = logging.getLogger(__name__)

api_system_monitoring_bp = Blueprint("api_system_monitoring", __name__)

# ============================================================================
# TOOL AVAILABILITY CACHE — populated once at startup, refreshed every hour
# ============================================================================
_tool_availability_cache: Dict[str, bool] = {}
_tool_availability_lock = threading.Lock()
_tool_availability_last_refresh: float = 0.0
_tool_availability_refresh_in_progress = False

# Plugin tools registered at runtime.
# Maps mcp_tool_name -> { type, binary, install } from plugin.yaml check block.
# _get_tool_availability() probes each entry and overlays the result.
_plugin_tools: Dict[str, Dict[str, Any]] = {}


def register_plugin_tool(tool_name: str, check: Optional[Dict[str, Any]] = None, category: str = "plugins") -> None:
    """Register a plugin tool with its check metadata.

    check keys (all optional):
      type    — one of: builtin, which, dpkg, pip, gem, cargo  (default: builtin)
      binary  — executable/package name to probe (default: tool_name)
      install — human-readable install hint shown when the tool is missing

    category — maps to a HEALTH_TOOL_CATEGORIES key so the tool appears in the
               dashboard category row.  Defaults to 'plugins' (auto-created).
    """
    _plugin_tools[tool_name] = check or {}

    # Inject into HEALTH_TOOL_CATEGORIES so the dashboard category row includes
    # this tool in its count and availability bar.
    if tool_name not in HEALTH_TOOL_CATEGORIES.get(category, []):
        HEALTH_TOOL_CATEGORIES.setdefault(category, []).append(tool_name)


# Precompute the flat list of all static tools at module load
ALL_TOOLS_FLAT = list({
    tool
    for tools in HEALTH_TOOL_CATEGORIES.values()
    for tool in tools
})


def _probe_binary(check_type: str, binary: str) -> bool:
    """Low-level probe — returns True if the tool/package is present.

    check_type — one of: builtin, which, dpkg, pip, gem, cargo
    binary     — executable or package name to probe
    """
    if check_type == "builtin":
        return True
    try:
        if check_type == "dpkg":
            r = subprocess.run(
                ["dpkg", "-s", binary],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return r.returncode == 0
        elif check_type == "pip":
            r = subprocess.run(
                [sys.executable, "-m", "pip", "list"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            )
            return binary in r.stdout
        elif check_type == "gem":
            r = subprocess.run(
                ["gem", "list"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            )
            return binary in r.stdout
        elif check_type == "cargo":
            r = subprocess.run(
                ["cargo", "install", "--list"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            )
            return binary in r.stdout
        else:  # which (default)
            r = subprocess.run(
                ["which", binary],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return r.returncode == 0
    except Exception:
        return False


def _refresh_tool_availability() -> None:
    """Probe all static tools in parallel and update the module-level cache."""
    global _tool_availability_last_refresh, _tool_availability_refresh_in_progress

    with _tool_availability_lock:
        if _tool_availability_refresh_in_progress:
            return
        _tool_availability_refresh_in_progress = True

    try:
        def probe(tool: str) -> tuple:
            binary = BINARY_NAME_OVERRIDES.get(tool, tool)
            if binary in BUILT_IN_TOOLS:
                return tool, True
            if binary in REQUIRE_DPKG_CHECK:
                check_type = "dpkg"
            elif binary in REQUIRE_PIP_CHECK:
                check_type = "pip"
            elif binary in REQUIRE_GEM_CHECK:
                check_type = "gem"
            elif binary in REQUIRE_CARGO_CHECK:
                check_type = "cargo"
            else:
                check_type = "which"
            return tool, _probe_binary(check_type, binary)

        with ThreadPoolExecutor(max_workers=20) as pool:
            results = dict(pool.map(probe, ALL_TOOLS_FLAT))

        with _tool_availability_lock:
            _tool_availability_cache.update(results)
            _tool_availability_last_refresh = time.time()

        missing = sorted(t for t, ok in results.items() if not ok)
        RED = ModernVisualEngine.COLORS['HACKER_RED']
        RESET = ModernVisualEngine.COLORS['RESET']
        lines = ["Tool availability refreshed: %d/%d available" % (
            sum(ok for ok in results.values()), len(results))]
        for tool in missing:
            lines.append("%s  %-30s NOT INSTALLED%s" % (RED, tool, RESET))
        logger.info("\n".join(lines))
    finally:
        with _tool_availability_lock:
            _tool_availability_refresh_in_progress = False


def _get_tool_availability() -> Dict[str, bool]:
    """Return cached tool availability, refreshing in a background thread if stale."""
    now = time.time()
    with _tool_availability_lock:
        stale = (now - _tool_availability_last_refresh) > config_core.get("TOOL_AVAILABILITY_TTL", 3600)
        empty = not _tool_availability_cache

    if empty:
        _refresh_tool_availability()
    elif stale:
        threading.Thread(target=_refresh_tool_availability, daemon=True).start()

    with _tool_availability_lock:
        output_status = dict(_tool_availability_cache)

    for tool in BUILT_IN_TOOLS:
        output_status[tool] = True

    # Plugin tools: resolve check_type + binary from plugin.yaml check block,
    # then reuse _probe_binary — same code path as static tools.
    for tool_name, check in _plugin_tools.items():
        check_type = str(check.get("type", "builtin")).lower()
        binary = str(check.get("binary", tool_name))
        output_status[tool_name] = _probe_binary(check_type, binary)

    return output_status


def _get_plugin_install_hints() -> Dict[str, str]:
    """Return a dict of tool_name -> install hint for plugins that declare one."""
    return {
        name: check["install"]
        for name, check in _plugin_tools.items()
        if check.get("install")
    }

@api_system_monitoring_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with comprehensive tool detection"""
    tools_status = _get_tool_availability()

    essential_tools = HEALTH_TOOL_CATEGORIES["essential"]
    all_essential_tools_available = all(tools_status.get(t, False) for t in essential_tools)

    category_stats = {
        cat: {
            "total": len(tools),
            "available": sum(1 for t in tools if tools_status.get(t, False)),
        }
        for cat, tools in HEALTH_TOOL_CATEGORIES.items()
    }

    all_tools_count = len(tools_status)

    return jsonify({
        "status": "healthy",
        "message": "NyxStrike Tools API Server is operational",
        "version": config_core.get("VERSION", "unknown"),
        "tools_status": tools_status,
        "all_essential_tools_available": all_essential_tools_available,
        "total_tools_available": sum(1 for available in tools_status.values() if available),
        "total_tools_count": all_tools_count,
        "category_stats": category_stats,
        "plugin_install_hints": _get_plugin_install_hints(),
        "cache_stats": cache.get_stats(),
        "telemetry": telemetry.get_stats(),
        "uptime": time.time() - telemetry.stats["start_time"],
        "tool_availability_age_seconds": round(time.time() - _tool_availability_last_refresh, 1),
    })


@api_system_monitoring_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "success": True,
        "message": "Pong! NyxStrike Tools API Server is responsive",
        "timestamp": datetime.now().isoformat()
    })


@api_system_monitoring_bp.route("/api/command", methods=["POST"])
def generic_command():
    """Execute any command provided in the request with enhanced logging"""
    try:
        params = request.json
        command = params.get("command", "")
        use_cache = params.get("use_cache", True)
        timeout = params.get("timeout")

        if not command:
            logger.warning("Command endpoint called without command parameter")
            return jsonify({
                "error": "Command parameter is required"
            }), 400

        result = execute_command(command, use_cache=use_cache, timeout=timeout)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in command endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500


@api_system_monitoring_bp.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """Get cache statistics"""
    return jsonify(cache.get_stats())


@api_system_monitoring_bp.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """Clear the cache"""
    cache.clear()
    logger.info("Cache cleared")
    return jsonify({"success": True, "message": "Cache cleared"})


@api_system_monitoring_bp.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    """Get system telemetry"""
    return jsonify(telemetry.get_stats())

@api_system_monitoring_bp.route("/api/tools/categories", methods=["GET"])
def get_tool_categories():
    """Get the list of tool categories and their tools"""
    return jsonify({
        "categories": HEALTH_TOOL_CATEGORIES
    })


@api_system_monitoring_bp.route("/api/tools/availability/refresh", methods=["POST"])
def refresh_tool_availability_now():
    """Force immediate tool availability refresh and return current status."""
    try:
        _refresh_tool_availability()
        with _tool_availability_lock:
            tools_status = dict(_tool_availability_cache)
            last_refresh = _tool_availability_last_refresh

        for tool in BUILT_IN_TOOLS:
            tools_status[tool] = True

        return jsonify({
            "success": True,
            "message": "Tool availability refreshed",
            "total_tools_available": sum(1 for available in tools_status.values() if available),
            "total_tools_count": len(tools_status),
            "tool_availability_age_seconds": round(time.time() - last_refresh, 1) if last_refresh > 0 else 0,
            "tools_status": tools_status,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error("Error refreshing tool availability: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@api_system_monitoring_bp.route("/api/server/restart", methods=["POST"])
def server_restart():
  """Restart the NyxStrike server process.

  Strategy:
  1. Duplicate stdout/stderr to new fds with FD_CLOEXEC cleared so they
     survive execve but are separate from the parent's socket fds.
  2. Spawn a detached watcher passing only those two fds (close_fds=True
     closes everything else — including the inherited listening socket).
  3. Watcher polls until the parent is gone AND the port is free.
  4. Watcher os.execve → becomes the new server with output on the terminal.
  5. Parent sends itself SIGTERM to release the port.
  """
  import os
  import signal

  logger.info("server_restart: restart requested via API")

  parent_pid = os.getpid()
  python     = sys.executable
  cmd        = [python] + sys.argv[:]
  env        = dict(os.environ)
  port       = int(env.get("NYXSTRIKE_PORT", 8888))

  # Duplicate stdout/stderr to fresh fds so we can pass them explicitly
  # while closing everything else (especially the listening socket).
  try:
    raw_stdout = sys.stdout.fileno()
    new_stdout = os.dup(raw_stdout)
    os.set_inheritable(new_stdout, True)
  except Exception:
    new_stdout = -1

  try:
    raw_stderr = sys.stderr.fileno()
    new_stderr = os.dup(raw_stderr)
    os.set_inheritable(new_stderr, True)
  except Exception:
    new_stderr = -1

  pass_fds = tuple(fd for fd in (new_stdout, new_stderr) if fd >= 0)

  wait_and_exec = (
    "import os, time, socket\n"
    f"ppid       = {parent_pid}\n"
    f"cmd        = {cmd!r}\n"
    f"env        = {env!r}\n"
    f"port       = {port}\n"
    f"new_stdout = {new_stdout}\n"
    f"new_stderr = {new_stderr}\n"
    # Step 1 — wait for parent process to exit
    "for _ in range(80):\n"
    "    try:\n"
    "        os.kill(ppid, 0)\n"
    "        time.sleep(0.25)\n"
    "    except OSError:\n"
    "        break\n"
    # Step 2 — wait for the port to be free (up to 15 s)
    "for _ in range(60):\n"
    "    try:\n"
    "        s = socket.socket()\n"
    "        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)\n"
    "        s.bind(('127.0.0.1', port))\n"
    "        s.close()\n"
    "        break\n"
    "    except OSError:\n"
    "        time.sleep(0.25)\n"
    # Step 3 — point fd 1/2 at the terminal then exec
    "if new_stdout >= 0: os.dup2(new_stdout, 1)\n"
    "if new_stderr >= 0: os.dup2(new_stderr, 2)\n"
    "os.execve(cmd[0], cmd, env)\n"
  )

  def _spawn_watcher():
    try:
      subprocess.Popen(
        [python, "-c", wait_and_exec],
        close_fds=True,          # closes inherited listening socket — this is the fix
        pass_fds=pass_fds,       # but keeps our duplicated terminal fds
        start_new_session=True,
        stdin=subprocess.DEVNULL,
      )
    except Exception as exc:
      logger.error("server_restart: failed to spawn watcher: %s", exc)
      # clean up duplicated fds if watcher failed to start
      for fd in pass_fds:
        try: os.close(fd)
        except OSError: pass
      return

    time.sleep(0.6)  # let HTTP response flush to client
    os.kill(parent_pid, signal.SIGTERM)

  threading.Thread(target=_spawn_watcher, daemon=True, name="server-restart").start()

  return jsonify({
    "success": True,
    "message": "Server restart initiated. Reconnect in a few seconds.",
  })
