"""
server_core/llm_agent.py

LLM analysis for NyxStrike.

analyze_session(session_id, llm_client, db, run_history)
  Passive analysis pass — reads an existing session's tool
  run logs from RunHistoryStore, sends them to the LLM for
  interpretation, and persists structured findings (vulns, risk level,
  summary) to NyxStrikeDB.  The LLM does NOT dispatch any tools.

follow_up_session(session_id, llm_client, db, run_history)
  Follow-up planning pass — reads the same session data and findings,
  then asks the LLM to produce a prioritised list of next steps /
  follow-up tool invocations.  Saves as a structured markdown plan.

Protocol tags (output):
  VULN: <name> | SEVERITY: CRITICAL|HIGH|MEDIUM|LOW|INFO | PORT: <port> | SERVICE: <svc> | DESC: <text> | FIX: <text>
  RISK_LEVEL: CRITICAL|HIGH|MEDIUM|LOW
  SUMMARY: <free text>
  NEXT: <tool_name> | REASON: <short rationale>
  STEP: <tool_name> | PARAMS: <key=val,...> | REASON: <rationale>

Design notes:
  - Graceful degradation: if llm_client.is_available() is False the
    function returns an error immediately.
  - Thread-safe: each call is independent; the DB lock is inside NyxStrikeDB.
"""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Tag parsers ────────────────────────────────────────────────────────────────

_VULN_RE = re.compile(
  r'VULN:\s*(?P<vuln>[^|]+)\s*\|\s*SEVERITY:\s*(?P<sev>[^|]+)\s*\|\s*PORT:\s*(?P<port>[^|]+)\s*\|\s*SERVICE:\s*(?P<svc>[^|]+)\s*\|\s*DESC:\s*(?P<desc>[^|]+)\s*\|\s*FIX:\s*(?P<fix>.+)',
  re.IGNORECASE,
)
_RISK_RE = re.compile(r'RISK_LEVEL:\s*(?P<risk>CRITICAL|HIGH|MEDIUM|LOW)', re.IGNORECASE)
_SUMMARY_RE = re.compile(r'SUMMARY:\s*(?P<text>.+)', re.IGNORECASE | re.DOTALL)
_NEXT_RE = re.compile(r'NEXT:\s*(?P<tool>[^|\n]+)\s*\|\s*REASON:\s*(?P<reason>[^\n]+)', re.IGNORECASE)


def _parse_findings(transcript: str) -> Tuple[List[Dict], str, str, List[Dict]]:
  """Extract vulnerabilities, risk_level, summary, and next_steps from the LLM response."""
  vulns = []
  for m in _VULN_RE.finditer(transcript):
    vulns.append({
      "vuln_name": m.group("vuln").strip(),
      "severity": m.group("sev").strip(),
      "port": m.group("port").strip(),
      "service": m.group("svc").strip(),
      "description": m.group("desc").strip(),
      "fix_text": m.group("fix").strip(),
    })

  risk_match = _RISK_RE.search(transcript)
  risk_level = risk_match.group("risk").upper() if risk_match else "UNKNOWN"

  # SUMMARY: must stop before any NEXT: lines — take only the first line of the match
  summary_match = _SUMMARY_RE.search(transcript)
  summary = ""
  if summary_match:
    raw = summary_match.group("text").strip()
    # Trim at the first NEXT: occurrence so it doesn't bleed into next_steps text
    next_pos = _NEXT_RE.search(raw)
    summary = raw[:next_pos.start()].strip() if next_pos else raw

  next_steps = []
  for m in _NEXT_RE.finditer(transcript):
    next_steps.append({
      "tool": m.group("tool").strip(),
      "reason": m.group("reason").strip(),
    })

  return vulns, risk_level, summary, next_steps


# ── Passive session analysis ───────────────────────────────────────────────────

