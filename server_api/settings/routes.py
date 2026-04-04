import os
import logging
from typing import Dict, Tuple
from flask import Blueprint, jsonify, request
import server_core.config_core as config_core
from server_core.singletons import wordlist_store

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
            "working_dir": os.getcwd(),
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
    raw = wordlist_store.load_all()
    default_names = set(config_core.get("WORD_LISTS", {}).keys())
    out = []
    for name, meta in raw.items():
        out.append({
            "name": name,
            "path": meta.get("path", ""),
            "type": meta.get("type", ""),
            "speed": meta.get("speed", ""),
            "coverage": meta.get("coverage", ""),
            "is_default": name in default_names,
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


def _persist_wordlists(wordlists: list) -> Tuple[Dict[str, int], Dict[str, str]]:
    updated = {}
    errors = {}
    seen_names = set()
    original_names = {item.get("name", "") for item in _wordlists_summary()}
    default_names = set(config_core.get("WORD_LISTS", {}).keys())
    user_wordlists = wordlist_store.load_user_wordlists()
    saved_count = 0

    for idx, entry in enumerate(wordlists):
        if not isinstance(entry, dict):
            errors[f"wordlists[{idx}]"] = "must be an object"
            continue

        raw_name = str(entry.get("name", "")).strip()
        if not raw_name:
            errors[f"wordlists[{idx}].name"] = "name is required"
            continue
        if raw_name in seen_names:
            errors[f"wordlists[{idx}].name"] = "duplicate name"
            continue
        seen_names.add(raw_name)

        current = wordlist_store.load(raw_name) or {}
        merged = dict(current)
        for key in ("path", "type", "speed", "coverage"):
            if key in entry and entry[key] is not None:
                merged[key] = str(entry[key]).strip()

        if not merged.get("path"):
            errors[f"wordlists[{idx}].path"] = "path is required"
            continue
        if not merged.get("type"):
            errors[f"wordlists[{idx}].type"] = "type is required"
            continue

        if not wordlist_store.save(raw_name, merged):
            errors[f"wordlists[{idx}]"] = "failed to save"
            continue
        saved_count += 1

    provided_names = set(seen_names)
    for existing_name in original_names - provided_names:
        if existing_name in default_names:
            continue
        if existing_name in user_wordlists:
            if not wordlist_store.delete(existing_name):
                errors[f"wordlists[{existing_name}]"] = "failed to delete"

    if saved_count:
        updated["wordlists"] = saved_count

    return updated, errors


@api_settings_bp.route("/api/settings/wordlists", methods=["PATCH"])
def patch_wordlists():
    try:
        body = request.get_json(force=True, silent=True) or {}
        wordlists = body.get("wordlists")
        if not isinstance(wordlists, list):
            return jsonify({"success": False, "errors": {"wordlists": "must be a list"}, "updated": {}}), 400

        updated, errors = _persist_wordlists(wordlists)
        if errors:
            return jsonify({"success": False, "errors": errors, "updated": updated}), 400

        return jsonify({"success": True, "updated": updated, "wordlists": _wordlists_summary()})
    except Exception as exc:
        logger.error("patch_wordlists error: %s", exc)
        return jsonify({"success": False, "error": str(exc)}), 500
