"""
server_api/ops/plugins.py

REST endpoints for the plugin system.

  GET   /api/plugins/list          — flat list of all loaded plugins
  GET   /api/plugins/by-category   — plugins grouped by category
  GET   /api/plugins/by-type       — plugins grouped by plugin type
  GET   /api/plugins/manifest      — all plugins from plugins.yaml (loaded + disabled)
  PATCH /api/plugins/<name>        — toggle enabled/disabled flag in plugins.yaml
"""

import logging
from flask import Blueprint, jsonify, request
from server_core.plugin_loader import (
  get_plugin_list,
  get_plugins_by_category,
  get_plugins_by_type,
  get_manifest_entries,
  set_plugin_enabled,
)

logger = logging.getLogger(__name__)

api_plugins_bp = Blueprint("api_plugins", __name__)


@api_plugins_bp.route("/api/plugins/list", methods=["GET"])
def plugins_list():
  """Return a flat list of all successfully loaded plugins."""
  try:
    return jsonify({"success": True, "plugins": get_plugin_list()})
  except Exception as exc:
    logger.error("plugins_list error: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_plugins_bp.route("/api/plugins/by-category", methods=["GET"])
def plugins_by_category():
  """Return plugins grouped by their declared category."""
  try:
    return jsonify({"success": True, "categories": get_plugins_by_category()})
  except Exception as exc:
    logger.error("plugins_by_category error: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_plugins_bp.route("/api/plugins/by-type", methods=["GET"])
def plugins_by_type():
  """Return plugins grouped by plugin type (tools, workflows, …)."""
  try:
    return jsonify({"success": True, "types": get_plugins_by_type()})
  except Exception as exc:
    logger.error("plugins_by_type error: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_plugins_bp.route("/api/plugins/manifest", methods=["GET"])
def plugins_manifest():
  """Return every plugin declared in plugins.yaml including disabled ones."""
  try:
    entries = get_manifest_entries()
    return jsonify({"success": True, "plugins": entries, "total": len(entries)})
  except Exception as exc:
    logger.error("plugins_manifest error: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500


@api_plugins_bp.route("/api/plugins/<string:plugin_name>", methods=["PATCH"])
def plugin_toggle(plugin_name: str):
  """Enable or disable a plugin in plugins.yaml.

  Body (JSON): ``{"enabled": true|false}``

  A server restart is required for the change to take effect.
  """
  try:
    body = request.get_json(silent=True) or {}
    if "enabled" not in body:
      return jsonify({"success": False, "error": "Missing 'enabled' field in request body"}), 400

    enabled = bool(body["enabled"])
    ok = set_plugin_enabled(plugin_name, enabled)
    if not ok:
      return jsonify({
        "success": False,
        "error": f"Plugin '{plugin_name}' not found in plugins.yaml",
      }), 404

    return jsonify({
      "success": True,
      "plugin": plugin_name,
      "enabled": enabled,
      "message": f"Plugin '{plugin_name}' {'enabled' if enabled else 'disabled'}. Restart the server to apply.",
    })
  except Exception as exc:
    logger.error("plugin_toggle error: %s", exc)
    return jsonify({"success": False, "error": str(exc)}), 500
