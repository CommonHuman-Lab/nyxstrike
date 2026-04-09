---
description: Internal bug bounty shared contract (anti-loop). Not user-selectable.
mode: subagent
hidden: true
---

# Bug Bounty — Anti-Loop Rules

Seven rules every agent MUST apply before and during execution.

---

## Rule 1 — No Duplicate Tool Runs

Before firing any tool, check `state.tool_runs[]` for an entry with the same `tool` and equivalent key parameters.

- If found with `status: ok` and timestamp < 60 minutes ago → **skip, use cached result**
- If found with `status: timeout` or `status: error` → **try an alternative tool first**
- Exception: tools whose output is inherently stateful (e.g. live traffic capture) may re-run after 30 minutes

---

## Rule 2 — Max 3 Attempts Per Finding Vector

Track in `state.findings[].notes` or `state.dead_ends[]`.

- After 3 failed attempts on the same URL + parameter + payload class → mark `false_positive`, move on
- Do not retry confirmed false positives ever

---

## Rule 3 — Phase Entry Limit

Track in `state.phase_attempts{}` (e.g. `{"ENUM": 2}`).

- If a phase has been entered `>= 3` times with no new findings added → return `dead-end` immediately
- This prevents oscillating between phases when nothing is progressing

---

## Rule 4 — No Blind Wordlist Exhaustion

Wordlist progression — always start small:

| Step | Wordlist | Size | When to advance |
|------|----------|------|-----------------|
| 1 | `common.txt` | ~4.6k | Nothing found |
| 2 | `raft-medium-directories.txt` | ~30k | Still nothing found |
| 3 | `raft-large-directories.txt` | ~62k | Still nothing found |
| 4 | tech-specific list (e.g. `wp-content`) | varies | Only when tech confirmed |

**Stop when** you find something meaningful — do not keep running larger lists once hits are coming in.

---

## Rule 5 — No Blind Credential / Auth Testing

- Never spray credentials unless you have a real username list from OSINT or enumeration
- Max 50-entry password list per service per run — use targeted common passwords (seasonal, company-name-based, leaked)
- Never run hydra/medusa against login pages with rate limiting or lockout (check `Retry-After`, `X-RateLimit-*` headers first)
- One service at a time — no parallel credential sprays

---

## Rule 6 — Structured Dead-End Reporting

When returning a dead-end, always include this envelope:

```json
{
  "agent": "web",
  "status": "dead-end",
  "phase": "VULN",
  "attempted": [
    {"tool": "sqlmap", "target": "https://acme.com/search?q=", "result": "no injection found"},
    {"tool": "dalfox", "target": "https://acme.com/search?q=", "result": "no XSS found"}
  ],
  "findings": {},
  "next_suggested": "fuzz",
  "next_reason": "parameter map may be incomplete — run arjun on /search before retrying",
  "flags": ["ENUM_INCOMPLETE"]
}
```

---

## Rule 7 — Scope Boundary Hard Stop

If any tool run would touch a domain, IP, or endpoint not in `state.scope[]` or present in `state.out_of_scope[]`:

- **Do not run the tool**
- Log to `state.notes[]` with the out-of-scope asset
- Return immediately with `status: "scope-violation-prevented"`

This rule overrides everything else. Scope violations end bug bounty eligibility.

---

## Pre-Flight Checklist (run before every tool invocation)

```
[ ] Target is in state.scope[] and NOT in state.out_of_scope[]
[ ] This exact tool + params combo is not already in tool_runs[] with status: ok
[ ] Phase attempt count < 3
[ ] Attack vector attempt count < 3
[ ] Credential spray? → username list exists and password list <= 50 entries
[ ] Wordlist? → starting at common.txt unless previous run returned zero results
```
