# Report Generator (`report.sh`)

Generates structured Markdown engagement reports from NyxStrike session data.
Reports are written to `scripts/reports/` and cover all session fields: findings
by severity, tools executed, workflow steps, and a full event timeline.

---

## Requirements

- **jq** (preferred) — `sudo apt install jq`
- **python3** — used as automatic fallback if `jq` is not installed
- At least one completed or active NyxStrike session in `.nyxstrike_data/sessions/`

The script exits cleanly with a message if neither `jq` nor `python3` is available.

---

## Usage

```bash
./scripts/report.sh                    # Report for the most recently updated session
./scripts/report.sh list               # Table of all sessions
./scripts/report.sh <session_id>       # Report for a specific session ID
./scripts/report.sh all                # Generate reports for every session
./scripts/report.sh help               # Show usage
```

### Short IDs

You can use a prefix of the session ID instead of the full string:

```bash
./scripts/report.sh sess_a4           # matches sess_a4175c6c92
```

---

## Output

Reports are written to:

```
scripts/reports/<session_id>_report_<YYYYMMDD>.md
```

Example:

```
scripts/reports/sess_a4175c6c92_report_20260428.md
```

---

## Report Structure

Each generated report contains the following sections:

### Session Info

Metadata table with session ID, target, objective, status, risk level, and timestamps.

### Executive Summary

Finding counts grouped by severity (Critical / High / Medium / Low / Info) and a
total count of tools executed.

### Findings

One sub-section per severity level that contains findings. Each finding is rendered
as a table row:

| Title | Tool | CVE | Status | Tags |

Severity groups are rendered in order: Critical → High → Medium → Low → Info.
Empty severity groups are omitted.

### Tools Executed

Bulleted list of all tools recorded in `tools_executed`.

### Workflow Steps

Table of planned workflow steps with parameters, expected outcome, and estimated
execution time.

### Timeline

Chronological table of all entries in `event_log`, with human-readable timestamps
(UTC).

---

## Data Source

Reports are built entirely from:

```
.nyxstrike_data/sessions/<session_id>/session.json
```

The data directory is resolved in this order:

1. `$NYXSTRIKE_DATA_DIR` environment variable (if set)
2. `.nyxstrike_data/` relative to the repository root (default)

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NYXSTRIKE_DATA_DIR` | `<repo_root>/.nyxstrike_data` | Override the NyxStrike data directory |

---

## Examples

```bash
# Quick report for the latest session
./scripts/report.sh

# List all sessions to find a session ID
./scripts/report.sh list

# Report for a specific session
./scripts/report.sh sess_a4175c6c92

# Batch — generate all reports at once
./scripts/report.sh all
```
