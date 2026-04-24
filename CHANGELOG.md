# Changelog

## 1.4.0 - NyxStrike

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

## 1.3.0 - shellshark
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
