# Changelog

## 2.0.0 (NEXT)

## 1.9.0 (2026-08-20)

### Run page
- Boolean params (e.g. `exploit`, `dump_all`) now render as toggle switches instead of free-text true/false fields.

### Payload workbench
- New "Payload Workbench" — generate and test payloads (SQLi, XSS, etc.) without leaving the UI.

### HTTP framework
- `http_spider` now runs on the `commonhuman-core` crawler — threaded discovery, richer form parsing (select/hidden/required-field handling), and correct handling of redirects and off-origin filtering.
- New `http_authenticate` tool — logs the shared session into a target via form login, OAuth2 client-credentials, or Basic/Digest/NTLM, so subsequent `http_request`/`http_spider`/`http_intruder` calls run authenticated.
- New `js_api_discover` tool — extracts REST/JSON API endpoints straight out of a SPA's JavaScript bundles (React/Vue/Angular), catching `fetch`/`axios` calls a plain crawl never sees.
- New `source_map_recover` tool — recovers original pre-minified JS/TS source via `sourceMappingURL`/`.map` files, for real source instead of minified bundles when reviewing DOM-XSS sinks.
- New `ws_discover`/`ws_inject` tools — find WebSocket endpoints referenced in a page's HTML/JS, then send payloads over them and check responses for reflection (chat, real-time features).

### API scanning
- `api_schema_analyzer` now parses OpenAPI/Swagger specs (JSON or YAML, v2 or v3, `$ref`-resolving) via `commonhuman-core` instead of a bare JSON fetch — every endpoint comes back with a real, scannable URL (path params filled, base URL resolved) ready to hand to breachsql/phaseaccess.
- New `openapi_discover` tool — probes a target's common paths (`/openapi.json`, Swagger UI, ReDoc, ...) to locate its spec automatically.

### Recon
- New `dork_search` tool — queries DuckDuckGo/Bing/Yahoo for URLs matching a dork query (e.g. `site:target.com inurl:search`), returning only parameter-bearing candidates. No API keys required.

### Hardening
- Smart-scan now re-scores remaining tool candidates between small batches instead of committing to one fixed list up front, so a failure can down-rank a tool before the next round fires.
- Fixed a shared-driver race in the browser agent — concurrent requests now queue instead of racing on the same Selenium session.
- Harvested credentials are now encrypted at rest.
- Plugin loading now logs before executing third-party code, with an opt-in allowlist mode.

## 1.8.0 - exploitotter (2026-08-13)

### Workbench
- New "Workbench" page — local data-transform toolkit, no target or network required: 40+ operations spanning encoding, hashing, AES/RSA crypto, ciphers, compression, JWT/X.509/regex analysis, text utilities, networking calculators, and diff/compare. Chain operations into a recipe, piping one output into the next.
- Recipes save, load, and export/import as JSON; favorite, hide, and reorder operations and categories in the sidebar; binary/image output downloads straight to a file.

### Evidence chain-of-custody
- Every tool run is now hash-chained (tamper-evident), including one-off runs made outside any session.
- New "Verify" page — look up the exact run behind a given hash, or check any session's evidence chain by ID. Session reports also show integrity inline.

### Topology map
- Added a network topology map — export a completed nmap/nmap-advanced run to a live host/port graph, auto-creating a session if needed.
- Toggle on the Run page to auto-export scan results, plus manual "Export to Topology" buttons on the Run page and session tool runs.
- New "Topology" tab on the session detail page renders the graph.

### Dependencies
- Migrated Python dependency management from `dependencies/requirements*.txt` to `pyproject.toml` + `uv.lock`.

### Security & hardening
- Server now refuses to start if bound to a non-loopback host with no API token configured.
- Closed command-injection risk across ~35 tool builders — commands are now built as safely-quoted argv lists instead of raw string interpolation.
- Closed a Python source-injection risk in the Pwntools exploit generator.
- Added rate limiting to NyxStrike's own API.
- Fixed a race where concurrent browser-agent requests could stomp on the same Selenium driver.

