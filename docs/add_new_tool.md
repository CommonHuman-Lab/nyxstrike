# Add a New Tool to NyxStrike

This guide covers the full path for adding a new tool:

- Flask server endpoint (`/api/tools/...`)
- MCP tool wrapper (`@mcp.tool()`)
- Tool registry entry (`tool_registry.py`)
- Optional intelligence-planner integration

Related docs:

- `docs/add_new_tool_examples.md`
- `docs/testing_matrix.md`
- `docs/naming_and_schema_conventions.md`
- `docs/intelligence_tool_catalog.md`

## Architecture at a glance

1. **Server API route** executes the underlying binary or logic.
2. **MCP wrapper** calls that API route through `api_client.safe_post(...)`.
3. **Tool registry** exposes the tool to gateway flows (`classify_task` + `run_tool`).
4. **Tool profile** includes MCP wrapper in default/full profile groups.

---

## 1) Add the server endpoint

Create a module under `server_api/<category>/` (or extend an existing one).

For new tools, use category-prefixed routes:

- `POST /api/tools/<category>/<tool-name>`

Example pattern:

```python
from flask import Blueprint, request, jsonify
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)

api_web_scan_mytool_bp = Blueprint("api_web_scan_mytool", __name__)


@api_web_scan_mytool_bp.route("/api/tools/web_scan/mytool", methods=["POST"])
def run_mytool():
    start_time = time.time()
    try:
        data = request.get_json()
        if not data or "target" not in data:
            return jsonify({"error": "target is required", "success": False}), 400

        # Run tool logic here
        stdout = "..."

        return jsonify({
            "success": True,
            "stdout": stdout,
            "stderr": "",
            "return_code": 0,
            "timed_out": False,
            "partial_results": False,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}",
            "stdout": "",
            "stderr": str(e),
            "return_code": 1,
            "timed_out": False,
            "partial_results": False,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
        }), 500
```

### Register the blueprint

- Export blueprint from `server_api/<category>/__init__.py`.
- Register blueprint in `server_api/__init__.py` inside `register_blueprints(app)`.

---

## 2) Add the MCP tool wrapper

Create or extend a file in `mcp_tools/<category>/`.

Example pattern:

```python
import asyncio
from typing import Dict, Any


def register_mytool(mcp, api_client, logger):
    @mcp.tool()
    async def mytool(target: str, additional_args: str = "") -> Dict[str, Any]:
        """Run MyTool against a target."""
        payload = {
            "target": target,
            "additional_args": additional_args,
        }
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: api_client.safe_post("api/tools/web_scan/mytool", payload)
        )
```

### Register MCP profile loading

Add wrapper registration to `mcp_core/tool_profiles.py`:

- Put it in an existing profile (e.g. `web_scan`, `web_fuzz`, `recon`), or
- Add a new profile group and include it in `DEFAULT_PROFILE` if appropriate.

---

## 3) Add tool registry entry

Update `tool_registry.py` `TOOLS` dictionary:

```python
"mytool": {
    "desc": "One-line tool description",
    "endpoint": "/api/tools/web_scan/mytool",
    "method": "POST",
    "category": "web_recon",
    "params": {"target": {"required": True}},
    "optional": {"additional_args": ""},
    "effectiveness": 0.85,
},
```

Guidelines:

- `endpoint` must match the Flask route.
- Prefer category-prefixed endpoint paths for new tools.
- `params` = required fields for `run_tool` gateway validation.
- `optional` = defaults auto-filled by `run_tool`.
- `category` should match existing taxonomy when possible.

---

## 4) (Optional but recommended) Integrate with Intelligence Engine

If the tool should be auto-selected by intelligence workflows, also update:

1. `server_core/intelligence/tool_catalog.py`
   - Add `ToolSpec` entry (`capabilities`, `target_types`, `objectives`, `noise_score`, etc.)
2. `server_core/intelligence/decision_engine_constants.py`
   - Add baseline in `initialize_tool_effectiveness()`
   - Add to relevant `initialize_attack_patterns()` sequences
   - Add estimate to `TIME_ESTIMATES`
3. Run planner tests:

```bash
pytest tests/test_intelligence_precision_planner.py
```

See also: `docs/intelligence_tool_catalog.md`.

---

## 5) Endpoint and route sanity checks

At minimum run:

```bash
pytest tests/test_endpoints_exist.py
```

If you added intelligence behavior, also run:

```bash
pytest tests/test_intelligence_precision_planner.py
```

---

## 6) Common checklist (copy/paste)

- [ ] Flask route implemented under `server_api/...`
- [ ] Blueprint exported and registered in `server_api/__init__.py`
- [ ] MCP wrapper added under `mcp_tools/...`
- [ ] MCP wrapper registered via `mcp_core/tool_profiles.py`
- [ ] `tool_registry.py` entry added/updated
- [ ] (If needed) intelligence catalog/effectiveness/patterns/time updated
- [ ] Endpoint test(s) pass
- [ ] Planner test(s) pass (if intelligence integration)
