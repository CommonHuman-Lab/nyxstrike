---
description: Internal HTB shared contract (anti-loop). Not user-selectable.
mode: subagent
hidden: true
---

# HTB CTF — Anti-Loop Rules

These rules apply to **every agent** in the htb-ctf system. Violating them causes infinite loops, wasted tool calls, and timeouts.

---

## Rule 1 — No duplicate tool runs

Before invoking any NyxStrike tool, check `state.json` → `tool_runs`.

If an entry already exists with the **same tool name AND same key parameters**, do not run it again.

```
# Bad — nmap already ran against this target with same params
tool_runs = [{ "tool": "nmap_scan", "params": { "target": "10.10.11.42", "ports": "22,80,443" } }]
# DO NOT run nmap_scan with same target+ports again

# OK — different ports
run_tool(tool="nmap_scan", target="10.10.11.42", ports="1-65535")  ✓
```

**Exception:** tools that are inherently stateful or time-sensitive (e.g. `responder_capture`, `system_monitoring`) may be re-run if the previous run was > 30 minutes ago.

---

## Rule 2 — Max 3 attempts per attack vector

Track attempts in `state.json` → `privesc.attempted` and `dead_ends`.

If the same attack vector (e.g. "sudo -l → NOPASSWD exploit", "CVE-2021-4034") has been attempted 3 times without success:
1. Mark it as a dead end in `dead_ends`
2. Move to the next vector
3. Do NOT retry it in the same session

---

## Rule 3 — Phase entry limit

A phase must not be entered more than 3 times without advancing.

```json
// In state.json — track phase entry counts
"phase_attempts": {
  "RECON": 1,
  "ENUM": 2,
  "FOOTHOLD": 3
}
```

If `phase_attempts[current_phase] >= 3` and no progress: escalate to Leader with `status: dead-end`.

---

## Rule 4 — No blind wordlist exhaustion

Never run a fuzzer (ffuf, feroxbuster, gobuster, wfuzz) with a wordlist > 100,000 entries unless:
- A smaller wordlist already returned zero results, AND
- The target shows evidence of a deep path structure

Default progression:
1. `/usr/share/wordlists/dirb/common.txt` (~4,600 entries)
2. `/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt` (~30,000)
3. `/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt` (~62,000)

Stop when you find something meaningful. Do not chain all three automatically.

---

## Rule 5 — No credential spray without a list

Do not run `hydra_attack` or `medusa_attack` with:
- A username of `admin` and password list > 1,000 entries on the first pass
- More than one service at a time (avoid account lockout)

Build a targeted credential list from:
1. Usernames found via enumeration (SMB, web, OSINT)
2. Passwords from `rockyou.txt` top-1000 first pass
3. Service-specific defaults (e.g. `root:root`, `admin:admin`, `sa:sa`)

---

## Rule 6 — Structured dead-end reporting

When stuck, return this to Leader rather than retrying:

```json
{
  "agent": "<agent-name>",
  "status": "dead-end",
  "phase": "<current-phase>",
  "attempted": ["vector 1", "vector 2", "vector 3"],
  "findings": { "...partial findings..." },
  "next_suggested": "<suggested-pivot>",
  "flags": []
}
```

Leader will decide whether to try a different path or report to the user.

---

## Rule 7 — Timeout awareness

All NyxStrike tools have a default `COMMAND_TIMEOUT`. If a tool call times out:
1. Log it in `tool_runs` as `status: timeout`
2. Try a faster/lighter alternative (e.g. rustscan instead of nmap full scan)
3. Do NOT retry the same timed-out invocation identically

---

## Summary Checklist (run before every tool call)

- [ ] Is this tool already in `tool_runs` with same params? → skip
- [ ] Is this attack vector in `dead_ends`? → skip
- [ ] Is `phase_attempts[phase] >= 3`? → escalate
- [ ] Am I about to run a wordlist > 100k? → start smaller
- [ ] Am I about to spray credentials blindly? → build a targeted list first
