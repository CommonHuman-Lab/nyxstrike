"""
server_core/llm_agent.py

LLM analysis for NyxStrike.

analyze_session(session_id, llm_client, db, run_history)
  Passive analysis pass — reads an existing session's tool
  run logs from RunHistoryStore, sends them to the LLM for
  interpretation, and persists structured findings (vulns, risk level,
  summary) to NyxStrikeDB.  The LLM does NOT dispatch any tools.

Protocol tags (output):
  VULN: <name> | SEVERITY: CRITICAL|HIGH|MEDIUM|LOW|INFO | PORT: <port> | SERVICE: <svc> | DESC: <text> | FIX: <text>
  RISK_LEVEL: CRITICAL|HIGH|MEDIUM|LOW
  SUMMARY: <free text>

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
) -> List[Dict[str, Any]]:
  """
  Return log entries that likely belong to this session.

  Primary strategy (when session_id is known):
    - Match entries whose stored session_id equals the workflow session_id.

  Fallback heuristic (for old log entries that pre-date session_id tagging):
    - entry timestamp (epoch or ISO) >= session created_at
      AND tool name appears in the session's tools_executed list
    - OR entry params contain the session target string
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

  # ── Fetch and filter run logs ─────────────────────────────────────────────────
  all_logs: List[Dict[str, Any]] = run_history.get_all() if run_history else []
  relevant_logs = _filter_run_logs(
    all_logs, tools_executed, target, created_at_ts, session_id=session_id
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
    response = llm_client.chat(messages)
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