## 1.7.0 - phishfalcon (2026-07-28)

### Navigation
- Replaced the top nav tab bar with a collapsible sidebar — icon-only rail on desktop (state persists across reloads), slide-out drawer on mobile.

### Themes
- Added new themes — Dracula, Rosé, and more.
- Every theme now has a subtle animated accent sweep across the top bar and sidebar edge, respecting the OS "reduce motion" setting.

### Intelligence
- The Decision Engine now weighs the current session's run history when scoring tools — a tool that just failed is deprioritized (not excluded) on the next recommendation.

### Run page & live output
- Run page tool execution now streams live output and progress instead of blocking silently until the command finishes.
- Fixed the process dashboard/stream showing a fake "Running for Xs" placeholder — `last_output` now carries the tool's real stdout/stderr, visible live on the Tasks page.
- Selecting a tool on the Run page now updates the URL to `#/run/<tool>` — bookmarkable/shareable, reopens straight into that tool with empty inputs (no params prefilled).

### Accessibility
- Added focus-trap keyboard navigation to the Command Palette and Chat widget.

### Error recovery
- Fixed `/api/error-handling/execute-with-recovery` raising a server error on every real call.
- Wired automatic error recovery (retry/backoff, alternative-tool swap) into recon, scanning, fuzzing, and forensics tool executions.

### Process pool
- Fixed `/api/process/execute-async` returning the cached result payload instead of a task ID on a cache hit, which broke polling it via `/api/process/get-task-result/<task_id>`.
- Fixed the process pool's worker auto-scaling miscounting active workers after scaling down.
- All tool command execution now runs through the process pool's auto-scaling (previously bypassed it); pooled task results no longer leak memory on long-running instances.

### Internals
- Migrated the entire tool registry to a unified `ToolSpec`-driven registration system, replacing legacy per-category registration code across all tool categories.

## 1.6.0 - injectlynx (2026-07-03)

### New tools
- Integrated `breachsql` — SQLi detection and exploitation across all major backends with boolean, time-blind, union, error, and OOB techniques; `--exploit` and `--dump` support.
- Integrated `stingxss` — context-aware XSS scanner covering reflected, DOM, stored, and blind XSS with WAF evasion, probe filtering, and headless browser confirmation.
- Integrated `phaseaccess` — IDOR/BOLA scanner with dual-session confirmed findings, JWT tampering, method bypass, and parameter pollution checks.
- Integrated `vaultrip` — post-exploitation credential harvesting across files, process memory, browsers, system keyrings, Kerberos caches, and offline dumps.

### Settings
- Added per-tool binary path overrides — configure custom executable paths per tool from the Settings UI with a live Test button that validates the path exists and is executable.
- Fixed `httpx` PATH resolution — falls back to system PATH when no override is set instead of erroring out.

### Performance
- Optimised `RunHistoryPanel` and `RunPage` rendering to reduce unnecessary re-renders on large run histories.

### Internals
- Tools using exit code 1 for "findings found" now report `✅ SUCCESS` in logs — no false failure noise.
- Added `FINDINGS_EXIT_CODE_TOOLS` checks it before logging and setting the success flag.

## 1.5.0 - backdoorbear (2026-05-09)

### Loot
- Added Loot page for managing captured credentials and loot items from engagements.
- Loot page is accessible from the nav and Command Palette.

### Reports
- Added HTML report generation endpoint for richer, exportable engagement reports.

### Plugin management
- Improved plugin management modal with enhanced plugin install/enable/disable UX.

### Settings & navigation
- Added page visibility controls — show or hide individual nav pages from Settings.
- Dashboard and Settings pages are always visible and cannot be disabled.

### Help page
- Added Command Palette section explaining shortcuts and tool launch workflow.
- Added UI Features section covering chat panel shortcut and page visibility.

## 1.4.0 - NyxStrike (2026-04-24)

