# Intelligence Tool Catalog

This document explains how to add new tools to the Intelligent Decision Engine
without touching planner internals.

## Overview

The planner is catalog-driven. Tool selection logic reads metadata from
`server_core/intelligence/tool_catalog.py` and scores each tool by:

- baseline effectiveness (plus contextual learning)
- objective fit
- target-type fit
- technology affinities
- noise/cost penalties (precision-first)

## Add a New Tool (Required steps)

1. Add a `ToolSpec` entry in `build_tool_catalog()`.
2. Add baseline effectiveness in `initialize_tool_effectiveness()` in
   `server_core/intelligence/decision_engine_constants.py` for relevant
   target types.
3. Include the tool in one or more attack pattern groups in
   `initialize_attack_patterns()` in
   `server_core/intelligence/decision_engine_constants.py`.
4. Include realistic values for:
   - `capabilities`
   - `target_types`
   - `objectives`
   - `tech_affinities`
   - `noise_score` (0.0 to 1.0)
5. (Recommended) Add a `TIME_ESTIMATES` entry in
   `server_core/intelligence/decision_engine_constants.py` for better ranking.
6. Run tests:

```bash
pytest tests/test_intelligence_precision_planner.py
```

## ToolSpec field guidance

- `name`: must match the dict key.
- `capabilities`: purpose tags used for coverage requirements.
  - examples: `surface`, `content_discovery`, `web_vulnerability`,
    `api_discovery`, `api_assessment`, `network_scan`, `smb_enum`,
    `binary_analysis`, `cloud_assessment`
- `target_types`: use values from `TargetType` enum.
- `objectives`: planner objective keys.
  - examples: `quick`, `comprehensive`, `stealth`, `api_security`,
    `internal_network_ad`, `intelligence`
- `tech_affinities`: optional technology values from `TechnologyStack`.
- `noise_score`: how noisy the tool is (higher means less preferred in
  precision/stealth scenarios).

## Validation

The catalog validator (`validate_tool_catalog`) enforces:

- non-empty capabilities/target_types/objectives
- valid `TargetType` values
- `noise_score` in `[0.0, 1.0]`
- spec key/name consistency

## Notes

- No planner algorithm code changes are needed for normal additions.
- If you skip effectiveness/pattern updates, the tool may validate but will be
  under-selected or not appear in attack chains.
- Add optional tests for objective-specific expectations when introducing
  specialized tools.
