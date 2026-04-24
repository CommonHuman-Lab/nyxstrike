"""
Plugin: example_net_ping — server_api.py
Flask Blueprint that executes ping and returns structured results.

This file is the server-side half of the plugin.
It must expose a module-level `blueprint` (a Flask Blueprint instance).
The plugin loader registers it with the Flask app automatically.
"""

import re
import logging
from flask import Blueprint, request, jsonify
from server_core.command_executor import execute_command

logger = logging.getLogger(__name__)

blueprint = Blueprint("plugin_net_ping", __name__)


@blueprint.route("/api/plugins/net_ping", methods=["POST"])
def net_ping():
  """
  ICMP ping endpoint.

  Expects JSON:
    {
      "target":  "192.168.1.1",   # required
      "count":   4,               # optional, default 4
      "timeout": 10               # optional, default 10 s
    }

  Returns:
    {
      "success":      bool,
      "output":       str,   # raw ping output
      "packets_sent": int,
      "packets_recv": int,
      "packet_loss":  str,   # e.g. "0%"
      "rtt_min":      str,
      "rtt_avg":      str,
      "rtt_max":      str
    }
  """
  data = request.get_json(force=True) or {}
  target = (data.get("target") or "").strip()
  if not target:
    return jsonify({"error": "Missing required parameter: target", "success": False}), 400

  try:
    count = max(1, min(int(data.get("count", 4)), 20))
  except (TypeError, ValueError):
    count = 4

  try:
    timeout = max(1, min(int(data.get("timeout", 10)), 60))
  except (TypeError, ValueError):
    timeout = 10

  cmd = f"ping -c {count} -W {timeout} {target}"
  result = execute_command(cmd, use_cache=False, timeout=timeout * count + 5)

  output = result.get("stdout") or result.get("stderr") or ""
  success = result.get("success", False)

  # Parse summary line: "4 packets transmitted, 4 received, 0% packet loss"
  packets_sent = packets_recv = 0
  packet_loss = "unknown"
  rtt_min = rtt_avg = rtt_max = "N/A"

  summary_match = re.search(
    r"(\d+) packets transmitted,\s*(\d+) (?:packets )?received,\s*([\d.]+)% packet loss",
    output,
  )
  if summary_match:
    packets_sent = int(summary_match.group(1))
    packets_recv = int(summary_match.group(2))
    packet_loss = f"{summary_match.group(3)}%"

  # Parse RTT line: "rtt min/avg/max/mdev = 0.123/0.456/0.789/0.100 ms"
  rtt_match = re.search(
    r"rtt min/avg/max/mdev\s*=\s*([\d.]+)/([\d.]+)/([\d.]+)/[\d.]+ ms",
    output,
  )
  if rtt_match:
    rtt_min = f"{rtt_match.group(1)} ms"
    rtt_avg = f"{rtt_match.group(2)} ms"
    rtt_max = f"{rtt_match.group(3)} ms"

  return jsonify({
    "success": success,
    "output": output,
    "packets_sent": packets_sent,
    "packets_recv": packets_recv,
    "packet_loss": packet_loss,
    "rtt_min": rtt_min,
    "rtt_avg": rtt_avg,
    "rtt_max": rtt_max,
  })
