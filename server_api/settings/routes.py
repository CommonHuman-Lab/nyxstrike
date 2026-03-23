import os
import logging
from flask import Blueprint, jsonify, request
import server_core.config_core as config_core

logger = logging.getLogger(__name__)

api_settings_bp = Blueprint("api_settings", __name__)

# Keys that may be mutated at runtime via PATCH /api/settings
_MUTABLE_KEYS = {"COMMAND_TIMEOUT", "CACHE_SIZE", "CACHE_TTL", "TOOL_AVAILABILITY_TTL"}


def _current_settings() -> dict:
    return {
        "server": {
            "host": os.environ.get("HEXSTRIKE_HOST", "127.0.0.1"),
            "port": int(os.environ.get("HEXSTRIKE_PORT", 8888)),
            "auth_enabled": bool(os.environ.get("HEXSTRIKE_API_TOKEN")),
            "debug_mode": os.environ.get("DEBUG_MODE", "0") in ("1", "true", "yes", "y"),
            "data_dir": os.environ.get(
                "HEXSTRIKE_DATA_DIR",
                os.path.join(os.getcwd(), ".hexstrike_data"),
            ),
        },
        "runtime": {
            "command_timeout": config_core.get("COMMAND_TIMEOUT", 300),
            "cache_size": config_core.get("CACHE_SIZE", 1000),
            "cache_ttl": config_core.get("CACHE_TTL", 3600),
            "tool_availability_ttl": config_core.get("TOOL_AVAILABILITY_TTL", 3600),
        },
        "wordlists": _wordlists_summary(),
    }


def _wordlists_summary() -> list:
    raw = config_core.get("WORD_LISTS", {})
    out = []
    for name, meta in raw.items():
        out.append({
            "name": name,
            "path": meta.get("path", ""),
            "type": meta.get("type", ""),
            "speed": meta.get("speed", ""),
            "coverage": meta.get("coverage", ""),
        })
    return out


@api_settings_bp.route("/api/settings", methods=["GET"])
def get_settings():
    try:
        return jsonify({"success": True, "settings": _current_settings()})
    except Exception as exc:
        logger.error("get_settings error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500


@api_settings_bp.route("/api/settings", methods=["PATCH"])
def patch_settings():
    try:
        body = request.get_json(force=True, silent=True) or {}
        runtime = body.get("runtime", {})
        updated = {}
        errors = {}

        key_map = {
            "command_timeout": ("COMMAND_TIMEOUT", int),
            "cache_size": ("CACHE_SIZE", int),
            "cache_ttl": ("CACHE_TTL", int),
            "tool_availability_ttl": ("TOOL_AVAILABILITY_TTL", int),
        }

        for field, (cfg_key, cast) in key_map.items():
            if field not in runtime:
                continue
            try:
                val = cast(runtime[field])
                if val <= 0:
                    raise ValueError("must be positive")
                config_core.set_value(cfg_key, val)
                updated[field] = val
            except (ValueError, TypeError) as exc:
                errors[field] = str(exc)

        if errors:
            return jsonify({"success": False, "errors": errors, "updated": updated}), 400

        return jsonify({"success": True, "updated": updated, "settings": _current_settings()})
    except Exception as exc:
        logger.error("patch_settings error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500
