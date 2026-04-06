# Changelog

## 1.3.0 - shellshark (next)
- Added smarter timeout handling for long-running tools: per-tool overrides, optional no hard timeout, inactivity watchdog, and 24h max runtime safety cap.
- Decoupled request timeout from command runtime timeout so heavy tools are less likely to fail from client-side timeout.
- Updated Run/Sessions/manual execution paths to honor extended timeout behavior consistently.

## 1.2.0 - packetpanther (2026-04-04)
- Introduced the `packetpanther` release line for broader platform improvements and release packaging updates.
- Added in-app update notification groundwork (version check surfaced in UI).
- Consolidated release stabilization for the 1.1.x tooling and dashboard foundation.

## 1.1.2 - rootkitfox (2026-03-29)
- Rootkitfox release focused on reliability and packaging consistency for the expanded 1.1.x toolset.
- Included maintenance-level fixes and quality improvements ahead of the 1.2.0 cycle.

## 1.1.1 - Zerodaywolf (2026-03-26)
- Added new security tools: `joomscan`, `parsero`, and `sublist3r`.
- Improved installation hints and tool/category alignment, including x8 install/check refinements.
- Refined dashboard/tool status behavior and parent/child tool status matching.

## 1.1.0 (2026-03-23)
- Major web dashboard expansion: dedicated Tasks, Tools, Reports, and Sessions pages.
- Added rich run-history UX: search, clear, export, rerun, and run-result modal workflows.
- Added SSE live streaming with polling fallback for dashboard/process/log surfaces.
- Improved tool experience: install-command copy, effectiveness tracking, registry modal polish, and category/health alignment.
- Added demo mode support and broad UI responsiveness/quality improvements.

## 1.0.12 (2026-03-15)
- Stabilization release with reliability-focused fixes.
- Prepared the codebase for the larger 1.1 dashboard/session/tooling expansion.

## 1.0.11 (2026-03-11)
- Hardening release for production-readiness improvements.
- Included reliability fixes and operational cleanup

## 1.0.10 (2026-02-25)
- Added service/tool check improvements including Metasploit detection correction.
- Patch release focused on tool availability accuracy and stability.

## 1.0.3 - 1.0.9 (2026-02-14 - 2026-02-24)
- Included incremental fixes and release packaging cleanup.
- Hardening of workflows
- Quality-Of-life fixes

## 1.0.2 (2026-02-13)
- Established the early baseline for Community Edition usability and docs.
- Improved CVE intelligence/exploitability flow and fixed key integration errors.
- Added broad installation/docs cleanup, tool discovery fixes, and initial UX polish.
