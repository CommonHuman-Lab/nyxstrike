#!/usr/bin/env bash
# =============================================================================
# NyxStrike Report Generator
# Build a Markdown engagement report from a NyxStrike session JSON file
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DATA_DIR="${NYXSTRIKE_DATA_DIR:-${REPO_ROOT}/.nyxstrike_data}"
SESSIONS_DIR="${DATA_DIR}/sessions"
REPORTS_DIR="${SCRIPT_DIR}/reports"

# ---------------- colours / output helpers -----------------------------------
RED='\033[0;31m'
GREEN='\033[38;5;46m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
BOLD='\033[1m'
RESET='\033[0m'

good()   { echo -e "\t${GREEN}[+]${RESET} $*"; }
bad()    { echo -e "\t${RED}[-]${RESET} $*"; }
info()   { echo -e "\t${GRAY}[*]${RESET} $*"; }
warn()   { echo -e "\t${YELLOW}[!]${RESET} $*"; }
header() { echo -e "\n${GREEN}${BOLD}$*${RESET}"; }

# ---------------- banner -----------------------------------------------------
banner() {
  echo ""
  echo -e "${GREEN}${BOLD}"
  echo "  ███╗   ██╗██╗   ██╗██╗  ██╗███████╗████████╗██████╗ ██╗██╗  ██╗███████╗"
  echo "  ████╗  ██║╚██╗ ██╔╝╚██╗██╔╝██╔════╝╚══██╔══╝██╔══██╗██║██║ ██╔╝██╔════╝"
  echo "  ██╔██╗ ██║ ╚████╔╝  ╚███╔╝ ███████╗   ██║   ██████╔╝██║█████╔╝ █████╗  "
  echo "  ██║╚██╗██║  ╚██╔╝   ██╔██╗ ╚════██║   ██║   ██╔══██╗██║██╔═██╗ ██╔══╝  "
  echo "  ██║ ╚████║   ██║   ██╔╝ ██╗███████║   ██║   ██║  ██║██║██║  ██╗███████╗"
  echo "  ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝"
  echo -e "${RESET}"
  echo -e "  ${BOLD}Report Generator${RESET} — Markdown engagement reports from session data"
  echo ""
}

# ---------------- JSON helper ------------------------------------------------
# Use jq if available, fall back to python3, exit if neither present
JSON_BACKEND=""

detect_json_backend() {
  if command -v jq &>/dev/null; then
    JSON_BACKEND="jq"
  elif command -v python3 &>/dev/null && python3 -c "import json" &>/dev/null 2>&1; then
    JSON_BACKEND="python3"
  else
    bad "Neither jq nor python3 found — one is required to parse session data."
    bad "Install jq:     sudo apt install jq"
    bad "Install python: https://www.python.org/downloads/"
    exit 1
  fi
  info "JSON backend: ${JSON_BACKEND}"
}

# jq_or_py <jq_filter> <py_expr> <json_file>
# py_expr receives the parsed dict as variable 'd'
jq_or_py() {
  local jq_filter="$1"
  local py_expr="$2"
  local json_file="$3"

  if [[ "$JSON_BACKEND" == "jq" ]]; then
    jq -r "$jq_filter" "$json_file" 2>/dev/null || true
  else
    python3 - "$json_file" <<PYEOF 2>/dev/null || true
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
result = (lambda d: $py_expr)(d)
if isinstance(result, list):
    for item in result:
        print(item if item is not None else "")
elif result is not None:
    print(result)
PYEOF
  fi
}

# ---------------- session discovery ------------------------------------------
list_sessions() {
  header "Available Sessions"
  echo ""
  printf "  ${BOLD}%-26s %-30s %-10s %-10s %s${RESET}\n" "SESSION ID" "TARGET" "STATUS" "FINDINGS" "UPDATED"
  echo "  ─────────────────────────────────────────────────────────────────────────────────"

  local found=0
  for session_file in "${SESSIONS_DIR}"/*/session.json; do
    [[ -f "$session_file" ]] || continue
    found=1

    local sid target status findings updated
    sid=$(jq_or_py '.session_id // "unknown"' 'd.get("session_id","unknown")' "$session_file")
    target=$(jq_or_py '.target // "unknown"' 'd.get("target","unknown")' "$session_file")
    status=$(jq_or_py '.status // "unknown"' 'd.get("status","unknown")' "$session_file")
    findings=$(jq_or_py '.total_findings // 0' 'd.get("total_findings",0)' "$session_file")
    updated=$(jq_or_py '.updated_at // 0' 'd.get("updated_at",0)' "$session_file")

    # convert epoch to human date
    local updated_fmt
    updated_fmt=$(date -d "@${updated}" '+%Y-%m-%d %H:%M' 2>/dev/null || date -r "${updated}" '+%Y-%m-%d %H:%M' 2>/dev/null || echo "$updated")

    printf "  ${GREEN}%-26s${RESET} %-30s %-10s %-10s %s\n" \
      "$sid" "$target" "$status" "$findings" "$updated_fmt"
  done

  if [[ $found -eq 0 ]]; then
    info "No sessions found in ${SESSIONS_DIR}"
  fi
  echo ""
}

# Pick the session with the highest updated_at timestamp
latest_session() {
  local latest_file="" latest_ts=0
  for session_file in "${SESSIONS_DIR}"/*/session.json; do
    [[ -f "$session_file" ]] || continue
    local ts
    ts=$(jq_or_py '.updated_at // 0' 'd.get("updated_at",0)' "$session_file")
    if [[ "$ts" -gt "$latest_ts" ]] 2>/dev/null; then
      latest_ts="$ts"
      latest_file="$session_file"
    fi
  done
  echo "$latest_file"
}

