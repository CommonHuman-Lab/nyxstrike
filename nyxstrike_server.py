#!/usr/bin/env python3
"""
NyxStrike - Advanced Penetration Testing Framework Server

Enhanced with AI-Powered Intelligence & Automation
🚀 Bug Bounty | CTF | Red Team | Security Research

Framework: FastMCP integration for AI agent communication
"""

import argparse
import hmac
import logging
import os
import threading
from flask import Flask, request, abort, jsonify
import server_core.config_core as config_core
from server_core.modern_visual_engine import ModernVisualEngine
from server_core.singletons import run_history, tool_stats
from server_core.session_flow import append_event as _append_event, append_run_log as _append_run_log
from server_api import register_blueprints
from server_api.ops.web_dashboard import initialize_update_status_check
from server_core.plugin_loader import load_plugins

# ============================================================================
# LOGGING CONFIGURATION (MUST BE FIRST)
# ============================================================================

from server_core.setup_logging import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# API Configuration
API_PORT = int(os.environ.get('NYXSTRIKE_PORT', 8888))
API_HOST = os.environ.get('NYXSTRIKE_HOST', '127.0.0.1')  # e.g. export NYXSTRIKE_HOST=0.0.0.0
API_TOKEN = os.environ.get("NYXSTRIKE_API_TOKEN", None)  # e.g. export API_TOKEN=secret-token

# Configuration
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes", "y")
COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # 5 minutes default timeout
CACHE_SIZE = config_core.get("CACHE_SIZE", 1000)
CACHE_TTL = config_core.get("CACHE_TTL", 3600)  # 1 hour default TTL

@app.before_request
def optional_bearer_auth():
    # If no token is configured, allow all requests
    if not API_TOKEN:
        return

    auth_header = request.headers.get("Authorization", "")
    prefix = "Bearer "

    if not auth_header.startswith(prefix):
        abort(401, description="Unexpected authorization header format")

    token = auth_header[len(prefix):]
    if not hmac.compare_digest(token, API_TOKEN):
        abort(401, description="Unauthorized!")

@app.before_request
def require_json_for_post():
    """Return 400 instead of a 500 AttributeError when a POST body is missing or not JSON."""
    if request.method != "POST":
        return
    if not request.content_type or not request.content_type.startswith("application/json"):
        return  # multipart uploads and other non-JSON POSTs are handled by their own routes
    if request.content_length != 0 and request.json is None:
        return jsonify({
            "error": "Request body must be valid JSON with Content-Type: application/json",
            "success": False,
        }), 400

register_blueprints(app)
load_plugins(app)
initialize_update_status_check()

# Pre-load the Ollama model in the background so it's ready before the first request.
# Only runs when NYXSTRIKE_LLM_WARMUP=1 is set (done automatically by -ai / -ai-small flags).
def _warm_up_llm() -> None:
  from server_core.singletons import llm_client
  llm_client.warm_up()

if os.environ.get("NYXSTRIKE_LLM_WARMUP") == "1":
  threading.Thread(target=_warm_up_llm, daemon=True, name="llm-warmup").start()


def _build_tool_context_key(path: str, params: dict, body: dict) -> str:
  """Build context key for contextual tool effectiveness tracking."""
  try:
    if path.startswith("/api/intelligence/"):
      target_profile = body.get("target_profile", {}) if isinstance(body, dict) else {}
      target_type = target_profile.get("target_type", "unknown") if isinstance(target_profile, dict) else "unknown"
      objective = "comprehensive"
      if isinstance(params, dict):
        objective = str(params.get("objective", "comprehensive")).strip().lower()
      technologies = target_profile.get("technologies", []) if isinstance(target_profile, dict) else []
      primary_tech = "none"
      if isinstance(technologies, list):
        for tech in technologies:
          if isinstance(tech, str) and tech and tech != "unknown":
            primary_tech = tech
            break
      return f"{target_type}|{objective}|{primary_tech}"

    if path.startswith("/api/tools/") and isinstance(params, dict):
      target = params.get("target") or params.get("url") or params.get("domain") or ""
      target_text = str(target).lower()
      if target_text.startswith(("http://", "https://")):
        target_type = "web_application"
      elif "/api" in target_text:
        target_type = "api_endpoint"
      else:
        target_type = "unknown"
      return f"{target_type}|tool_run|none"
  except Exception:
    return ""
  return ""

