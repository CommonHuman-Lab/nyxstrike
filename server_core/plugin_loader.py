"""
server_core/plugin_loader.py

Discovers, validates, and loads NyxStrike plugins at server startup.

Plugin types
------------
tools   — Flask Blueprint (server_api.py) + FastMCP tool (mcp_tool.py).
          Lives under  plugins/tools/<name>/

(Additional types can be added by extending _TYPE_LOADERS below.)

Manifest
--------
plugins/plugins.yaml  —  root manifest; each top-level key is a plugin type
and its value is a list of {name, enabled} entries.

Error handling
--------------
Problems with an individual plugin are logged as warnings and that plugin is
**skipped** — the server continues to start normally.
"""

from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_REPO_ROOT    = Path(__file__).parent.parent
_PLUGINS_DIR  = _REPO_ROOT / "plugins"
_MANIFEST_FILE = _PLUGINS_DIR / "plugins.yaml"

# Internal registry: plugin_type -> {name -> metadata}
_loaded: Dict[str, Dict[str, Dict[str, Any]]] = {}

_REQUIRED_TOOL_META = (
  "name", "version", "description",
  "category", "endpoint", "mcp_tool_name", "effectiveness", "check",
)


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------

def _load_yaml(path: Path) -> Dict[str, Any]:
  """Load a YAML file.  Prefers PyYAML; falls back to a minimal inline parser."""
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

      if indent >= 2 and stripped.startswith("- "):
        item_val = stripped[2:].strip()
        if current_list_key is not None:
          current_list.append(item_val)

  if current_item is not None and current_list_key:
    current_list.append(current_item)
  if current_list_key and current_list:
    result[current_list_key] = current_list

  return result


# ---------------------------------------------------------------------------
# Tool plugin loader
# ---------------------------------------------------------------------------

def _load_tool_plugin(
  app,
  plugin_name: str,
  registered_endpoints: set,
  registered_tool_names: set,
) -> bool:
  """Load a single *tools* plugin.  Returns True on success."""
  plugin_dir = _PLUGINS_DIR / "tools" / plugin_name

  if not plugin_dir.is_dir():
    logger.warning("plugin_loader [tools]: '%s' — directory not found: %s", plugin_name, plugin_dir)
    return False

  # ---- plugin.yaml ----
  meta_file = plugin_dir / "plugin.yaml"
  if not meta_file.exists():
    logger.warning("plugin_loader [tools]: '%s' — plugin.yaml not found", plugin_name)
    return False

  try:
    meta = _load_yaml(meta_file)
  except Exception as exc:
    logger.warning("plugin_loader [tools]: '%s' — failed to parse plugin.yaml: %s", plugin_name, exc)
    return False

  # Coerce numeric fields
  if "effectiveness" in meta:
    try:
      meta["effectiveness"] = float(meta["effectiveness"])
    except (TypeError, ValueError):
      pass

  # Validate
  _VALID_CHECK_TYPES = ("builtin", "which", "dpkg", "pip", "gem", "cargo")
  errors: List[str] = []
  for key in _REQUIRED_TOOL_META:
    if key not in meta:
      errors.append(f"missing key '{key}'")
  endpoint = str(meta.get("endpoint", ""))
  if endpoint and not endpoint.startswith("/"):
    errors.append(f"endpoint '{endpoint}' must start with '/'")
  eff = meta.get("effectiveness")
  if eff is not None:
    try:
      eff_f = float(eff)
      if not 0.0 <= eff_f <= 1.0:
        errors.append(f"effectiveness {eff_f} must be 0.0–1.0")
    except (TypeError, ValueError):
      errors.append(f"effectiveness '{eff}' must be a float")
  check = meta.get("check")
  if check is not None:
    if not isinstance(check, dict):
      errors.append("check must be a mapping")
    else:
      check_type = str(check.get("type", "")).lower()
      if not check_type:
        errors.append("check.type is required")
      elif check_type not in _VALID_CHECK_TYPES:
        errors.append(f"check.type '{check_type}' must be one of: {', '.join(_VALID_CHECK_TYPES)}")
  if errors:
    logger.warning("plugin_loader [tools]: '%s' — %s — skipping", plugin_name, "; ".join(errors))
    return False

  tool_name = str(meta["mcp_tool_name"])

  # Duplicate checks
  if endpoint in registered_endpoints:
    logger.warning("plugin_loader [tools]: '%s' — endpoint '%s' already registered — skipping", plugin_name, endpoint)
    return False
  if tool_name in registered_tool_names:
    logger.warning("plugin_loader [tools]: '%s' — mcp_tool_name '%s' already registered — skipping", plugin_name, tool_name)
    return False

  # ---- Import server_api.py ----
  server_api_file = plugin_dir / "server_api.py"
  if not server_api_file.exists():
    logger.warning("plugin_loader [tools]: '%s' — server_api.py not found", plugin_name)
    return False

  try:
    module = _import_file(f"_plugin_tool_server_api_{plugin_name}", server_api_file)
  except Exception as exc:
    logger.warning("plugin_loader [tools]: '%s' — failed to import server_api.py: %s", plugin_name, exc)
    return False

  blueprint = getattr(module, "blueprint", None)
  if blueprint is None:
    logger.warning("plugin_loader [tools]: '%s' — server_api.py has no 'blueprint' variable", plugin_name)
    return False

  try:
    app.register_blueprint(blueprint)
  except Exception as exc:
    logger.warning("plugin_loader [tools]: '%s' — failed to register blueprint: %s", plugin_name, exc)
    return False

  # ---- Inject into tool_registry ----
  _inject_tool_registry(plugin_name, meta)

  registered_endpoints.add(endpoint)
  registered_tool_names.add(tool_name)

  _loaded.setdefault("tools", {})[plugin_name] = meta
  logger.info("plugin_loader [tools]: '%s' loaded  (endpoint=%s)", plugin_name, endpoint)
  return True


