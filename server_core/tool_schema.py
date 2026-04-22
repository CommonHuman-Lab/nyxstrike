"""
server_core/tool_schema.py

Converts NyxStrike tool_registry entries into Ollama/OpenAI function-calling
tool schemas.

The registry is already categorised and effectiveness-sorted.  This module
provides one entry point used by the chat layer:

  build_tool_schemas(tools) -> List[dict]

Where ``tools`` is the list returned by ``get_tools_for_category()`` or a
hand-picked subset.  The output is ready to pass directly as the ``tools``
argument to ``LLMClient.chat()``.
"""

from typing import Any, Dict, List


# Parameter type hints: registry values look like "REQUIRED" or "default=X".
# We map them to JSON-schema "string" by default; numeric defaults get "number".
def _infer_type(default_value: Any) -> str:
  if isinstance(default_value, bool):
    return "boolean"
  if isinstance(default_value, int):
    return "number"
  if isinstance(default_value, float):
    return "number"
  return "string"


def _registry_entry_to_schema(name: str, tool_def: Dict[str, Any]) -> Dict[str, Any]:
  """Convert a single full registry entry (from TOOLS dict) into an Ollama tool schema."""
  properties: Dict[str, Any] = {}
  required: List[str] = []

  # Required params (params dict — keys are param names, values are {required:True} or similar)
  for param_name, param_meta in tool_def.get("params", {}).items():
    properties[param_name] = {"type": "string", "description": f"{param_name} (required)"}
    required.append(param_name)

  # Optional params (optional dict — keys are param names, values are defaults)
  for param_name, default_val in tool_def.get("optional", {}).items():
    param_type = _infer_type(default_val)
    desc = f"{param_name} (optional, default: {default_val!r})"
    properties[param_name] = {"type": param_type, "description": desc}

  return {
    "type": "function",
    "function": {
      "name": name,
      "description": tool_def.get("desc", ""),
      "parameters": {
        "type": "object",
        "properties": properties,
        "required": required,
      },
    },
  }


def build_tool_schemas(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
  """Convert a list of compact registry tool dicts into Ollama tool schemas.

  Each item in ``tools`` is the shape returned by ``get_tools_for_category()``:
    {"name": str, "desc": str, "endpoint": str, "method": str, "params": dict}

  The ``params`` dict here already has the combined required + optional view
  from get_tools_for_category (values are "REQUIRED" or "default=X" strings).
  We reconstruct required/optional from that.

  Args:
    tools: List of compact tool dicts from get_tools_for_category().

  Returns:
    List of Ollama-compatible tool schema dicts.
  """
  schemas = []
  for t in tools:
    name = t.get("name", "")
    desc = t.get("desc", "")
    params_compact = t.get("params", {})

    properties: Dict[str, Any] = {}
    required: List[str] = []

    for param_name, param_val in params_compact.items():
      if param_val == "REQUIRED":
        properties[param_name] = {"type": "string", "description": f"{param_name} (required)"}
        required.append(param_name)
      else:
        # "default=X" string — extract default for description
        default_str = str(param_val).replace("default=", "", 1) if str(param_val).startswith("default=") else str(param_val)
        properties[param_name] = {
          "type": "string",
          "description": f"{param_name} (optional, default: {default_str})",
        }

    schemas.append({
      "type": "function",
      "function": {
        "name": name,
        "description": desc,
        "parameters": {
          "type": "object",
          "properties": properties,
          "required": required,
        },
      },
    })

  return schemas
