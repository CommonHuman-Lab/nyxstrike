"""
mcp_core/plugin_mcp_loader.py

Loads plugin MCP tools from ``plugins/`` into a running FastMCP instance.

Mirrors the type-aware structure of server_core/plugin_loader.py:
  plugins/tools/<name>/mcp_tool.py   — must expose register(mcp, api_client, logger)

Called from ``mcp_core/server_setup.py`` after standard profile tools are
registered.  Problems with individual plugins are logged and skipped.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_REPO_ROOT     = Path(__file__).parent.parent
_PLUGINS_DIR   = _REPO_ROOT / "plugins"
_MANIFEST_FILE = _PLUGINS_DIR / "plugins.yaml"


# ---------------------------------------------------------------------------
# Minimal YAML loader (no dependency on server_core)
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> Dict[str, Any]:
  try:
    import yaml  # type: ignore
    with path.open("r", encoding="utf-8") as fh:
      return yaml.safe_load(fh) or {}
  except ImportError:
    pass

  import re
  result: Dict[str, Any] = {}
  current_list_key: Optional[str] = None
  current_list: List[Any] = []
  current_item: Optional[Dict[str, Any]] = None

  with path.open("r", encoding="utf-8") as fh:
    for raw_line in fh:
      line = raw_line.rstrip()
      stripped = line.lstrip()
      if not stripped or stripped.startswith("#"):
        continue
      indent = len(line) - len(stripped)

      if indent == 0 and stripped.startswith("- "):
        if current_item is not None and current_list_key:
          current_list.append(current_item)
          current_item = None
        value_part = stripped[2:].strip()
        if ":" in value_part:
          k, v = value_part.split(":", 1)
          current_item = {k.strip(): v.strip()}
        else:
          current_list.append(value_part)
        continue

      if indent >= 2 and current_item is not None and ":" in stripped:
        k, v = stripped.split(":", 1)
        current_item[k.strip()] = v.strip()
        continue

      if ":" in stripped and indent == 0:
        if current_item is not None and current_list_key:
          current_list.append(current_item)
          current_item = None
        if current_list_key and current_list:
          result[current_list_key] = current_list
          current_list = []
          current_list_key = None
        k, v = stripped.split(":", 1)
        key = k.strip()
        val = v.strip()
        if val == "":
          current_list_key = key
          current_list = []
        else:
          result[key] = re.sub(r'^["\']|["\']$', "", val)
        continue

      if indent >= 2 and stripped.startswith("- ") and current_list_key is not None:
        current_list.append(stripped[2:].strip())

  if current_item is not None and current_list_key:
    current_list.append(current_item)
  if current_list_key and current_list:
    result[current_list_key] = current_list

  return result


# ---------------------------------------------------------------------------
# Type → subfolder mapping  (extend when new plugin types are introduced)
# ---------------------------------------------------------------------------
# Each key is the manifest section name; the value is the subfolder under
# plugins/ where those plugins live, and the name of the file to import.

_TYPE_CONFIG: Dict[str, Dict[str, str]] = {
  "tools": {
    "subdir":   "tools",
    "filename": "mcp_tool.py",
  },
  # Future example:
  # "workflows": {
  #   "subdir":   "workflows",
  #   "filename": "mcp_workflow.py",
  # },
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_plugin_tools(mcp, api_client, logger_override=None) -> None:
  """Import and register MCP tools/workflows from all enabled plugins.

  Args:
      mcp:             FastMCP instance to register tools on.
      api_client:      ApiClient used to forward calls to the Flask server.
      logger_override: Optional logger; falls back to this module's logger.
  """
  log = logger_override or logger

  if not _MANIFEST_FILE.exists():
    log.debug("plugin_mcp_loader: no plugins/plugins.yaml — skipping")
    return

  try:
    manifest = _load_yaml(_MANIFEST_FILE)
  except Exception as exc:
    log.warning("plugin_mcp_loader: failed to read plugins.yaml: %s", exc)
    return

  total = 0

  for plugin_type, entries in manifest.items():
    if not isinstance(entries, list):
      continue

    type_cfg = _TYPE_CONFIG.get(plugin_type)
    if type_cfg is None:
      # Not an MCP-bearing type — silently skip (server_core handles it)
      continue

    subdir   = type_cfg["subdir"]
    filename = type_cfg["filename"]

    for entry in entries:
      if not isinstance(entry, dict):
        continue
      name = entry.get("name", "").strip()
      if not name:
        continue
      enabled = str(entry.get("enabled", "true")).lower() not in ("false", "0", "no")
      if not enabled:
        continue

      plugin_dir  = _PLUGINS_DIR / subdir / name
      target_file = plugin_dir / filename

      if not target_file.exists():
        log.warning("plugin_mcp_loader [%s]: '%s' — %s not found", plugin_type, name, filename)
        continue

      try:
        module = _import_file(f"_plugin_mcp_{plugin_type}_{name}", target_file)
      except Exception as exc:
        log.warning("plugin_mcp_loader [%s]: '%s' — import failed: %s", plugin_type, name, exc)
        continue

      register_fn = getattr(module, "register", None)
      if register_fn is None:
        log.warning(
          "plugin_mcp_loader [%s]: '%s' — %s has no 'register' function",
          plugin_type, name, filename,
        )
        continue

      try:
        register_fn(mcp, api_client, log)
        total += 1
        log.info("plugin_mcp_loader [%s]: '%s' registered", plugin_type, name)
      except Exception as exc:
        log.warning(
          "plugin_mcp_loader [%s]: '%s' — register() failed: %s",
          plugin_type, name, exc,
        )

  if total:
    log.info("plugin_mcp_loader: %d plugin MCP registration(s) complete", total)


def _import_file(module_name: str, path: Path):
  spec = importlib.util.spec_from_file_location(module_name, str(path))
  if spec is None or spec.loader is None:
    raise ImportError(f"Cannot create module spec for {path}")
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)  # type: ignore[union-attr]
  return module