def _inject_tool_registry(plugin_name: str, meta: Dict[str, Any]) -> None:
  try:
    import tool_registry as _tr

    params_raw   = meta.get("params")   or {}
    optional_raw = meta.get("optional") or {}

    params: Dict[str, Any] = {}
    if isinstance(params_raw, dict):
      for k, v in params_raw.items():
        params[k] = v if isinstance(v, dict) else {"required": True}

    optional: Dict[str, Any] = {}
    if isinstance(optional_raw, dict):
      for k, v in optional_raw.items():
        optional[k] = v.get("default", "") if isinstance(v, dict) else v

    tool_name = str(meta["mcp_tool_name"])

    _tr.TOOLS[tool_name] = {  # type: ignore[attr-defined]
      "desc":          str(meta.get("description", plugin_name)),
      "endpoint":      str(meta["endpoint"]),
      "method":        "POST",
      "category":      str(meta.get("category", "plugin")),
      "params":        params,
      "optional":      optional,
      "effectiveness": float(meta.get("effectiveness", 0.5)),
    }

    try:
      from server_api.ops.system_monitoring import register_plugin_tool
      check = meta.get("check") or {}
      if not isinstance(check, dict):
        check = {}
      register_plugin_tool(tool_name, check, category=str(meta.get("category", "plugins")))
    except Exception as sm_exc:
      logger.warning(
        "plugin_loader: could not register '%s' as always-available: %s",
        tool_name, sm_exc,
      )

  except Exception as exc:
    logger.warning("plugin_loader: failed to inject '%s' into tool_registry: %s", plugin_name, exc)


# ---------------------------------------------------------------------------
# Type dispatch table  (extend here to support new plugin types)
# ---------------------------------------------------------------------------

# Each entry: plugin_type_key -> callable(app, name, reg_endpoints, reg_tools) -> bool
_TYPE_LOADERS: Dict[str, Any] = {
  "tools": _load_tool_plugin,
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def load_plugins(app) -> None:
  """Load all enabled plugins and register them with *app*.

  Called once from ``nyxstrike_server.py`` after ``register_blueprints(app)``.
  """
  global _loaded
  _loaded = {}

  if not _MANIFEST_FILE.exists():
    logger.debug("plugin_loader: no plugins/plugins.yaml found — skipping")
    return

  try:
    manifest = _load_yaml(_MANIFEST_FILE)
  except Exception as exc:
    logger.warning("plugin_loader: failed to read plugins.yaml: %s", exc)
    return

  registered_endpoints:   set = set()
  registered_tool_names:  set = set()
  total_loaded = 0

  for plugin_type, entries in manifest.items():
    if not isinstance(entries, list):
      continue

    loader_fn = _TYPE_LOADERS.get(plugin_type)
    if loader_fn is None:
      logger.warning("plugin_loader: unknown plugin type '%s' — skipping section", plugin_type)
      continue

    for entry in entries:
      if not isinstance(entry, dict):
        logger.warning("plugin_loader [%s]: unexpected entry %r — skipping", plugin_type, entry)
        continue

      name = entry.get("name", "").strip()
      if not name:
        logger.warning("plugin_loader [%s]: entry missing 'name' — skipping", plugin_type)
        continue

      enabled = str(entry.get("enabled", "true")).lower() not in ("false", "0", "no")
      if not enabled:
        continue

      ok = loader_fn(app, name, registered_endpoints, registered_tool_names)
      if ok:
        total_loaded += 1

  if total_loaded:
    summary = {pt: list(plugins.keys()) for pt, plugins in _loaded.items()}
    logger.info("plugin_loader: %d plugin(s) loaded — %s", total_loaded, summary)
  else:
    logger.debug("plugin_loader: no plugins were loaded")


# ---------------------------------------------------------------------------
# Public query API  (used by /api/plugins/list)
# ---------------------------------------------------------------------------

def get_plugin_list() -> List[Dict[str, Any]]:
  """Return a flat list of all successfully loaded plugins."""
  result = []
  for plugin_type, plugins in _loaded.items():
    for name, meta in plugins.items():
      result.append({
        "name":           name,
        "type":           plugin_type,
        "version":        meta.get("version", ""),
        "description":    meta.get("description", ""),
        "author":         meta.get("author", ""),
        "category":       meta.get("category", ""),
        "tags":           meta.get("tags", []),
        "endpoint":       meta.get("endpoint", ""),
        "mcp_tool_name":  meta.get("mcp_tool_name", ""),
        "effectiveness":  meta.get("effectiveness", 0.5),
        "enabled":        True,
      })
  return result


def get_plugins_by_category() -> Dict[str, List[Dict[str, Any]]]:
  """Return plugins grouped by their declared category."""
  by_cat: Dict[str, List[Dict[str, Any]]] = {}
  for plugin in get_plugin_list():
    cat = plugin.get("category", "uncategorized")
    by_cat.setdefault(cat, []).append(plugin)
  return by_cat


def get_plugins_by_type() -> Dict[str, List[Dict[str, Any]]]:
  """Return plugins grouped by plugin type (tools, workflows, …)."""
  by_type: Dict[str, List[Dict[str, Any]]] = {}
  for plugin in get_plugin_list():
    pt = plugin.get("type", "unknown")
    by_type.setdefault(pt, []).append(plugin)
  return by_type


def _import_file(module_name: str, path: Path):
  spec = importlib.util.spec_from_file_location(module_name, str(path))
  if spec is None or spec.loader is None:
    raise ImportError(f"Cannot create module spec for {path}")
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)  # type: ignore[union-attr]
  return module
