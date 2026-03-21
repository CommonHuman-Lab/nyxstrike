#!/usr/bin/env python3
"""
HexStrike AI - Advanced Penetration Testing Framework Server

Enhanced with AI-Powered Intelligence & Automation
🚀 Bug Bounty | CTF | Red Team | Security Research

Framework: FastMCP integration for AI agent communication
"""

import argparse
import hmac
import json
import logging
import os
from flask import Flask, request, abort, jsonify
import server_core.config_core as config_core
from server_core.modern_visual_engine import ModernVisualEngine
from server_core.singletons import run_history
from server_api import register_blueprints

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
API_PORT = int(os.environ.get('HEXSTRIKE_PORT', 8888))
API_HOST = os.environ.get('HEXSTRIKE_HOST', '127.0.0.1')  # e.g. export HEXSTRIKE_HOST=0.0.0.0
API_TOKEN = os.environ.get("HEXSTRIKE_API_TOKEN", None)  # e.g. export API_TOKEN=secret-token

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
    if request.method == "POST" and request.content_length != 0 and request.json is None:
        return jsonify({
            "error": "Request body must be valid JSON with Content-Type: application/json",
            "success": False,
        }), 400

register_blueprints(app)

@app.after_request
def record_tool_run(response):
  """Record every POST /api/tools/<name> execution into run_history."""
  if request.method != "POST":
    return response
  path = request.path  # e.g. /api/tools/nmap
  if not path.startswith("/api/tools/"):
    return response
  # Derive tool name from the last path segment
  tool_name = path.split("/api/tools/", 1)[1].strip("/") or "unknown"
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
    run_history.record(
      tool=tool_name,
      endpoint=path,
      params=params,
      result=body,
    )
  return response

@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    logger.exception("Unhandled exception")
    return jsonify({"error": str(e), "success": False}), 500

if __name__ == "__main__":
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        BANNER = ModernVisualEngine.create_banner()
        print(BANNER)

    parser = argparse.ArgumentParser(description="Run the HexStrike AI API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Port for the API server (default: {API_PORT}) i.e export HEXSTRIKE_PORT=8888")
    parser.add_argument("--host", type=str, default=API_HOST, help=f"Host for the API server (default: {API_HOST}) i.e export HEXSTRIKE_HOST=0.0.0.0")

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

    app.run(host=API_HOST, port=API_PORT, debug=DEBUG_MODE)
