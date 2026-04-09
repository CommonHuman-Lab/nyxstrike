---
description: Internal bug bounty shared contract (state machine). Not user-selectable.
mode: subagent
hidden: true
---

# Bug Bounty — State Machine

## Phase Progression

```
RECON → OSINT → ENUM → FUZZ → VULN → REPORT → DONE
```

Each phase has a defined owner agent, entry condition, and exit condition.

---

## Phase Definitions

| Phase | Owner Agent | Entry Condition | Exit Condition |
|-------|-------------|-----------------|----------------|
| `RECON` | `recon` | Session initialized | Live subdomains + open ports mapped |
| `OSINT` | `osint` | `assets.subdomains` non-empty | Email, JS secrets, leaked creds collected |
| `ENUM` | `web` + `api` (parallel) | `assets.urls` non-empty | Endpoints, parameters, technologies mapped |
| `FUZZ` | `fuzz` | `endpoints.web` or `endpoints.api` non-empty | Parameters discovered, interesting inputs identified |
| `VULN` | `web` + `api` (parallel, driven by findings) | Fuzz results + parameter map complete | All identified vectors tested; each finding `confirmed` or `false_positive` |
| `REPORT` | `report` | `findings[]` non-empty | `report.md` written with PoC + severity triage |
| `DONE` | leader | `report.md` exists | — |

---

## Parallel Execution

During `ENUM`, invoke `web` and `api` simultaneously in a single `Task()` batch.

During `VULN`, group findings by type and invoke the relevant specialist in parallel:
- Web vulns (XSS, SQLi, SSRF, LFI, open redirect) → `web` agent in exploit mode
- API vulns (IDOR, mass assignment, JWT, broken auth) → `api` agent in exploit mode

---

## Phase Rollback Rules

- If a phase agent returns `dead-end` or `failed`:
  - First attempt: try an alternate tool within the same phase
  - Second attempt: try a broader wordlist or different approach
  - Third attempt: record in `dead_ends[]`, advance to the next phase anyway, note gaps in final report
- Never loop more than 3 times in the same phase for the same target/endpoint

---

## OS / Technology Detection Hints

| Signal | Inference |
|--------|-----------|
| `Server: nginx` or `Server: Apache` | Linux likely |
| `Server: IIS` | Windows likely |
| `X-Powered-By: PHP` | PHP backend |
| `X-Powered-By: Express` | Node.js backend |
| GraphQL introspection enabled | API target |
| JWT in cookies or `Authorization` header | Auth testing priority |
| `wp-content/` in URLs | WordPress — run wpscan |
| `admin/`, `dashboard/`, `panel/` in endpoints | Admin surface — test auth |

---

## Scope Enforcement

Before EVERY tool call and every finding creation:
1. Confirm the target domain/IP is in `scope[]`
2. Confirm it is NOT in `out_of_scope[]`
3. If unclear, mark as `needs_review` in `notes[]` and skip testing — do NOT test

Out-of-scope violations are a disqualification in bug bounty programs. This rule is absolute.
