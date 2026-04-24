"""
core/config_core.py

Configuration access utilities for core services.

This module provides functions to retrieve and manage wordlist metadata,
paths, and general configuration values from the global config object.

Functions:
    default_data_dir(): Get the default data directory path.
    get(key, default): Get a config value by key.
    set_value(key, value): Set a config value by key and persist to local overrides.
"""

from typing import Any, Optional
import logging
import threading
import config
import os
import json
import shutil

logger = logging.getLogger(__name__)

_config = config._config
_config_lock = threading.Lock()

DATA_DIR_NAME = _config.get("DATA_DIR_NAME", ".nyxstrike_data")
CONFIG_DIR_NAME = "config"
LOCAL_FILE_NAME = "config_local.json"


def default_data_dir() -> str:
    """Resolve the data directory path. Uses NYXSTRIKE_DATA_DIR env var or cwd."""
    return os.environ.get("NYXSTRIKE_DATA_DIR", os.path.join(os.getcwd(), DATA_DIR_NAME))


def _resolve_config_local_path() -> str:
    """Resolve config_local path and migrate legacy root file if needed."""
    explicit_file = os.environ.get("NYXSTRIKE_CONFIG_FILE", "").strip()
    if explicit_file:
        os.makedirs(os.path.dirname(explicit_file), exist_ok=True)
        return explicit_file

    data_dir = default_data_dir()
    legacy_path = os.path.join(data_dir, LOCAL_FILE_NAME)
    config_dir = os.path.join(data_dir, CONFIG_DIR_NAME)
    new_path = os.path.join(config_dir, LOCAL_FILE_NAME)

    os.makedirs(config_dir, exist_ok=True)

    if os.path.exists(legacy_path) and not os.path.exists(new_path):
        try:
            shutil.move(legacy_path, new_path)
        except OSError:
            # Fallback to copy+remove for cross-device or permission edge cases.
            shutil.copy2(legacy_path, new_path)
            try:
                os.remove(legacy_path)
            except OSError:
                pass

    return new_path


_CONFIG_LOCAL_PATH = _resolve_config_local_path()

# Load overrides from config_local.json if it exists
if os.path.exists(_CONFIG_LOCAL_PATH):
    try:
        with open(_CONFIG_LOCAL_PATH, "r", encoding="utf-8") as f:
            overrides = json.load(f)
            _config.update(overrides)
    except Exception as e:
        logger.warning("Failed to load config_local.json: %r", e)

def get(key: str, default: Optional[Any] = None) -> Any:
    """
    Retrieve a configuration value by key.

    Args:
        key (str): The configuration key.
        default (Any, optional): Default value if key is not found.

    Returns:
        Any: The configuration value, or default if not found.
    """
    return _config.get(key, default)

def set_value(key: str, value: Any) -> None:
    """
    Set a configuration value by key and persist it to config_local.json.
    """
    with _config_lock:
        _config[key] = value
        # Persist to config_local.json
        try:
            # Only store overrides, not the whole config
            overrides = {}
            os.makedirs(os.path.dirname(_CONFIG_LOCAL_PATH), exist_ok=True)
            if os.path.exists(_CONFIG_LOCAL_PATH):
                with open(_CONFIG_LOCAL_PATH, "r", encoding="utf-8") as f:
                    overrides = json.load(f)
            overrides[key] = value
            with open(_CONFIG_LOCAL_PATH, "w", encoding="utf-8") as f:
                json.dump(overrides, f, indent=2)
        except Exception as e:
            logger.warning("Failed to write config_local.json: %r", e)
