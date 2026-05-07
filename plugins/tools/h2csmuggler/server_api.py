import logging
import os
import shlex
from pathlib import Path

from flask import Blueprint, jsonify, request

from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)
blueprint = Blueprint("plugin_h2csmuggler", __name__)

DEFAULT_SCRIPT_PATH = "/usr/local/bin/h2csmuggler.py"


def _as_bool(value):
  if isinstance(value, bool):
    return value
  if value is None:
    return False
  if isinstance(value, (int, float)):
    return value != 0
  return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_headers(raw_headers):
  if isinstance(raw_headers, list):
    return [str(h).strip() for h in raw_headers if str(h).strip()]
  if not raw_headers:
    return []
  return [h.strip() for h in str(raw_headers).split(";") if h.strip()]


def _valid_url(url):
  return isinstance(url, str) and url.startswith(("http://", "https://"))


def _resolve_script_path():
  env_path = os.getenv("NYXSTRIKE_H2CSMUGGLER_PATH", "").strip()
  candidates = [
    env_path,
    DEFAULT_SCRIPT_PATH,
    str(Path(__file__).parent / "h2csmuggler.py"),
  ]
  for candidate in candidates:
    if candidate and Path(candidate).is_file():
      return candidate
  return ""


@blueprint.route("/api/plugins/h2csmuggler", methods=["POST"])
def h2csmuggler():
  data = request.get_json(force=True) or {}

  proxy = str(data.get("proxy", "")).strip()
  target_url = str(data.get("target_url", "")).strip()
  scan_list = str(data.get("scan_list", "")).strip()
  request_method = str(data.get("request", "GET")).strip().upper() or "GET"
  req_data = str(data.get("data", ""))
  headers = _parse_headers(data.get("headers", ""))
  wordlist = str(data.get("wordlist", "")).strip()
  additional_args = str(data.get("additional_args", "")).strip()
  upgrade_only = _as_bool(data.get("upgrade_only", False))
  test = _as_bool(data.get("test", False))
  verbose = _as_bool(data.get("verbose", False))

  try:
    max_time = float(data.get("max_time", 10))
  except (TypeError, ValueError):
    max_time = 10
  max_time = max(1, min(max_time, 120))

  try:
    threads = int(data.get("threads", 5))
  except (TypeError, ValueError):
    threads = 5
  threads = max(1, min(threads, 50))

  if not proxy:
    return jsonify({"error": "Missing required parameter: proxy", "success": False}), 400
  if not _valid_url(proxy):
    return jsonify({"error": "proxy must start with http:// or https://", "success": False}), 400

  if scan_list:
    mode = "scan"
  elif test:
    mode = "test"
  else:
    mode = "exploit"

  if mode == "scan" and test:
    return jsonify({"error": "scan_list mode cannot be combined with test=true", "success": False}), 400
  if mode == "exploit":
    if not target_url:
      return jsonify({"error": "target_url is required in exploit mode", "success": False}), 400
    if not _valid_url(target_url):
      return jsonify({"error": "target_url must start with http:// or https://", "success": False}), 400
  if mode == "scan" and not Path(scan_list).is_file():
    return jsonify({"error": "scan_list file not found", "success": False}), 400

  script_path = _resolve_script_path()
  if not script_path:
    return jsonify({
      "error": "h2csmuggler.py not found. Set NYXSTRIKE_H2CSMUGGLER_PATH or install to /usr/local/bin/h2csmuggler.py",
      "success": False,
    }), 500

  cmd = ["python3", script_path, "-x", proxy, "-m", str(max_time)]

  if upgrade_only:
    cmd.append("--upgrade-only")
  if verbose:
    cmd.append("-v")

  if mode == "scan":
    cmd.extend(["--scan-list", scan_list, "--threads", str(threads)])
  elif mode == "test":
    cmd.append("-t")
  else:
    cmd.extend(["-X", request_method])
    if req_data:
      cmd.extend(["-d", req_data])
    for header in headers:
      cmd.extend(["-H", header])
    if wordlist:
      cmd.extend(["-i", wordlist])
    cmd.append(target_url)

  if additional_args:
    cmd.extend(shlex.split(additional_args))

  command = " ".join(shlex.quote(part) for part in cmd)
  timeout = max(60, int(max_time * max(1, threads)) + 15)

  logger.info("Starting h2csmuggler mode=%s proxy=%s", mode, proxy)
  result = execute_command(command, use_cache=False, timeout=timeout)
  return jsonify(result)
