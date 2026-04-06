# Testing Matrix

Use this matrix to pick the smallest test set that still gives confidence.

## Fast path by change type

### Server endpoint only (`server_api/...`)

Run:

```bash
pytest tests/test_endpoints_exist.py
```

Optional (if intelligence endpoint changed):

```bash
pytest tests/test_endpoints_exist.py::TestIntelligence
```

---

### MCP wrapper only (`mcp_tools/...` / `mcp_core/tool_profiles.py`)

Run:

```bash
pytest tests/test_endpoints_exist.py
```

Reason: MCP wrappers call API routes; endpoint existence catches registration misses.

---

### Tool registry only (`tool_registry.py`)

Run:

```bash
pytest tests/test_endpoints_exist.py
```

And manually validate in UI/API if needed:

- `GET /api/tools`

---

### Intelligence planner/catalog changes

Run:

```bash
pytest tests/test_intelligence_precision_planner.py
```

If you touched API routes for intelligence too:

```bash
pytest tests/test_endpoints_exist.py::TestIntelligence
```

---

### UI changes only (`ui/src/...`)

Run:

```bash
npm --prefix ui run -s build
```

---

## Recommended full pre-PR check

```bash
pytest tests/test_intelligence_precision_planner.py
pytest tests/test_endpoints_exist.py
npm --prefix ui run -s build
```

---

## Common failures and likely causes

- `404` in endpoint tests:
  - blueprint not registered in `server_api/__init__.py`
  - route path typo in endpoint or registry
- tool visible but not callable via gateway:
  - missing/incorrect `tool_registry.py` entry
  - required `params` mismatch with endpoint expectations
- tool never selected by intelligence:
  - missing `ToolSpec` catalog entry
  - missing baseline in `initialize_tool_effectiveness()`
  - missing pattern inclusion in `initialize_attack_patterns()`
- UI session/intelligence flow broken:
  - objective values not aligned (`quick|comprehensive|stealth`)
  - endpoint changed but UI API client not updated
