"""
core/config_core.py

Configuration access utilities for HexStrike core.

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

logger = logging.getLogger(__name__)

_config = config._config
_config_lock = threading.Lock()

DATA_DIR_NAME = _config.get("DATA_DIR_NAME", ".hexstrike_data")
LOCAL_FILE_NAME = "config_local.json"
_CONFIG_LOCAL_PATH = os.environ.get("HEXSTRIKE_DATA_DIR", os.path.join(os.getcwd(), DATA_DIR_NAME, LOCAL_FILE_NAME))

# Load overrides from config_local.json if it exists
if os.path.exists(_CONFIG_LOCAL_PATH):
    try:
        with open(_CONFIG_LOCAL_PATH, "r") as f:
            overrides = json.load(f)
            _config.update(overrides)
    except Exception as e:
        logger.warning("Failed to load config_local.json: %r", e)

def default_data_dir() -> str:
    """Resolve the data directory path. Uses HEXSTRIKE_DATA_DIR env var or cwd."""
    return os.environ.get("HEXSTRIKE_DATA_DIR", os.path.join(os.getcwd(), DATA_DIR_NAME))

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
            if os.path.exists(_CONFIG_LOCAL_PATH):
                with open(_CONFIG_LOCAL_PATH, "r") as f:
                    overrides = json.load(f)
            overrides[key] = value
            with open(_CONFIG_LOCAL_PATH, "w") as f:
                json.dump(overrides, f, indent=2)
        except Exception as e:
            logger.warning("Failed to write config_local.json: %r", e)