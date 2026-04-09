---
description: Internal HTB shared contract (output envelope). Not user-selectable.
mode: subagent
hidden: true
---

# HTB CTF — Output Contract

Every specialist subagent MUST return a structured JSON envelope as its final message to the Leader. This is what the Leader uses to decide the next step.

---

## Envelope Schema

```json
{
  "agent": "<agent-name>",
  "phase": "<phase-this-agent-ran-in>",
  "status": "complete | partial | failed | dead-end",
  "duration_seconds": 120,

  "findings": {
    // Agent-specific findings — see per-agent sections below
  },

  "state_updates": {
    // Keys to merge into state.json — only include what changed
    "open_ports": [],
    "services": {},
    "credentials": [],
    "shells": [],
    "flags": {}
  },

  "flags": [],

  "next_suggested": "<agent-name or null>",
  "next_reason": "Found HTTP on port 8080, recommend web enumeration",

  "notes": []
}
```

---

## Status Meanings

| Status | Meaning | Leader Action |
|--------|---------|---------------|
| `complete` | Phase objective achieved, ready to advance | Advance phase |
| `partial` | Some progress, more work possible | Continue or pivot |
| `failed` | Tool errors, no useful output | Retry with alternate tool |
| `dead-end` | All vectors exhausted, no progress | Pivot or escalate to user |

---

## Per-Agent `findings` Shapes

### `recon`
```json
{
  "open_ports": [22, 80, 443],
  "services": { "80": { "name": "http", "version": "Apache 2.4.52" } },
  "os_hint": "linux",
  "hostnames": ["machine.htb"]
}
```

### `web`
```json
{
  "vhosts": ["admin.machine.htb"],
  "endpoints": ["/admin", "/api/v1", "/upload"],
  "technologies": ["PHP 8.1", "Laravel"],
  "waf": null,
  "vulns": [{ "type": "sqli", "url": "/login", "param": "username" }],
  "interesting": ["/backup.zip", "/.git/"]
}
```

### `api`
```json
{
  "endpoints": ["/api/v1/users", "/api/v1/admin"],
  "auth_type": "JWT Bearer",
  "vulns": [{ "type": "jwt_none_alg", "token": "eyJ..." }],
  "tokens": [{ "value": "eyJ...", "user": "admin" }]
}
```

### `service-enum`
```json
{
  "smb_shares": [{ "name": "ADMIN$", "access": "read" }],
  "users": ["administrator", "john"],
  "domain": "CORP",
  "dc": "10.10.11.1",
  "interesting_files": ["ntlm.hash", "credentials.txt"]
}
```

### `creds`
```json
{
  "credentials": [{ "username": "admin", "password": "admin123", "service": "http" }],
  "hashes": [{ "hash": "$6$...", "type": "sha512crypt", "cracked": "password1" }]
}
```

### `foothold`
```json
{
  "shell": { "type": "reverse", "user": "www-data", "port": 4444 },
  "method": "CVE-2023-XXXX via metasploit",
  "payload_path": "/tmp/htb-10.10.11.42/exploits/shell.elf"
}
```

### `privesc-linux` / `privesc-windows`
```json
{
  "vectors_found": ["sudo -l NOPASSWD /usr/bin/vim", "SUID /usr/bin/find"],
  "successful_vector": "sudo vim -c ':!/bin/bash'",
  "shell": { "type": "interactive", "user": "root" }
}
```

### `flag`
```json
{
  "user_flag": "HTB{abc123...}",
  "root_flag": "HTB{xyz789...}",
  "paths": { "user": "/home/john/user.txt", "root": "/root/root.txt" }
}
```

### `binary`
```json
{
  "mitigations": { "NX": true, "PIE": true, "canary": false, "RELRO": "full" },
  "vulnerability": "buffer overflow at 0x401234",
  "exploit_approach": "ret2libc",
  "gadgets": ["0x40129a: pop rdi; ret"],
  "exploit_script": "/tmp/htb-<target>/exploits/exploit.py"
}
```

### `forensics`
```json
{
  "files_carved": ["/tmp/htb-<t>/loot/recovered.jpg"],
  "strings_interesting": ["password: letmein", "flag{...}"],
  "metadata": { "author": "admin", "created": "2024-01-01" },
  "stego_extracted": null
}
```

### `crypto`
```json
{
  "hashes_cracked": [{ "hash": "5f4dcc3b...", "type": "md5", "plaintext": "password" }],
  "attack_used": "hashcat rockyou"
}
```

### `loot`
```json
{
  "report_path": "/tmp/htb-10.10.11.42/report.md",
  "flags": { "user": "HTB{...}", "root": "HTB{...}" },
  "credentials": [],
  "ssh_keys": [],
  "files_exfiltrated": []
}
```

---

## Mandatory Fields

These fields are **required** in every response regardless of status:

- `agent` — your agent name
- `phase` — the phase you ran in
- `status` — one of the four status values
- `findings` — object (may be empty `{}` on failure)
- `state_updates` — object (may be empty `{}`)
- `flags` — array (may be empty `[]`)
- `next_suggested` — string or `null`

Missing mandatory fields will cause the Leader to treat the response as `failed`.
