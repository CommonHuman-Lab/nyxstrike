# Add New Tool: Practical Examples

This page gives copy-friendly examples using existing, simple tools from this
repo.

Use this together with:

- `docs/add_new_tool.md`
- `docs/intelligence_tool_catalog.md`

---

## Example A: Simple lookup tool (`whois`)

### 1) Server endpoint

File: `server_api/net_lookup/whois.py`

- Route: `POST /api/tools/whois` (legacy flat route)
- Required input: `target`
- Returns JSON (currently `success` + `output`)

### 2) Blueprint registration

File: `server_api/__init__.py`

- Blueprint object exists: `api_net_lookup_whois_bp`
- Registered in `register_blueprints(app)`

### 3) MCP wrapper

File: `mcp_tools/net_lookup/whois.py`

- Register function: `register_whois(...)`
- MCP tool function: `whois_lookup(target: str)`
- Calls: `api_client.safe_post("api/tools/whois", {"target": target})`

### 4) Profile loading

File: `mcp_core/tool_profiles.py`

- `register_whois(...)` is in profile `net_lookup`
- `net_lookup` is included in `DEFAULT_PROFILE`

### 5) Tool registry

File: `tool_registry.py`

- Entry key: `"whois"`
- Endpoint: `"/api/tools/whois"`
- Category: `"osint"`

---

## Example B: Probe tool (`httpx`)

### 1) Server endpoint

File: `server_api/web_probe/httpx.py`

- Route: `POST /api/tools/httpx` (legacy flat route)
- Required input: `target`
- Optional inputs: `probe`, `tech_detect`, `status_code`, `title`, etc.

### 2) Blueprint registration

File: `server_api/__init__.py`

- Blueprint object: `api_web_probe_httpx_bp`
- Registered in `register_blueprints(app)`

### 3) MCP wrapper

File: `mcp_tools/web_probe/httpx.py`

- Register function: `register_httpx_tool(...)`
- MCP tool: `httpx_probe(...)`
- Calls API: `api/tools/httpx`

### 4) Profile loading

File: `mcp_core/tool_profiles.py`

- `register_httpx_tool(...)` in `web_probe` profile
- `web_probe` included in `DEFAULT_PROFILE`

### 5) Tool registry

File: `tool_registry.py`

- Entry key: `"httpx"`
- Endpoint: `"/api/tools/httpx"`
- Required param in schema: `target`

## For new tools, prefer category-prefixed routes

Existing tools in this repo include legacy flat endpoints (for compatibility).
When adding new tools, use:

- `POST /api/tools/<category>/<tool-name>`

Example:

- `POST /api/tools/web_scan/mytool`

---

## Optional Example C: Make the tool selectable by Intelligence Engine

If your new tool should be picked by intelligent attack-chain planning:

1. Add `ToolSpec` in `server_core/intelligence/tool_catalog.py`
2. Add baseline effectiveness in `server_core/intelligence/decision_engine_constants.py`
3. Add tool to relevant attack patterns in `server_core/intelligence/decision_engine_constants.py`
4. Add `TIME_ESTIMATES` entry in `server_core/intelligence/decision_engine_constants.py`

Then run:

```bash
pytest tests/test_intelligence_precision_planner.py
```

---

## Quick anti-miss checklist

- Server route exists and returns JSON
- Blueprint exported + registered
- MCP tool function added and wired to endpoint
- Profile includes the new MCP register function
- `tool_registry.py` has a matching entry
- Endpoint existence test passes