_ANALYSIS_SYSTEM_PROMPT = """\
You are NyxStrike, an expert penetration testing analyst.

You have been given the raw output of security tools that were already executed
against a target as part of a planned workflow session.  Your job is to:
  1. Analyse each tool's output carefully.
  2. Identify vulnerabilities, misconfigurations, and noteworthy findings.
  3. Produce a structured report using the tags below — one line each.

Output format (emit each applicable line):
  VULN: <name> | SEVERITY: CRITICAL|HIGH|MEDIUM|LOW|INFO | PORT: <port_or_N/A> | SERVICE: <svc_or_N/A> | DESC: <description> | FIX: <remediation>
  RISK_LEVEL: CRITICAL|HIGH|MEDIUM|LOW
  SUMMARY: <one paragraph executive summary>
  NEXT: <tool_name> | REASON: <short rationale for why this tool should run next>

Rules:
  - Do NOT call any tools.  Only analyse the data provided.
  - Be concise in DESC and FIX fields (max ~200 chars each).
  - Emit RISK_LEVEL and SUMMARY exactly once.
  - Emit 0–5 NEXT: lines ordered by priority (most important first).
  - NEXT: tool names must be exact lowercase tool identifiers (e.g. nuclei, sqlmap, dalfox, gobuster, subfinder).
  - If no vulnerabilities are found, emit RISK_LEVEL: LOW and a brief SUMMARY.
"""

_MAX_OUTPUT_CHARS = 3000  # per tool entry, before truncation


def _format_run_log_entry(entry: Dict[str, Any]) -> str:
  """Format a single RunHistoryStore entry into a readable block."""
  tool = entry.get("tool", "unknown")
  params = json.dumps(entry.get("params", {}), default=str)
  stdout = (entry.get("stdout") or "").strip()
  stderr = (entry.get("stderr") or "").strip()
  rc = entry.get("return_code", "?")
  ts = entry.get("timestamp", "")

  if len(stdout) > _MAX_OUTPUT_CHARS:
    stdout = stdout[:_MAX_OUTPUT_CHARS] + "\n... [truncated]"
  if len(stderr) > _MAX_OUTPUT_CHARS:
    stderr = stderr[:_MAX_OUTPUT_CHARS] + "\n... [truncated]"

  parts = [f"=== Tool: {tool} | Time: {ts} | Return code: {rc} ==="]
  parts.append(f"Params: {params}")
  if stdout:
    parts.append(f"stdout:\n{stdout}")
  if stderr:
    parts.append(f"stderr:\n{stderr}")
  return "\n".join(parts)


