# Naming and Schema Conventions

This document defines naming and payload conventions for tools and APIs.

## Endpoint naming

- Use lowercase paths with dashes where needed.
- Tool endpoints should follow:
  - `POST /api/tools/<category>/<tool-name>`
- Keep route names stable; prefer additive changes over renames.

Preferred format for new endpoints:

- `/api/tools/recon/subfinder`
- `/api/tools/web_scan/nikto`
- `/api/tools/net_scan/nmap`

Legacy endpoints like `/api/tools/httpx` still exist and are valid, but new tools
should use the category-prefixed route pattern.

Examples:

- `/api/tools/recon/subfinder`
- `/api/tools/net_lookup/whois`
- `/api/tools/smb_enum/enum4linux-ng`

## Blueprint naming

- Variable format: `api_<domain>_<tool>_bp`
- Blueprint key should be descriptive and unique.

Examples:

- `api_web_probe_httpx_bp`
- `api_net_lookup_whois_bp`

## MCP naming

- Register function format: `register_<tool>_tool(...)` (or existing local style)
- MCP tool function names should be descriptive and conflict-free.

Examples:

- `register_httpx_tool(...)` -> `httpx_probe(...)`
- `register_whois(...)` -> `whois_lookup(...)`

## Tool registry conventions (`tool_registry.py`)

Each tool entry should include:

- `desc`: concise one-line purpose
- `endpoint`: exact API path (leading slash)
- `method`: usually `POST`
- `category`: existing taxonomy where possible
- `params`: required params only
- `optional`: default values for optional params
- `effectiveness`: baseline float `0.0..1.0`

### Required/optional schema rules

- Put only required fields in `params`.
- Put defaults in `optional` (used by gateway `run_tool`).
- Match field names to endpoint payload exactly.
- Keep `endpoint` aligned to category-prefixed route where possible
  (for example `/api/tools/recon/subfinder`).

## API response schema (recommended)

For tool-like endpoints, return a consistent shape:

```json
{
  "success": true,
  "stdout": "...",
  "stderr": "",
  "return_code": 0,
  "timed_out": false,
  "partial_results": false,
  "execution_time": 0.12,
  "timestamp": "2026-01-01T00:00:00"
}
```

For errors:

```json
{
  "success": false,
  "error": "message",
  "stdout": "",
  "stderr": "details",
  "return_code": 1,
  "timed_out": false,
  "partial_results": false
}
```

Note: legacy endpoints may still return `output` instead of `stdout`. Prefer the
recommended schema for new endpoints.

## Intelligence planner naming

- Objective keys: `quick`, `comprehensive`, `stealth`, `api_security`, `internal_network_ad`, `intelligence`
- Keep tool names identical across:
  - `tool_registry.py`
  - intelligence catalog (`ToolSpec.name`)
  - attack patterns (`initialize_attack_patterns()`)
  - effectiveness map (`initialize_tool_effectiveness()`)

## Categories

Reuse existing categories when possible (examples):

- `network_recon`, `web_recon`, `web_vuln`, `api`, `osint`, `cloud`, `binary`, `forensics`, `intelligence`

Avoid creating a new category unless the tool truly does not fit existing groups.
