---
description: Internal HTB shared contract (memory schema). Not user-selectable.
mode: subagent
hidden: true
---

# HTB CTF — Shared Memory Schema

All agents read from and write to a canonical state file at:

```
/tmp/htb-<target>/state.json
```

Where `<target>` is the sanitized IP or hostname (e.g. `10.10.11.42` → `/tmp/htb-10.10.11.42/state.json`).

---

## Schema

```json
{
  "target": "10.10.11.42",
  "hostname": "machine.htb",
  "goal": "user and root flags",
  "os_hint": "linux|windows|unknown",
  "phase": "RECON|ENUM|FOOTHOLD|PRIVESC|FLAG|LOOT|DONE",
  "preset": "htb-linux|htb-windows|htb-web|none",

  "open_ports": [22, 80, 443, 445],
  "services": {
    "22":  { "name": "ssh",   "version": "OpenSSH 8.9", "banner": "" },
    "80":  { "name": "http",  "version": "Apache 2.4.52", "banner": "" },
    "445": { "name": "smb",   "version": "", "banner": "" }
  },

  "web": {
    "vhosts": [],
    "endpoints": [],
    "technologies": [],
    "waf": null,
    "interesting": []
  },

  "api": {
    "endpoints": [],
    "auth_type": null,
    "tokens": [],
    "vulns": []
  },

  "credentials": [
    { "username": "admin", "password": "password123", "source": "hydra", "service": "http" }
  ],

  "hashes": [
    { "hash": "$6$...", "type": "sha512crypt", "cracked": null, "source": "shadow file" }
  ],

  "shells": [
    { "type": "reverse|webshell|meterpreter", "user": "www-data", "host": "10.10.11.42", "port": 4444 }
  ],

  "flags": {
    "user": null,
    "root": null,
    "other": []
  },

  "privesc": {
    "vectors": [],
    "attempted": [],
    "successful": null
  },

  "loot": {
    "files": [],
    "secrets": [],
    "ssh_keys": []
  },

  "tool_runs": [
    { "tool": "rustscan", "params": { "target": "10.10.11.42" }, "timestamp": "2026-01-01T00:00:00Z", "status": "complete" }
  ],

  "dead_ends": [],
  "notes": []
}
```

---

## Rules for all agents

1. **Read** the full state file at the start of every task.
2. **Write** updates atomically — read the file, merge your changes, write it back.
3. **Append** to `tool_runs` for every NyxStrike tool you invoke, including params.
4. **Never** overwrite another agent's findings — merge arrays, don't replace them.
5. Use `file_operations` tool with `operation: read` / `operation: write` to access the state file.
6. If the state file does not exist yet, create it with the base schema — the Leader normally creates it first.

---

## Directory layout

```
/tmp/htb-<target>/
├── state.json          ← canonical shared state
├── report.md           ← final report written by loot agent
├── nmap/               ← raw nmap output files
├── ffuf/               ← ffuf output
├── exploits/           ← payloads, scripts
└── loot/               ← exfiltrated files
```

Create subdirectories as needed using `file_operations`.
