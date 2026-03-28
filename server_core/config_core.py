"""
core/config_core.py

Configuration access utilities for HexStrike core.

This module provides functions to retrieve and manage wordlist metadata,
paths, and general configuration values from the global config object.

Functions:
    get_word_list(name): Retrieve metadata for a wordlist by name.
    find_best_wordlist(criteria): Find the best wordlist matching criteria.
    get_word_list_path(name): Get the filesystem path for a wordlist.
    get(key, default): Get a config value by key.
    set_value(key, value): Set a config value by key.
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

def get_word_list(name: str) -> Optional[dict]:
    """
    Retrieve the metadata dictionary for a word list by its name.

    Args:
        name (str): The name of the word list.

    Returns:
        Optional[dict]: Metadata dictionary for the word list, or None if not found.
    """
    return _config["WORD_LISTS"].get(name)

def find_best_wordlist(criteria: dict) -> Optional[dict]:
    """
    Find the best wordlist matching all given criteria.

    Args:
        criteria (dict): Criteria to match against wordlist metadata fields.
            Supported keys include:
                - for_task: Task the wordlist is recommended for (matches if value is in 'recommended_for' list)
                - tool: Tool the wordlist is intended for (matches if value is in 'tool' list)
                - type: Type of wordlist (e.g., 'password', 'directory')
                - language: Language of the wordlist (e.g., 'en')
                - speed: Speed category (e.g., 'fast', 'medium', 'slow')
                - coverage: Coverage type (e.g., 'broad', 'focused')
                - format: File format (e.g., 'txt', 'lst')   

    Returns:
        Optional[dict]: Dictionary {"name": ..., "wordlist": ...} for the best match, or None if not found.
    """
    wordlists = _config["WORD_LISTS"]
    def matches(wl):
        for key, value in criteria.items():
            if key == "for_task":
                if value not in wl.get("recommended_for", []):
                    return False
            elif key == "tool":
                if value not in wl.get("tool", []):
                    return False
            else:
                if wl.get(key) != value:
                    return False
        return True

    # 1. Exact match for all criteria
    for name, wl in wordlists.items():
        if matches(wl):
            return {"name": name, "wordlist": wl}

    # 2. Relaxed: match at least for_task, then as many as possible
    if "for_task" in criteria:
        for name, wl in wordlists.items():
            if criteria["for_task"] in wl.get("recommended_for", []):
                return {"name": name, "wordlist": wl}

    # 3. Fallback: return any wordlist
    for name, wl in wordlists.items():
        logger.warning(
            "find_best_wordlist: no match for criteria %r — falling back to first available wordlist %r",
            criteria, name,
        )
        return {"name": name, "wordlist": wl}
    return None

def get_word_list_path(name: str) -> Optional[str]:
    """
    Get the filesystem path to a word list by its name.

    Args:
        name (str): The name of the word list.

    Returns:
        Optional[str]: Path to the word list, or None if not found.
    """
    wl = _config["WORD_LISTS"].get(name)
    if wl:
        return wl.get("path")
    return None

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