def _filter_run_logs(
  all_logs: List[Dict[str, Any]],
  tools_executed: List[str],
  target: str,
  created_at_ts: int,
  session_id: str = "",
  session_run_log: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
  """
  Return log entries that likely belong to this session.

  Primary strategy (when session_id is known):
    - Match entries whose stored session_id equals the workflow session_id.

  Fallback heuristic (for old log entries that pre-date session_id tagging):
    - entry timestamp (epoch or ISO) >= session created_at
      AND tool name appears in the session's tools_executed list
    - OR entry params contain the session target string

  session_run_log: per-session run log stored directly on the session document.
    These are merged in and take precedence.
  """
  from datetime import timezone

  tools_set = {t.lower() for t in (tools_executed or [])}
  target_lower = (target or "").lower()
  session_id_clean = (session_id or "").strip()
  matched: List[Dict[str, Any]] = []

  for entry in all_logs:
    # Primary match: session_id tag set at record time
    entry_session_id = (entry.get("session_id") or "").strip()
    if session_id_clean and entry_session_id:
      if entry_session_id == session_id_clean:
        matched.append(entry)
      # Skip heuristic when both sides have a session_id but they don't match
      continue

    # Fallback heuristic for entries without session_id tagging
    ts_raw = entry.get("timestamp", "")
    entry_ts: Optional[int] = None
    if ts_raw:
      try:
        if isinstance(ts_raw, (int, float)):
          entry_ts = int(ts_raw)
        else:
          dt = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
          if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
          entry_ts = int(dt.timestamp())
      except (ValueError, TypeError):
        pass

    after_session = (entry_ts is None) or (entry_ts >= created_at_ts)
    tool_match = entry.get("tool", "").lower() in tools_set
    params_str = json.dumps(entry.get("params", {}), default=str).lower()
    target_match = bool(target_lower) and (target_lower in params_str)

    if after_session and (tool_match or target_match):
      matched.append(entry)

  # Merge per-session run_log entries, deduplicating against what we already have
  # from the global ring buffer (matched by tool+timestamp pair).
  if session_run_log:
    seen = {(e.get("tool", ""), e.get("timestamp", "")) for e in matched}
    for entry in session_run_log:
      key = (entry.get("tool", ""), entry.get("timestamp", ""))
      if key not in seen:
        matched.append(entry)
        seen.add(key)

  # Return chronologically (oldest first for the prompt)
  return list(reversed(matched))


def analyze_session(
  session_id: str,
  llm_client=None,
  db=None,
  run_history=None,
) -> Dict[str, Any]:
  """Analyse an existing  workflow session using the LLM.

  Fetches the session from SessionStore and its associated tool run logs
  from RunHistoryStore, builds a prompt, sends it to the LLM once, parses
  VULN: / RISK_LEVEL: / SUMMARY: tags, and persists findings to NyxStrikeDB.

  The LLM does NOT dispatch any tools — this is a pure analysis pass.

  Args:
    session_id:  A ``sess_`` prefixed session ID from SessionStore.
    llm_client:  LLMClient instance (must be is_available()).
    db:          NyxStrikeDB instance for persistence.
    run_history: RunHistoryStore instance for fetching tool logs.

  Returns:
    Dict with keys: success, llm_session_id, session_id, target, objective,
    risk_level, summary, vulnerabilities, logs_analysed, full_response, error.
  """
  # ── Guard: LLM must be available ─────────────────────────────────────────────
  if llm_client is None or not llm_client.is_available():
    return {
      "success": False,
      "error": (
        "LLM is not available. Configure NYXSTRIKE_LLM_PROVIDER / "
        "NYXSTRIKE_LLM_MODEL and ensure the backend is reachable."
      ),
    }

  # ── Load workflow session ─────────────────────────────────────────────────────
  from server_core.session_flow import load_session_any

  loaded = load_session_any(session_id)
  if not loaded:
    return {
      "success": False,
      "error": f"Session '{session_id}' not found.",
    }

  session_dict, _state = loaded
  target = session_dict.get("target", "")
  objective = session_dict.get("objective", "")
  tools_executed: List[str] = session_dict.get("tools_executed", [])
  created_at_ts: int = int(session_dict.get("created_at", 0) or 0)
  session_run_log: List[Dict[str, Any]] = list(session_dict.get("run_log", []) or [])

  # ── Fetch and filter run logs ─────────────────────────────────────────────────
  all_logs: List[Dict[str, Any]] = run_history.get_all() if run_history else []
  relevant_logs = _filter_run_logs(
    all_logs, tools_executed, target, created_at_ts,
    session_id=session_id, session_run_log=session_run_log,
  )

  # ── Build analysis prompt ─────────────────────────────────────────────────────
  llm_session_id = f"llm_{uuid.uuid4().hex[:10]}"

  if not relevant_logs:
    tool_data_section = (

      "No tool run logs were found for this session. "
      "The tools may not have been executed yet, or the logs may have expired."
    )
  else:
    tool_blocks = [_format_run_log_entry(e) for e in relevant_logs]
    tool_data_section = "\n\n".join(tool_blocks)

  user_message = (
    f"Session ID: {session_id}\n"
    f"Target: {target}\n"
    f"Objective: {objective or 'comprehensive security assessment'}\n"
    f"Tools planned: {', '.join(tools_executed) or 'N/A'}\n"
    f"Logs analysed: {len(relevant_logs)}\n\n"
    f"--- Tool Output ---\n\n"
    f"{tool_data_section}\n\n"
    "Please analyse the above tool output and report your findings."
  )

  messages: List[Dict[str, Any]] = [
    {"role": "system", "content": _ANALYSIS_SYSTEM_PROMPT},
    {"role": "user", "content": user_message},
  ]

  # ── Persist session start ─────────────────────────────────────────────────────
  if db:
    db.create_llm_session(
      session_id=llm_session_id,
      target=target,
      objective=f"analyze:{session_id}",
      provider=llm_client.provider,
      model=llm_client.model,
    )

  # ── Single LLM call ───────────────────────────────────────────────────────────
  try:
    response = llm_client.chat(messages, think=True, num_ctx=llm_client.num_ctx_analyse)
  except RuntimeError as exc:
    logger.error("analyze_session: LLM call failed: %s", exc)
    if db:
      db.update_llm_session(
        llm_session_id,
        status="error",
        completed_at=datetime.utcnow().isoformat(),
      )
    return {
      "success": False,
      "stdout": "",
      "stderr": f"LLM call failed: {exc}",
      "return_code": 1,
      "llm_session_id": llm_session_id,
      "session_id": session_id,
      "error": f"LLM call failed: {exc}",
    }

  # ── Parse findings ────────────────────────────────────────────────────────────
  vulnerabilities, risk_level, summary, next_steps = _parse_findings(response)

  # ── Persist completion ────────────────────────────────────────────────────────
  if db:
    db.update_llm_session(
      llm_session_id,
      status="completed",
      risk_level=risk_level,
      summary=summary,
      full_response=response,
      raw_scan_data=user_message[:8000],  # store trimmed prompt context
      tool_loops=len(relevant_logs),
      completed_at=datetime.utcnow().isoformat(),
    )
    for vuln in vulnerabilities:
      db.save_llm_vulnerability(llm_session_id, vuln)

  # ── Write findings back to the workflow session JSON ─────────────────────────
  try:
    import time as _time
    from server_core.session_flow import update_session, load_session_any as _load_any

    # Convert LLM vulns → session finding dicts (skip duplicates by title)
    ts_now = int(_time.time())
    existing_loaded = _load_any(session_id)
    existing_findings: List[Dict] = []
    if existing_loaded:
      existing_findings = list(existing_loaded[0].get("findings", []) or [])
    existing_titles = {str(f.get("title", "")).lower() for f in existing_findings}

    new_findings: List[Dict] = []
    for v in vulnerabilities:
      title = (v.get("vuln_name") or v.get("title") or "Unnamed Finding").strip()
      if title.lower() in existing_titles:
        continue  # already recorded — don't duplicate
      sev_raw = str(v.get("severity", "info")).lower()
      sev = sev_raw if sev_raw in {"critical", "high", "medium", "low", "info"} else "info"
      finding = {
        "finding_id": f"finding_{uuid.uuid4().hex[:8]}",
        "title": title,
        "severity": sev,
        "description": str(v.get("description") or v.get("desc", "")).strip(),
        "tool": "ai_analyze_session",
        "step_key": "",
        "evidence": "",
        "recommendation": str(v.get("fix_text") or v.get("fix", "")).strip(),
        "cve": "",
        "tags": ["ai-analysis"],
        "status": "open",
        "created_at": ts_now,
        "updated_at": ts_now,
      }
      new_findings.append(finding)
      existing_titles.add(title.lower())

    all_findings = existing_findings + new_findings

    # Derive risk level from the combined findings list
    def _risk_from_findings(fs: List[Dict]) -> str:
      if not fs:
        return risk_level.lower()
      sevs = {str(f.get("severity", "info")).lower() for f in fs}
      for lvl in ("critical", "high", "medium", "low"):
        if lvl in sevs:
          return lvl
      return "info"

    combined_risk = _risk_from_findings(all_findings)

    update_session(session_id, {
      "findings": all_findings,
      "risk_level": combined_risk,
      "total_findings": len(all_findings),
      "next_steps": next_steps,
    })
    logger.info(
      "analyze_session: added %d new findings to session %s (%d total)",
      len(new_findings), session_id, len(all_findings),
    )
  except Exception as _wb_exc:
    logger.warning("analyze_session: failed to write back to session JSON: %s", _wb_exc)

  # ── Build stdout for dashboard display ───────────────────────────────────────
  completed_at_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

  vuln_lines = []
  for i, v in enumerate(vulnerabilities, 1):
    title = v.get("title", "Unnamed finding")
    severity = v.get("severity", "UNKNOWN")
    desc = v.get("description", "")
    vuln_lines.append(f"  [{i}] [{severity}] {title}")
    if desc:
      vuln_lines.append(f"       {desc}")
  vuln_block = "\n".join(vuln_lines) if vuln_lines else "  (none)"

  next_lines = []
  for i, ns in enumerate(next_steps, 1):
    next_lines.append(f"  [{i}] {ns.get('tool', '')} — {ns.get('reason', '')}")
  next_block = "\n".join(next_lines) if next_lines else "  (none)"

  stdout = (
    f"Session:       {session_id}\n"
    f"Date:          {completed_at_iso}\n"
    f"Target:        {target}\n"
    f"Logs analysed: {len(relevant_logs)}\n"
    f"Risk level:    {risk_level}\n"
    f"\nSummary:\n  {summary}\n"
    f"\nFindings ({len(vulnerabilities)}):\n{vuln_block}\n"
    f"\nRecommended next steps ({len(next_steps)}):\n{next_block}\n"
  )

  return {
    "success": True,
    "stdout": stdout,
    "stderr": "",
    "return_code": 0,
    "timestamp": completed_at_iso,
    "llm_session_id": llm_session_id,
    "session_id": session_id,
    "target": target,
    "objective": objective,
    "completed_at": completed_at_iso,
    "provider": llm_client.provider,
    "model": llm_client.model,
    "risk_level": risk_level,
    "summary": summary,
    "vulnerabilities": vulnerabilities,
    "next_steps": next_steps,
    "logs_analysed": len(relevant_logs),
    "full_response": response,
  }


def format_analysis_md(
  result: Dict[str, Any],
  session_id: str,
  target: str,
  objective: str = "",
) -> str:
  """Format an analyze_session result dict as a Markdown report suitable for saving to notes."""
  generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
  risk_level = result.get("risk_level", "unknown").upper()
  summary = result.get("summary", "").strip()
  vulnerabilities: List[Dict] = result.get("vulnerabilities", [])
  next_steps: List[Dict] = result.get("next_steps", [])
  provider = result.get("provider", "")
  model = result.get("model", "")
  logs_analysed = result.get("logs_analysed", 0)

  lines: List[str] = []

  # Header
  lines.append(f"# AI Session Analysis — {target}\n")
  lines.append(f"*Generated by NyxStrike AI on {generated_at}*\n")
  if provider and model:
    lines.append(f"*Provider: {provider} / {model}*\n")
  lines.append("---\n")

  # Metadata
  lines.append("## Session Metadata\n")
  lines.append("| Field | Value |")
  lines.append("|-------|-------|")
  lines.append(f"| Session ID | `{session_id}` |")
  lines.append(f"| Target | `{target}` |")
  if objective:
    lines.append(f"| Objective | {objective} |")
  lines.append(f"| Risk Level | **{risk_level}** |")
  lines.append(f"| Findings | {len(vulnerabilities)} |")
  lines.append(f"| Tool Logs Analysed | {logs_analysed} |")
  lines.append("")

  # Summary
  lines.append("## Summary\n")
  lines.append(summary if summary else "*No summary generated.*")
  lines.append("")

  # Risk level
  lines.append("## Risk Level\n")
  _risk_badge = {
    "CRITICAL": "🔴 CRITICAL",
    "HIGH": "🟠 HIGH",
    "MEDIUM": "🟡 MEDIUM",
    "LOW": "🔵 LOW",
    "UNKNOWN": "⚪ UNKNOWN",
  }
  lines.append(f"**{_risk_badge.get(risk_level, risk_level)}**")
  lines.append("")

  # Findings
  lines.append(f"## Findings ({len(vulnerabilities)})\n")
  if vulnerabilities:
    _sev_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "UNKNOWN"]
    by_sev: Dict[str, List[Dict]] = {}
    for v in vulnerabilities:
      sev = str(v.get("severity", "UNKNOWN")).upper()
      by_sev.setdefault(sev, []).append(v)
    for sev in _sev_order:
      if sev not in by_sev:
        continue
      for v in by_sev[sev]:
        title = v.get("title") or v.get("vuln_name", "Unnamed Finding")
        desc = (v.get("description") or v.get("desc", "")).strip()
        fix = (v.get("fix_text") or v.get("fix", "")).strip()
        port = str(v.get("port", "")).strip()
        service = str(v.get("service", "")).strip()
        lines.append(f"### [{sev}] {title}\n")
        if desc:
          lines.append(f"{desc}\n")
        meta_rows = []
        if port and port not in ("", "N/A", "none", "None"):
          meta_rows.append(f"| Port | `{port}` |")
        if service and service not in ("", "N/A", "none", "None"):
          meta_rows.append(f"| Service | {service} |")
        if meta_rows:
          lines.append("| Field | Value |")
          lines.append("|-------|-------|")
          lines += meta_rows
          lines.append("")
        if fix:
          lines.append(f"**Recommendation:** {fix}\n")
  else:
    lines.append("*No findings identified.*\n")

  # Next steps
  lines.append(f"## Recommended Next Steps ({len(next_steps)})\n")
  if next_steps:
    for i, ns in enumerate(next_steps, 1):
      tool = ns.get("tool", "").strip()
      reason = ns.get("reason", "").strip()
      if tool:
        lines.append(f"{i}. `{tool}` — {reason}")
      else:
        lines.append(f"{i}. {reason}")
    lines.append("")
  else:
    lines.append("*No next steps recommended.*\n")

  return "\n".join(lines)