# Resolve a session ID to its JSON file path
resolve_session() {
  local sid="$1"
  # exact directory match
  local exact="${SESSIONS_DIR}/${sid}/session.json"
  if [[ -f "$exact" ]]; then
    echo "$exact"
    return
  fi
  # prefix match (allow short IDs)
  for session_file in "${SESSIONS_DIR}"/*/session.json; do
    [[ -f "$session_file" ]] || continue
    local dir_name
    dir_name=$(basename "$(dirname "$session_file")")
    if [[ "$dir_name" == "${sid}"* ]]; then
      echo "$session_file"
      return
    fi
  done
  echo ""
}

# ---------------- report renderer --------------------------------------------
render_report() {
  local session_file="$1"
  local out_file="$2"

  info "Reading: ${session_file}"

  # --- pull scalar fields ---
  local sid target status objective risk findings_count created updated
  sid=$(jq_or_py       '.session_id // "unknown"'     'd.get("session_id","unknown")'     "$session_file")
  target=$(jq_or_py    '.target // "unknown"'          'd.get("target","unknown")'          "$session_file")
  status=$(jq_or_py    '.status // "unknown"'          'd.get("status","unknown")'          "$session_file")
  objective=$(jq_or_py '.objective // ""'              'd.get("objective","")'              "$session_file")
  risk=$(jq_or_py      '.risk_level // "unknown"'      'd.get("risk_level","unknown")'      "$session_file")
  findings_count=$(jq_or_py '.total_findings // 0'     'd.get("total_findings",0)'          "$session_file")
  created=$(jq_or_py   '.created_at // 0'              'd.get("created_at",0)'              "$session_file")
  updated=$(jq_or_py   '.updated_at // 0'              'd.get("updated_at",0)'              "$session_file")

  local created_fmt updated_fmt report_date
  created_fmt=$(date -d "@${created}" '+%Y-%m-%d %H:%M UTC' 2>/dev/null || date -r "${created}" '+%Y-%m-%d %H:%M UTC' 2>/dev/null || echo "$created")
  updated_fmt=$(date -d "@${updated}" '+%Y-%m-%d %H:%M UTC' 2>/dev/null || date -r "${updated}" '+%Y-%m-%d %H:%M UTC' 2>/dev/null || echo "$updated")
  report_date=$(date '+%Y-%m-%d')

  mkdir -p "$(dirname "$out_file")"

  # --- begin writing report ---
  {
    echo "# Engagement Report — ${target}"
    echo ""
    echo "> Generated by NyxStrike Report Generator on ${report_date}"
    echo ""
    echo "---"
    echo ""

    # ---- metadata table ----
    echo "## Session Info"
    echo ""
    echo "| Field | Value |"
    echo "|-------|-------|"
    echo "| **Session ID** | \`${sid}\` |"
    echo "| **Target** | \`${target}\` |"
    echo "| **Objective** | ${objective} |"
    echo "| **Status** | ${status} |"
    echo "| **Risk Level** | ${risk} |"
    echo "| **Created** | ${created_fmt} |"
    echo "| **Last Updated** | ${updated_fmt} |"
    echo ""

    # ---- executive summary ----
    echo "---"
    echo ""
    echo "## Executive Summary"
    echo ""

    # severity counts
    local crit high med low info_count
    if [[ "$JSON_BACKEND" == "jq" ]]; then
      crit=$(jq '[.findings[]? | select(.severity=="critical")] | length' "$session_file" 2>/dev/null || echo 0)
      high=$(jq '[.findings[]? | select(.severity=="high")]     | length' "$session_file" 2>/dev/null || echo 0)
      med=$(jq  '[.findings[]? | select(.severity=="medium")]   | length' "$session_file" 2>/dev/null || echo 0)
      low=$(jq  '[.findings[]? | select(.severity=="low")]      | length' "$session_file" 2>/dev/null || echo 0)
      info_count=$(jq '[.findings[]? | select(.severity=="info")] | length' "$session_file" 2>/dev/null || echo 0)
    else
      crit=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || echo 0
import json,sys
d=json.load(open(sys.argv[1]))
print(sum(1 for f in d.get("findings",[]) if f.get("severity")=="critical"))
PYEOF
)
      high=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || echo 0
import json,sys
d=json.load(open(sys.argv[1]))
print(sum(1 for f in d.get("findings",[]) if f.get("severity")=="high"))
PYEOF
)
      med=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || echo 0
import json,sys
d=json.load(open(sys.argv[1]))
print(sum(1 for f in d.get("findings",[]) if f.get("severity")=="medium"))
PYEOF
)
      low=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || echo 0
import json,sys
d=json.load(open(sys.argv[1]))
print(sum(1 for f in d.get("findings",[]) if f.get("severity")=="low"))
PYEOF
)
      info_count=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || echo 0
import json,sys
d=json.load(open(sys.argv[1]))
print(sum(1 for f in d.get("findings",[]) if f.get("severity")=="info"))
PYEOF
)
    fi

    local tools_count
    if [[ "$JSON_BACKEND" == "jq" ]]; then
      tools_count=$(jq '.tools_executed | length' "$session_file" 2>/dev/null || echo 0)
    else
      tools_count=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || echo 0
import json,sys
d=json.load(open(sys.argv[1]))
print(len(d.get("tools_executed",[])))
PYEOF
)
    fi

    echo "| Severity | Count |"
    echo "|----------|-------|"
    echo "| 🔴 Critical | ${crit} |"
    echo "| 🟠 High | ${high} |"
    echo "| 🟡 Medium | ${med} |"
    echo "| 🔵 Low | ${low} |"
    echo "| ⚪ Info | ${info_count} |"
    echo "| **Total** | **${findings_count}** |"
    echo ""
    echo "**Tools executed:** ${tools_count}"
    echo ""

    # ---- findings ----
    echo "---"
    echo ""
    echo "## Findings"
    echo ""

    local has_findings=0

    for severity in critical high medium low info; do
      local label
      case "$severity" in
        critical) label="🔴 Critical" ;;
        high)     label="🟠 High" ;;
        medium)   label="🟡 Medium" ;;
        low)      label="🔵 Low" ;;
        info)     label="⚪ Info" ;;
      esac

      local sev_findings
      if [[ "$JSON_BACKEND" == "jq" ]]; then
        sev_findings=$(jq -r \
          --arg sev "$severity" \
          '.findings[]? | select(.severity==$sev) | [.title//"", .tool//"", .cve//"", .status//"", (.tags//[]|join(", "))] | @tsv' \
          "$session_file" 2>/dev/null || true)
      else
        sev_findings=$(python3 - "$session_file" "$severity" <<'PYEOF' 2>/dev/null || true)
import json,sys
d=json.load(open(sys.argv[1]))
sev=sys.argv[2]
for f in d.get("findings",[]):
    if f.get("severity")==sev:
        tags=", ".join(f.get("tags",[]))
        print("\t".join([f.get("title",""), f.get("tool",""), f.get("cve",""), f.get("status",""), tags]))
PYEOF
      fi

      [[ -z "$sev_findings" ]] && continue
      has_findings=1

      echo "### ${label}"
      echo ""
      echo "| Title | Tool | CVE | Status | Tags |"
      echo "|-------|------|-----|--------|------|"

      while IFS=$'\t' read -r title tool cve fstatus tags; do
        echo "| ${title} | ${tool} | ${cve:-—} | ${fstatus} | ${tags:-—} |"
      done <<< "$sev_findings"
      echo ""
    done

    if [[ $has_findings -eq 0 ]]; then
      echo "_No findings recorded for this session._"
      echo ""
    fi

    # ---- tools executed ----
    echo "---"
    echo ""
    echo "## Tools Executed"
    echo ""

    local tools_list
    if [[ "$JSON_BACKEND" == "jq" ]]; then
      tools_list=$(jq -r '.tools_executed[]?' "$session_file" 2>/dev/null || true)
    else
      tools_list=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || true
import json,sys
d=json.load(open(sys.argv[1]))
for t in d.get("tools_executed",[]):
    print(t)
PYEOF
)
    fi

    if [[ -n "$tools_list" ]]; then
      while IFS= read -r tool; do
        echo "- \`${tool}\`"
      done <<< "$tools_list"
    else
      echo "_No tools recorded._"
    fi
    echo ""

    # ---- workflow steps ----
    echo "---"
    echo ""
    echo "## Workflow Steps"
    echo ""

    local steps
    if [[ "$JSON_BACKEND" == "jq" ]]; then
      steps=$(jq -r '.workflow_steps[]? | [.tool//"", (.parameters//{}|to_entries|map(.key+"="+(.value|tostring))|join(", ")), .expected_outcome//"", (.execution_time_estimate//0|tostring)+"s"] | @tsv' \
        "$session_file" 2>/dev/null || true)
    else
      steps=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || true
import json,sys
d=json.load(open(sys.argv[1]))
for s in d.get("workflow_steps",[]):
    params=", ".join(f"{k}={v}" for k,v in s.get("parameters",{}).items())
    outcome=s.get("expected_outcome","")
    etime=str(s.get("execution_time_estimate",0))+"s"
    print("\t".join([s.get("tool",""), params, outcome, etime]))
PYEOF
)
    fi

    if [[ -n "$steps" ]]; then
      echo "| Tool | Parameters | Expected Outcome | Est. Time |"
      echo "|------|------------|-----------------|-----------|"
      while IFS=$'\t' read -r tool params outcome etime; do
        echo "| \`${tool}\` | ${params} | ${outcome} | ${etime} |"
      done <<< "$steps"
    else
      echo "_No workflow steps recorded._"
    fi
    echo ""

    # ---- timeline ----
    echo "---"
    echo ""
    echo "## Timeline"
    echo ""

    local events
    if [[ "$JSON_BACKEND" == "jq" ]]; then
      events=$(jq -r '.event_log[]? | [(.timestamp|tostring), .type//"", .message//""] | @tsv' \
        "$session_file" 2>/dev/null || true)
    else
      events=$(python3 - "$session_file" <<'PYEOF' 2>/dev/null || true
import json,sys
d=json.load(open(sys.argv[1]))
for e in d.get("event_log",[]):
    print("\t".join([str(e.get("timestamp",0)), e.get("type",""), e.get("message","")]))
PYEOF
)
    fi

    if [[ -n "$events" ]]; then
      echo "| Timestamp | Event | Message |"
      echo "|-----------|-------|---------|"
      while IFS=$'\t' read -r ts etype msg; do
        local ts_fmt
        ts_fmt=$(date -d "@${ts}" '+%Y-%m-%d %H:%M UTC' 2>/dev/null \
               || date -r "${ts}" '+%Y-%m-%d %H:%M UTC' 2>/dev/null \
               || echo "$ts")
        echo "| ${ts_fmt} | \`${etype}\` | ${msg} |"
      done <<< "$events"
    else
      echo "_No events recorded._"
    fi
    echo ""

    echo "---"
    echo ""
    echo "_Report generated by [NyxStrike](https://github.com/CommonHuman-Lab/nyxstrike) on ${report_date}_"

  } > "$out_file"

  good "Report written: ${out_file}"
}

# ---------------- generate for one session -----------------------------------
generate_one() {
  local session_file="$1"

  if [[ ! -f "$session_file" ]]; then
    bad "Session file not found: ${session_file}"
    exit 1
  fi

  local sid
  sid=$(jq_or_py '.session_id // "unknown"' 'd.get("session_id","unknown")' "$session_file")
  local date_str
  date_str=$(date '+%Y%m%d')
  local out_file="${REPORTS_DIR}/${sid}_report_${date_str}.md"

  render_report "$session_file" "$out_file"
}

# ---------------- generate for all sessions ----------------------------------
generate_all() {
  local found=0
  for session_file in "${SESSIONS_DIR}"/*/session.json; do
    [[ -f "$session_file" ]] || continue
    found=1
    generate_one "$session_file"
  done
  if [[ $found -eq 0 ]]; then
    warn "No sessions found in ${SESSIONS_DIR}"
  fi
}

# ---------------- main -------------------------------------------------------
banner
detect_json_backend

case "${1:-auto}" in
  list)
    list_sessions ;;
  all)
    header "Generating reports for all sessions"
    generate_all ;;
  auto)
    header "Auto-detecting latest session"
    latest=$(latest_session)
    if [[ -z "$latest" ]]; then
      bad "No sessions found in ${SESSIONS_DIR}"
      exit 1
    fi
    info "Latest session: ${latest}"
    generate_one "$latest" ;;
  help|-h|--help)
    echo "Usage: $0 [list | all | <session_id> | auto]"
    echo ""
    echo "  (no args)       Generate report for the most recently updated session"
    echo "  list            List all available sessions"
    echo "  all             Generate reports for every session"
    echo "  <session_id>    Generate report for a specific session ID"
    echo "  help            Show this help"
    echo ""
    echo "Reports are written to: ${REPORTS_DIR}/"
    echo "" ;;
  *)
    # treat argument as session ID
    header "Resolving session: ${1}"
    session_file=$(resolve_session "$1")
    if [[ -z "$session_file" ]]; then
      bad "No session found matching: ${1}"
      echo ""
      list_sessions
      exit 1
    fi
    generate_one "$session_file" ;;
esac