### Built-in AI Chat assistant
- Added persistent chat widget — start a conversation without leaving your workflow. Supports multi-session history, and a resizable floating UI.
- Added chat personality settings and presets — tune the assistant's tone and behavior.
- Added chat session renaming, deletion, stats tracking.
- Added tool call resolution handling and streaming identifier improvements.
- Enabled "think" mode and reasoning support in LLM backends (Ollama, OpenAI, Anthropic).
- And a few smaller features build into the chat.

### LLM analysis
- Added `analyze_session` — passive LLM analysis pass that reads existing workflow session run logs, interprets them, and persists structured findings.
- Added `llm_agent_scan_result` tool — retrieve results of completed LLM agent scan sessions.
- Added `NyxStrikeDB` (SQLite) for persisting LLM analysis sessions and vulnerability findings.
- Added `LLMClient` — provider-agnostic LLM adapter supporting Ollama, OpenAI, and Anthropic backends.
- Added internal API client for tool execution and classification from the chat layer.
- Improved tool injection logic with confidence threshold and conversational pattern filtering.

### Session management
- Added follow-up session functionality — chain sessions for iterative engagements.
- Added session notes management, report generation, findings, and timeline view.
- Added AI analysis section surfacing vulnerabilities and risk level in session cards.

### Plugin system
- Introduced a drop-in plugin architecture — extend NyxStrike without touching core code.
- Drop a folder under `plugins/tools/`, add an entry to `plugins.yaml`, and restart; the server auto-loads the plugin.
- Each tool plugin provides a Flask Blueprint (API endpoint) and a FastMCP registration (AI-callable tool).
- Failed plugins are skipped with a warning — server always starts cleanly.
- Bundled `example_net_ping` plugin as a copy-paste starting point.

### New tools
- Added `schemathesis` integration — property-based API fuzzing against OpenAPI/GraphQL schemas.
- Added `interactsh` wrapper — OOB interaction URL generation for blind SSRF/XSS detection.
- Added `http_headers` tool — fetches and displays HTTP response headers for a target URL.
- Added `dig` tool — DNS lookup via `dig` with configurable record type and nameserver.
- Added Burp Agent Loop API for autonomous pentesting integration.

### Performance and internals
- Implemented thread-safe lazy singleton pattern for service objects.
- Optimized SSE endpoints with unified stream for processes and pool stats, reducing duplicate events.
- Added CPU niceness adjustment and performance dashboard recording to command execution.
- Configurable session wait time for Metasploit execution.
- Improved tool registry validation and cache key hashing.
- Added session-wide subprocess mocking safety net for tests.

### Others
- Added `nyxstrike.sh` main entrypoint script with external tool install list.

## 1.3.0 - shellshark (2026-04-09)
- Added new tools/wrappers: `hurl`, `waymore`, `assetfinder`, `shuffledns`, `massdns`, and `gospider`; also improved `testssl.sh` compatibility/fallback.
- Upgraded intelligence workflows with precision planning, preview mode, and tool selection reasons.
- Improved sessions and UI flows (template/workbench polish, log export, ESC-to-close modals, update modal with copyable `git pull`).
- Streamlined UI responsiveness and topbar UX: FAB quick actions and condensed health/refresh status via tooltip.
- Strengthened long-running execution with per-tool timeout policies, request/runtime timeout split, inactivity watchdog, and max runtime cap.
- Added streamlined installer workflow: split `install.sh`/`run.sh`.
- Manual Tool Execution: deep chaining prior-step artifact chaining with operator approval, confidence hints, and mapping pinning.
- Durable session workflow evolution: stronger end-to-end session handoff model between AI planning and manual dashboard execution.
- Theme system major upgrade: new premium themes (Unicorn + Forest), plus richer per-theme visual identity.

## 1.2.0 - packetpanther (2026-04-04)
- Added global command palette (`Ctrl/Cmd+K`) and plug-and-play theme system.
- Improved Run/Sessions workflows (favorites, recent targets, compare results, session template/workbench improvements).
- Moved run history to server-side persistence and polished dashboard/frontend structure.