# ── Follow-up session planning ─────────────────────────────────────────────────

_FOLLOWUP_SYSTEM_PROMPT = """\
You are NyxStrike, an expert penetration testing planner.

You have been given the details of a completed or in-progress security session,
including the tools that were run, their raw output, and any findings already
identified.  Your job is to produce a prioritised, concrete follow-up action
plan — a list of next tool invocations that would maximise impact given what
has already been found.

Output format (emit each applicable line):
  SUMMARY: <one paragraph describing the current state and overall follow-up rationale>
  STEP: <tool_name> | PARAMS: <key=val,key2=val2,...> | REASON: <one sentence rationale>
  NEXT: <tool_name> | REASON: <short rationale for a tool to run later, no params needed yet>

Rules:
  - Do NOT call any tools.  Only plan based on the data provided.
  - Emit SUMMARY exactly once.
  - Emit 3–7 STEP: lines ordered by priority (highest impact first).
  - STEP: tool names must be exact lowercase tool identifiers matching NyxStrike's registry
    (e.g. nuclei, sqlmap, dalfox, gobuster, nmap_scan, subfinder, nikto_scan).
  - PARAMS: should be realistic key=value pairs based on what was already discovered.
    Use the session target as the default value for target/url/domain params.
    Separate multiple params with commas.  If no specific params are needed, write PARAMS: target=<target>.
  - Emit 0–3 NEXT: lines for lower-priority or conditional follow-up tools.
  - NEXT: tool names must also be exact lowercase tool identifiers.
  - Be specific: reference actual ports, services, paths, and findings from the session data.
  - If the session has no findings yet, plan a comprehensive initial enumeration.
"""

