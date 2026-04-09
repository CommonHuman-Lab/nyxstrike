---
description: Internal bug bounty shared contract (memory schema). Not user-selectable.
mode: subagent
hidden: true
---

# Bug Bounty — Shared State Schema

All agents read and write a single canonical state file:

```
/tmp/bb-<program>-<timestamp>/state.json
```

---

## Full Schema

```json
{
  "program": "hackerone-acme",
  "target": "*.acme.com",
  "scope": ["*.acme.com", "api.acme.com"],
  "out_of_scope": ["blog.acme.com", "status.acme.com"],
  "goal": "find P1/P2 vulnerabilities",
  "preset": "bb-broad",
  "phase": "RECON",
  "phase_attempts": {},

  "assets": {
    "domains": [],
    "subdomains": [],
    "ips": [],
    "urls": [],
    "js_files": [],
    "open_ports": {},
    "technologies": {}
  },

  "endpoints": {
    "web": [],
    "api": [],
    "interesting": [],
    "login_pages": [],
    "admin_panels": [],
    "file_uploads": [],
    "redirects": []
  },

  "parameters": {
    "get": {},
    "post": {},
    "headers": {},
    "json_keys": {}
  },

  "auth": {
    "mechanisms": [],
    "tokens_found": [],
    "jwt_secrets": [],
    "api_keys": [],
    "session_cookies": []
  },

  "credentials": [],

  "findings": [
    {
      "id": "FINDING-001",
      "title": "",
      "severity": "P1 | P2 | P3 | P4 | INFO",
      "cvss": 0.0,
      "type": "XSS | SQLi | SSRF | IDOR | AuthBypass | InfoDisclosure | ...",
      "url": "",
      "method": "GET | POST | ...",
      "parameter": "",
      "payload": "",
      "evidence": "",
      "poc_curl": "",
      "poc_steps": [],
      "status": "confirmed | unconfirmed | false_positive",
      "reported": false,
      "notes": ""
    }
  ],

  "osint": {
    "emails": [],
    "employees": [],
    "github_repos": [],
    "js_secrets": [],
    "exposed_files": [],
    "breach_data": [],
    "shodan_results": []
  },

  "tool_runs": [
    {
      "tool": "",
      "params": {},
      "timestamp": "",
      "status": "ok | timeout | error",
      "output_file": ""
    }
  ],

  "dead_ends": [],
  "notes": []
}
```

---

## Directory Layout

```
/tmp/bb-<program>/
├── state.json
├── report.md
├── recon/
│   ├── subdomains.txt
│   ├── live_hosts.txt
│   └── ports.txt
├── web/
│   ├── endpoints.txt
│   └── screenshots/
├── api/
│   └── schema.json
├── osint/
│   ├── emails.txt
│   └── js_secrets.txt
├── fuzz/
│   └── params.txt
└── findings/
    ├── FINDING-001.md
    └── FINDING-002.md
```

---

## Rules for All Agents

1. **Read state.json before every tool call** — never duplicate a tool run that already succeeded.
2. **Write atomically** — read the current state, merge your changes, write back. Never replace arrays, only append.
3. **Log every tool call** — append to `tool_runs[]` with tool name, key params, and timestamp before firing.
4. **Scope check** — before testing any asset, verify it matches `scope[]` and is NOT in `out_of_scope[]`.
5. **Finding IDs** — auto-increment: `FINDING-001`, `FINDING-002`, etc. Check the highest existing ID before assigning.
