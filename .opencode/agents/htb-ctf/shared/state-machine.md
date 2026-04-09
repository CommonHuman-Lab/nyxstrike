---
description: Internal HTB shared contract (state machine). Not user-selectable.
mode: subagent
hidden: true
---

# HTB CTF — State Machine

The attack lifecycle is a linear phase progression with conditional branches.
The current phase is stored in `state.json` → `phase`.

---

## Phase Definitions

```
RECON → ENUM → FOOTHOLD → PRIVESC → FLAG → LOOT → DONE
```

| Phase      | Owner Agent(s)                        | Entry Condition                        | Exit Condition                                  |
|------------|---------------------------------------|----------------------------------------|-------------------------------------------------|
| `RECON`    | `recon`                               | State file created by Leader           | At least one open port and service identified   |
| `ENUM`     | `web`, `service-enum`, `api`          | RECON complete                         | Attack surface mapped; at least one attack vector identified |
| `FOOTHOLD` | `foothold`, `creds`, `web`            | ENUM complete, vector identified       | Shell obtained (`shells` array non-empty)       |
| `PRIVESC`  | `privesc-linux` or `privesc-windows`  | FOOTHOLD complete                      | Root/SYSTEM shell obtained                      |
| `FLAG`     | `flag`                                | Any shell active                       | At least one flag value written to `flags`      |
| `LOOT`     | `loot`                                | FLAG complete                          | `report.md` written                             |
| `DONE`     | Leader                                | LOOT complete                          | Leader returns final summary to user            |

---

## Phase Transitions — Leader Logic

```
START
  └─ invoke planner → get attack_plan
  └─ present plan to user, wait for confirmation
  └─ create state.json, set phase = RECON

RECON
  └─ invoke recon agent
  └─ on complete: update services, set phase = ENUM

ENUM
  └─ parallel invocation based on services found:
       port 80/443/8080/8443  → invoke web
       port 445/139/3389      → invoke service-enum
       API fingerprint        → invoke api
       port 21/23/25/110/3306 → invoke service-enum
  └─ on complete: collect vectors, set phase = FOOTHOLD

FOOTHOLD
  └─ if web vuln found       → invoke web (exploitation mode)
  └─ if creds found          → invoke creds (brute-force/spray)
  └─ if public exploit found → invoke foothold
  └─ on shell obtained: set phase = PRIVESC

PRIVESC
  └─ if os_hint = linux      → invoke privesc-linux
  └─ if os_hint = windows    → invoke privesc-windows
  └─ if unknown              → invoke both, race
  └─ on root shell: set phase = FLAG

FLAG
  └─ invoke flag agent
  └─ on flag(s) found: set phase = LOOT

LOOT
  └─ invoke loot agent
  └─ on report written: set phase = DONE

DONE
  └─ Leader prints summary and report path to user
```

---

## Parallel Enumeration Rules

During ENUM, multiple agents CAN run in parallel if they target different services:
- `web` + `service-enum` + `api` may all run simultaneously
- Use separate Task tool calls in one message to achieve parallelism
- Each writes its own section of state.json (no conflicts if domains are separate)

---

## Phase Rollback

If an agent returns `status: dead-end` or `status: failed` three times for the same phase:
1. Leader sets a `dead_ends` entry in state.json
2. Leader attempts an alternate path (e.g. skip web, try service-enum instead)
3. If all paths exhausted, Leader reports to user: "Stuck at phase X — manual intervention needed"
4. Do NOT loop indefinitely — max 3 attempts per phase path

---

## OS Detection

Set `os_hint` in state.json as soon as evidence appears:

| Signal | OS Hint |
|--------|---------|
| Port 445/139 open | `windows` |
| Port 22 open, no 3389 | `linux` |
| nmap OS detection result | use that |
| TTL ~64 in ping | `linux` |
| TTL ~128 in ping | `windows` |
| IIS in HTTP headers | `windows` |
| Apache/nginx in headers | `linux` |