_STEP_RE = re.compile(
  r'STEP:\s*(?P<tool>[^|]+)\s*\|\s*PARAMS:\s*(?P<params>[^|]+)\s*\|\s*REASON:\s*(?P<reason>[^\n]+)',
  re.IGNORECASE,
)


def _parse_followup(transcript: str) -> Tuple[str, List[Dict], List[Dict]]:
  """Extract summary, steps, and next_steps from a follow-up LLM response."""
  # SUMMARY
  summary_match = _SUMMARY_RE.search(transcript)
  summary = ""
  if summary_match:
    raw = summary_match.group("text").strip()
    step_pos = _STEP_RE.search(raw)
    next_pos = _NEXT_RE.search(raw)
    end_pos = min(
      step_pos.start() if step_pos else len(raw),
      next_pos.start() if next_pos else len(raw),
    )
    summary = raw[:end_pos].strip()

  # STEP:
  steps: List[Dict] = []
  for m in _STEP_RE.finditer(transcript):
    steps.append({
      "tool": m.group("tool").strip(),
      "params": m.group("params").strip(),
      "reason": m.group("reason").strip(),
    })

  # NEXT:
  next_steps: List[Dict] = []
  for m in _NEXT_RE.finditer(transcript):
    next_steps.append({
      "tool": m.group("tool").strip(),
      "reason": m.group("reason").strip(),
    })

  return summary, steps, next_steps