## 1.1.2 - rootkitfox (2026-03-29)
- Refactored tool system internals (centralized constants, flatter probing, better detector logic for pip/gem/cargo).
- Added `/api/tools/categories` and dashboard helper cleanups for stronger frontend integration.
- Improved vulnerability-intelligence matching and wordlist store integration.

## 1.1.1 - Zerodaywolf (2026-03-26)
- Expanded reconnaissance/vuln tooling with `sherlock`, `spiderfoot`, `sublist3r`, `parsero`, `joomscan`, `whatweb`, `vulnx`, `ldapdomaindump`, and `commix`.
- Improved coverage for OSINT, web fingerprinting, CVE intelligence, and AD enumeration workflows.

## 1.1.0 - Major Features (2026-03-23)
- Introduced the built-in web dashboard (`http://localhost:8888`) with tool availability, reports, live KPIs, and logs.
- Expanded platform scale to 185+ MCP tools and added more multi-agent/skill workflows.
- Delivered major refactor/performance pass and improved operator control across run/registry/help surfaces.

## 1.0.12 (2026-03-15)
- Added 12 new tools and 9 new LLM skills.
- Updated docs for expanded toolset, async execution model, and newer Python compatibility/modes.

## 1.0.11 (2026-03-11)
- Added optional bearer auth (`NYXSTRIKE_API_TOKEN`) and MCP client auth/SSL flags (`--auth-token`, `--disable-ssl-verify`).
- Added `auto_install_missing_apt_tools` MCP flow for server-side tool installation.
- Improved deployment/security documentation and general cleanup.

## 1.0.10 (2026-02-25)
- Added `autopsy`, `aircrack-ng`, `theharvester`, and `exploit-db` integrations.
- Refactored tool registration/import flow for cleaner modularity and easier extension.

## 1.0.9 (2026-02-24)
- Added password-cracking tools: `hashid`, `patator`, `ophcrack`, `medusa`.
- Fixed `httpx` target flag handling.

## 1.0.8 (2026-02-23)
- Added MCP profile modes (`--profile`, `--compact`) and improved default tool profile behavior.
- Introduced `AGENTS.md` guidance and new config defaults (`DEFAULT_NYXSTRIKE_SERVER`, `MAX_RETRIES`).
- Refactored `nyxstrike_mcp.py` entrypoint to a much smaller modular structure.

## 1.0.7 (2026-02-21)
- Added wordlist management API (`wordlist_store`) with CRUD and best-match retrieval.
- Introduced `core/config_core.py` and metadata-driven wordlist configuration.
- Continued MCP modularization and docs improvements for compact mode/flags.

## 1.0.6 (2026-02-21)
- Added `bbot` integration (API endpoint, registry, MCP wrapper) and upgraded FastMCP v3.
- Centralized wordlist paths and removed hardcoded values across tool endpoints.
- Added `requirements-tools.txt` and improved install/dependency guidance.

## 1.0.5 (2026-02-18)
- Large internal refactor for process/resource management, telemetry, and caching architecture.
- Improved attack modeling and intelligent decision engine organization.
- Split/refined API modules and docs for maintainability.

## 1.0.4 (2026-02-15)
- Added database query tooling for MySQL, PostgreSQL, and SQLite.
- Improved CTF workflow internals and API-audit typing fixes.
- Added cache configuration knobs (`CACHE_SIZE`, `CACHE_TTL`).

## 1.0.3 (2026-02-14)
- Added `whois_lookup` tool and improved OpenCode integration/docs.
- Fixed payload naming bugs and removed duplicate tool definitions.
- Improved output rendering/extensibility in vulnerability/smart-scan flows.

## 1.0.2 (2026-02-13)
- Added foundational project standards (`.editorconfig`, `.gitattributes`, contributing/PR templates).
- Introduced central `config.py`, compact MCP mode, and secure file-ops module.
- Updated docs/README for clearer architecture and contributor onboarding.
