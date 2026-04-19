# AGENTS.md

## Guidance for agentic coding assistants working in this repository

## Quick orientation

- Project: NyxStrike (Python 3.13+)
- Primary entrypoints: `nyxstrike_server.py`, `nyxstrike_mcp.py`
- Config helpers: `config.py`, `core/config_core.py`
- Tools registry: `tool_registry.py`
- Tests directory exists but is currently empty of test modules.

## Build, lint, test commands

### Environment setup

```bash
python3 -m venv nyxstrike-env
source nyxstrike-env/bin/activate
python3 -m pip install -r requirements.txt
```

### Run the server

```bash
python3 nyxstrike_server.py
```

### Run the MCP client

```bash
nyxstrike-env/bin/python3 nyxstrike_mcp.py --server http://localhost:8888
```

### Tests

This repo appears to use pytest (there is a `.pytest_cache`), but no test files are
present under `tests/` right now. If you add tests, prefer pytest.

Run all tests (if any are added):

```bash
pytest
```

Run a single test file:

```bash
pytest tests/path/to/test_file.py
```

Run a single test function:

```bash
pytest tests/path/to/test_file.py::test_function_name
```

Run a single test class method:

```bash
pytest tests/path/to/test_file.py::TestClassName::test_method_name
```

### Lint/format

No explicit lint/format configuration was found (no `pyproject.toml`, `setup.cfg`,
or `tox.ini`). Do not introduce auto-format-only changes unless requested.

If you add a linter, follow existing conventions and keep diffs scoped.

## Code style guidelines

### General conventions

- Follow existing patterns and keep changes minimal.
- Avoid large formatting-only diffs.
- Keep PRs small and focused (see `.github/CONTRIBUTING.md`).

### Indentation and whitespace

- `.editorconfig` specifies: spaces, 2-space indent, LF, final newline.
- Respect existing files even if they deviate (avoid reformatting).

### Imports

- Prefer standard ordering: stdlib, third-party, local modules.
- Use explicit imports for project modules (e.g., `from core import ...`).
- Keep import lists stable; do not reorder for style only.

### Typing

- Use type hints on public functions and significant internal APIs.
- Prefer `Dict[str, Any]`, `Optional[T]`, and dataclasses where already used.
- Keep typing consistent with existing style in the file you edit.

### Naming

- Modules/files: `snake_case.py`.
- Classes: `PascalCase`.
- Functions/variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Use descriptive names for tools and endpoints (see `mcp_tools/*`).

### Logging and errors

- Prefer the `logging` module; reuse existing loggers in each module.
- Follow existing patterns for structured error returns, e.g.
  `{"error": "message", "success": False}`.
- When integrating tool execution, surface recovery or escalation info if present.

### API and tool patterns

- Gateway tools are registered via `mcp.tool()` decorators (see `mcp_tools/gateway.py`).
- When calling tools, validate required params and fill defaults like existing logic.
- When adding tools, keep signature docstrings short and consistent.

### Configuration

- Read config values via `core.config_core.get(key, default)`.
- Avoid hard-coding wordlist paths; use `config_core.get_word_list_path(...)`.

### External tools

- Many security tools are external and not installed via pip.
- If you add new tool integrations, document required binaries and parameters.

## Contribution guidelines (from repo docs)

- Keep PRs focused; avoid unrelated formatting changes.
- Prefer PRs under 300 changed lines; avoid exceeding 500 lines.
- Use clear commit messages: `type: short description`.
- Branch naming: `feature/...`, `fix/...`, `docs/...`, `refactor/...`.
- AI assistance is allowed but must be reviewed and tested.

## Repo-specific notes

- Server binds to `127.0.0.1` by default; override via `NYXSTRIKE_HOST`.
- API token: set `NYXSTRIKE_API_TOKEN` to enable bearer auth.
- Default API port: `NYXSTRIKE_PORT` (default 8888).
- Command timeouts: `COMMAND_TIMEOUT` in config.

## Intelligence planner

- The Intelligent Decision Engine is catalog-driven.
- Add or tune tool behavior in `server_core/intelligence/tool_catalog.py`.
- Use `docs/intelligence_tool_catalog.md` for the add-tool workflow.
- Run planner tests when modifying catalog/scoring:

```bash
pytest tests/test_intelligence_precision_planner.py
```

## When in doubt

- Mirror the style of the file you are editing.
- Keep diffs minimal and avoid global refactors.
- Prefer adding tests when adding new logic, even if the suite is small.