def follow_up_session(
  session_id: str,
  llm_client=None,
  db=None,
  run_history=None,
) -> Dict[str, Any]:
  """Produce a prioritised follow-up plan for an existing workflow session.

  Reads the session, its tool run logs, and existing findings, then asks
  the LLM to plan the next concrete tool invocations.  Does not persist
  findings to NyxStrikeDB — the output is a planning document only.

  Args:
    session_id:  A ``sess_`` prefixed session ID from SessionStore.
    llm_client:  LLMClient instance (must be is_available()).
    db:          NyxStrikeDB instance (used for LLM session tracking).
    run_history: RunHistoryStore instance for fetching tool logs.

  Returns:
    Dict with keys: success, session_id, target, objective, summary,
    steps, next_steps, logs_analysed, full_response, error.
  """
  # ── Guard: LLM must be available ─────────────────────────────────────────────
  if llm_client is None or not llm_client.is_available():
    return {
      "success": False,
      "error": (
        "LLM is not available. Configure NYXSTRIKE_LLM_PROVIDER / "
        "NYXSTRIKE_LLM_MODEL and ensure the backend is reachable."
      ),
    }

  # ── Load workflow session ─────────────────────────────────────────────────────
  from server_core.session_flow import load_session_any

  loaded = load_session_any(session_id)
  if not loaded:
    return {
      "success": False,
      "error": f"Session '{session_id}' not found.",
    }

  session_dict, _state = loaded
  target = session_dict.get("target", "")
  objective = session_dict.get("objective", "")
  tools_executed: List[str] = session_dict.get("tools_executed", [])
  created_at_ts: int = int(session_dict.get("created_at", 0) or 0)
  existing_findings: List[Dict] = list(session_dict.get("findings", []) or [])
  risk_level: str = session_dict.get("risk_level", "unknown") or "unknown"

  # ── Fetch and filter run logs ─────────────────────────────────────────────────
  all_logs: List[Dict[str, Any]] = run_history.get_all() if run_history else []
  session_run_log: List[Dict[str, Any]] = list(session_dict.get("run_log", []) or [])
  relevant_logs = _filter_run_logs(
    all_logs, tools_executed, target, created_at_ts,
    session_id=session_id, session_run_log=session_run_log,
  )

  # ── Build follow-up prompt ────────────────────────────────────────────────────
  llm_session_id = f"llm_{uuid.uuid4().hex[:10]}"

  if not relevant_logs:
    tool_data_section = (
      "No tool run logs were found for this session. "
      "The tools may not have been executed yet, or the logs may have expired."
    )
  else:
    tool_blocks = [_format_run_log_entry(e) for e in relevant_logs]
    tool_data_section = "\n\n".join(tool_blocks)

  # Summarise existing findings for the prompt
  if existing_findings:
    finding_lines = []
    for f in existing_findings[:20]:  # cap to avoid prompt bloat
      title = str(f.get("title", "Unnamed")).strip()
      sev = str(f.get("severity", "info")).upper()
      desc = str(f.get("description", "")).strip()[:200]
      finding_lines.append(f"  [{sev}] {title}" + (f" — {desc}" if desc else ""))
    findings_section = "\n".join(finding_lines)
  else:
    findings_section = "  (none yet)"

  user_message = (
    f"Session ID: {session_id}\n"
    f"Target: {target}\n"
    f"Objective: {objective or 'comprehensive security assessment'}\n"
    f"Current risk level: {risk_level}\n"
    f"Tools planned: {', '.join(tools_executed) or 'N/A'}\n"
    f"Logs analysed: {len(relevant_logs)}\n\n"
    f"--- Existing Findings ({len(existing_findings)}) ---\n\n"
    f"{findings_section}\n\n"
    f"--- Tool Output ---\n\n"
    f"{tool_data_section}\n\n"
    "Based on the above, produce a prioritised follow-up action plan."
  )

  messages: List[Dict[str, Any]] = [
    {"role": "system", "content": _FOLLOWUP_SYSTEM_PROMPT},
    {"role": "user", "content": user_message},
  ]

  # ── Persist session start ─────────────────────────────────────────────────────
  if db:
    db.create_llm_session(
      session_id=llm_session_id,
      target=target,
      objective=f"follow-up:{session_id}",
      provider=llm_client.provider,
      model=llm_client.model,
    )

  # ── Single LLM call ───────────────────────────────────────────────────────────
  try:
    response = llm_client.chat(messages, think=True, num_ctx=llm_client.num_ctx_analyse)
  except RuntimeError as exc:
    logger.error("follow_up_session: LLM call failed: %s", exc)
    if db:
      db.update_llm_session(
        llm_session_id,
        status="error",
        completed_at=datetime.utcnow().isoformat(),
      )
    return {
      "success": False,
      "stdout": "",
      "stderr": f"LLM call failed: {exc}",
      "return_code": 1,
      "llm_session_id": llm_session_id,
      "session_id": session_id,
      "error": f"LLM call failed: {exc}",
    }

  # ── Parse response ────────────────────────────────────────────────────────────
  summary, steps, next_steps = _parse_followup(response)

  # ── Persist completion ────────────────────────────────────────────────────────
  if db:
    db.update_llm_session(
      llm_session_id,
      status="completed",
      summary=summary,
      full_response=response,
      raw_scan_data=user_message[:8000],
      tool_loops=len(relevant_logs),
      completed_at=datetime.utcnow().isoformat(),
    )

  # ── Build stdout ──────────────────────────────────────────────────────────────
  completed_at_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

  step_lines = []
  for i, s in enumerate(steps, 1):
    step_lines.append(f"  [{i}] {s.get('tool', '')} — {s.get('reason', '')}")
    if s.get("params"):
      step_lines.append(f"       params: {s['params']}")
  step_block = "\n".join(step_lines) if step_lines else "  (none)"

  next_lines = []
  for i, ns in enumerate(next_steps, 1):
    next_lines.append(f"  [{i}] {ns.get('tool', '')} — {ns.get('reason', '')}")
  next_block = "\n".join(next_lines) if next_lines else "  (none)"

  stdout = (
    f"Session:       {session_id}\n"
    f"Date:          {completed_at_iso}\n"
    f"Target:        {target}\n"
    f"Logs analysed: {len(relevant_logs)}\n"
    f"\nSummary:\n  {summary}\n"
    f"\nPrioritised steps ({len(steps)}):\n{step_block}\n"
    f"\nAdditional tools to consider ({len(next_steps)}):\n{next_block}\n"
  )

  return {
    "success": True,
    "stdout": stdout,
    "stderr": "",
    "return_code": 0,
    "timestamp": completed_at_iso,
    "llm_session_id": llm_session_id,
    "session_id": session_id,
    "target": target,
    "objective": objective,
    "completed_at": completed_at_iso,
    "provider": llm_client.provider,
    "model": llm_client.model,
    "summary": summary,
    "steps": steps,
    "next_steps": next_steps,
    "logs_analysed": len(relevant_logs),
    "full_response": response,
  }


