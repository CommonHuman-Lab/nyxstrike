"""
server_api/ops/plugins.py

REST endpoints for the plugin system.

  GET  /api/plugins/list          — flat list of all loaded plugins
  GET  /api/plugins/by-category   — plugins grouped by category
  GET  /api/plugins/by-type       — plugins grouped by plugin type
"""

import logging
from flask import Blueprint, jsonify
from server_core.plugin_loader import (
  get_plugin_list,
  get_plugins_by_category,
  get_plugins_by_type,
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