@app.after_request
def record_tool_run(response):
  """Record selected POST executions into run_history."""
  if request.method != "POST":
    return response

  path = request.path
  is_tool_run = path.startswith("/api/tools/")
  is_intelligence_run = path in {
    "/api/intelligence/analyze-target",
    "/api/intelligence/smart-scan",
    "/api/intelligence/select-tools",
    "/api/intelligence/technology-detection",
    #"/api/intelligence/preview-attack-chain",
    "/api/intelligence/create-attack-chain",
    "/api/intelligence/analyze-session",
  }
  if not is_tool_run and not is_intelligence_run:
    return response

  if is_tool_run:
    tool_name = path.split("/api/tools/", 1)[1].strip("/") or "unknown"
  else:
    tool_name = path.rsplit("/", 1)[-1] or "unknown"

  try:
    params = request.json or {}
  except Exception:
    params = {}
  try:
    body = response.get_json(silent=True) or {}
  except Exception:
    body = {}
  # Only record responses that look like tool execution results
  if "stdout" in body or "stderr" in body or "return_code" in body:
    session_id = (params.get("session_id") or "") if isinstance(params, dict) else ""
    run_history.record(
      tool=tool_name,
      endpoint=path,
      params=params,
      result=body,
      session_id=session_id,
    )
    # A run is "successful" when the tool reported success AND produced output.
    ran_ok = bool(body.get("success", False)) and bool(str(body.get("stdout", "")).strip())
    tool_stats.record(tool=tool_name, success=ran_ok)
    context_key = _build_tool_context_key(path, params, body)
    if context_key:
      tool_stats.record_contextual(tool=tool_name, success=ran_ok, context_key=context_key)
    # Emit a tool_run event on the associated session when a session_id is present
    if session_id:
      try:
        status_label = "succeeded" if ran_ok else "completed"
        _append_event(session_id, "tool_run", f"Tool {tool_name} {status_label}", {
          "tool": tool_name,
          "success": ran_ok,
          "return_code": body.get("return_code"),
        })
        _append_run_log(session_id, {
          "tool": tool_name,
          "endpoint": path,
          "params": params if isinstance(params, dict) else {},
          "session_id": session_id,
          "stdout": body.get("stdout", ""),
          "stderr": body.get("stderr", ""),
          "return_code": body.get("return_code", -1),
          "success": bool(body.get("success", False)),
          "timed_out": bool(body.get("timed_out", False)),
          "partial_results": bool(body.get("partial_results", False)),
          "execution_time": body.get("execution_time", 0),
          "timestamp": body.get("timestamp", ""),
        })
      except Exception:
        logger.debug("session_flow recording failed for tool %s", tool_name, exc_info=True)
  return response

@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    logger.exception("Unhandled exception")
    return jsonify({"error": str(e), "success": False}), 500

if __name__ == "__main__":
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        BANNER = ModernVisualEngine.create_banner()
        print(BANNER)

    parser = argparse.ArgumentParser(description="Run the NyxStrike API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Port for the API server (default: {API_PORT}) i.e export NYXSTRIKE_PORT=8888")
    parser.add_argument("--host", type=str, default=API_HOST, help=f"Host for the API server (default: {API_HOST}) i.e export NYXSTRIKE_HOST=0.0.0.0")

    args = parser.parse_args()

    if args.debug:
        DEBUG_MODE = True
        logger.setLevel(logging.DEBUG)

    if args.port != API_PORT:
        API_PORT = args.port

    if args.host != API_HOST:
        API_HOST = args.host

    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # Enhanced startup messages with beautiful formatting.
        # ANSI codes have zero visible width, so we track visible length manually
        C = ModernVisualEngine.COLORS
        BOX_WIDTH = 66  # visible characters between the two │ borders (including leading space)

        import re as _re
        from wcwidth import wcswidth as _wcswidth
        _ansi = _re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')

        def _box_row(content_with_ansi: str) -> str:
            """Return a full box row: │ <content padded to BOX_WIDTH> │"""
            visible = _ansi.sub('', content_with_ansi)
            visible_len = _wcswidth(visible)
            if visible_len < 0:
                visible_len = len(visible)  # fallback if string has non-printable chars
            padding = ' ' * (BOX_WIDTH - visible_len)
            return (
                f"{C['BOLD']}{C['MATRIX_GREEN']}│{C['RESET']}"
                f"{content_with_ansi}{padding}"
                f"{C['BOLD']}{C['MATRIX_GREEN']}│{C['RESET']}"
            )

        _hr  = '─' * BOX_WIDTH
        lines = [
            f"{C['MATRIX_GREEN']}{C['BOLD']}╭{_hr}╮{C['RESET']}",
            _box_row(f" {C['RUBY']}🌐 Running on:{C['RESET']} http://{API_HOST}:{API_PORT}"),
            _box_row(f" {C['MATRIX_GREEN']}💻 Web Dashboard:{C['RESET']} http://{API_HOST}:{API_PORT}  ← open in browser"),
            _box_row(f" {C['WARNING']}🔧 Debug Mode:{C['RESET']} {DEBUG_MODE}"),
            _box_row(f" {C['ELECTRIC_PURPLE']}💾 Cache Size:{C['RESET']} {CACHE_SIZE} | TTL: {CACHE_TTL}s"),
            _box_row(f" {C['SCARLET']}⏰ Command Timeout:{C['RESET']} {COMMAND_TIMEOUT}s"),
            f"{C['MATRIX_GREEN']}{C['BOLD']}╰{_hr}╯{C['RESET']}",
        ]
        print('\n'.join(lines), flush=True)

    # Suppress Flask's click.echo() startup banner ("* Serving Flask app", "* Debug mode").
    # These bypass the logging system entirely, so a logging filter cannot catch them.
    import flask.cli as _flask_cli
    _flask_cli.show_server_banner = lambda *_a, **_kw: None

    app.run(host=API_HOST, port=API_PORT, debug=DEBUG_MODE, threaded=True)