def format_followup_md(
  result: Dict[str, Any],
  session_id: str,
  target: str,
  objective: str = "",
) -> str:
  """Format a follow_up_session result dict as a Markdown plan suitable for saving to notes."""
  generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
  summary = result.get("summary", "").strip()
  steps: List[Dict] = result.get("steps", [])
  next_steps: List[Dict] = result.get("next_steps", [])
  provider = result.get("provider", "")
  model = result.get("model", "")
  logs_analysed = result.get("logs_analysed", 0)

  lines: List[str] = []

  # Header
  lines.append(f"# AI Follow-up Plan — {target}\n")
  lines.append(f"*Generated by NyxStrike AI on {generated_at}*\n")
  if provider and model:
    lines.append(f"*Provider: {provider} / {model}*\n")
  lines.append("---\n")

  # Metadata
  lines.append("## Session Metadata\n")
  lines.append("| Field | Value |")
  lines.append("|-------|-------|")
  lines.append(f"| Session ID | `{session_id}` |")
  lines.append(f"| Target | `{target}` |")
  if objective:
    lines.append(f"| Objective | {objective} |")
  lines.append(f"| Follow-up Steps | {len(steps)} |")
  lines.append(f"| Tool Logs Analysed | {logs_analysed} |")
  lines.append("")

  # Summary
  lines.append("## Current State & Rationale\n")
  lines.append(summary if summary else "*No summary generated.*")
  lines.append("")

  # Prioritised steps
  lines.append(f"## Prioritised Follow-up Steps ({len(steps)})\n")
  if steps:
    for i, s in enumerate(steps, 1):
      tool = s.get("tool", "").strip()
      params = s.get("params", "").strip()
      reason = s.get("reason", "").strip()
      lines.append(f"### Step {i}: `{tool}`\n")
      if reason:
        lines.append(f"**Rationale:** {reason}\n")
      if params:
        lines.append("**Parameters:**\n")
        lines.append("```")
        for kv in params.split(","):
          lines.append(kv.strip())
        lines.append("```")
      lines.append("")
  else:
    lines.append("*No steps generated.*\n")

  # Additional tools
  lines.append(f"## Additional Tools to Consider ({len(next_steps)})\n")
  if next_steps:
    for i, ns in enumerate(next_steps, 1):
      tool = ns.get("tool", "").strip()
      reason = ns.get("reason", "").strip()
      lines.append(f"{i}. `{tool}` — {reason}")
    lines.append("")
  else:
    lines.append("*No additional tools recommended.*\n")

  return "\n".join(lines)
