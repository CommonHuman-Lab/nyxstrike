---
description: Internal bug bounty shared contract (output envelope). Not user-selectable.
mode: subagent
hidden: true
---

# Bug Bounty — Output Contract

Every subagent's final response to the leader MUST be a single JSON object matching this envelope.

The leader treats any response missing mandatory fields as `status: "failed"`.

---

## Envelope

```json
{
  "agent": "<agent-name>",
  "phase": "<phase-this-agent-ran-in>",
  "status": "complete | partial | failed | dead-end | scope-violation-prevented",
  "duration_seconds": 120,
  "findings": { },
  "state_updates": {
    "assets": {},
    "endpoints": {},
    "parameters": {},
    "auth": {},
    "credentials": [],
    "findings": [],
    "osint": {}
  },
  "next_suggested": "<agent-name or null>",
  "next_reason": "...",
  "notes": []
}
```

---

## Mandatory Fields (7)

Missing any of these → leader treats as `status: "failed"`:

1. `agent`
2. `phase`
3. `status`
4. `findings`
5. `state_updates`
6. `next_suggested`
7. `notes`

---

## Status → Leader Action

| Status | Leader Action |
|--------|--------------|
| `complete` | Advance to next phase or invoke `next_suggested` |
| `partial` | Continue in same phase with alternate tool or invoke `next_suggested` |
| `failed` | Retry with alternate tool; if 3rd failure → advance anyway, note gap in report |
| `dead-end` | Pivot using `next_suggested`; if 3rd dead-end for same phase → escalate to user |
| `scope-violation-prevented` | Log to notes, do not retry, move on |

---

## Per-Agent `findings` Shapes

### `recon`
```json
{
  "subdomains_found": 42,
  "live_hosts": ["sub1.acme.com", "sub2.acme.com"],
  "open_ports": {"sub1.acme.com": [80, 443, 8080]},
  "technologies": {"sub1.acme.com": ["nginx/1.18", "PHP/7.4"]},
  "waf_detected": {"sub1.acme.com": "Cloudflare"}
}
```

### `osint`
```json
{
  "emails": ["admin@acme.com"],
  "employees": ["John Smith"],
  "js_secrets": [{"file": "app.js", "secret_type": "AWS_KEY", "value": "AKIA..."}],
  "historical_urls": 1240,
  "interesting_urls": ["https://acme.com/admin", "https://acme.com/.git/config"],
  "github_repos": ["acme/frontend"],
  "breach_mentions": 0
}
```

### `web`
```json
{
  "endpoints_found": 87,
  "interesting": ["https://acme.com/admin", "https://acme.com/api/v1"],
  "login_pages": ["https://acme.com/login"],
  "admin_panels": ["https://acme.com/admin"],
  "file_uploads": ["https://acme.com/upload"],
  "vulns_identified": [
    {"type": "XSS", "url": "https://acme.com/search", "param": "q", "confidence": "high"}
  ]
}
```

### `api`
```json
{
  "endpoints_found": 34,
  "schema_url": "https://acme.com/api/swagger.json",
  "auth_type": "JWT | Bearer | API-Key | None",
  "graphql_introspection": true,
  "vulns_identified": [
    {"type": "IDOR", "endpoint": "/api/users/{id}", "confidence": "high"},
    {"type": "JWT_ALG_NONE", "token": "eyJ...", "confidence": "confirmed"}
  ]
}
```

### `fuzz`
```json
{
  "parameters_found": {
    "https://acme.com/search": {"get": ["q", "page", "debug"], "post": []},
    "https://acme.com/api/items": {"get": [], "post": ["id", "user_id", "admin"]}
  },
  "interesting_params": ["debug", "admin", "user_id", "redirect"],
  "hidden_endpoints": ["/api/internal/users", "/api/debug/config"]
}
```

### `report`
```json
{
  "findings_total": 5,
  "by_severity": {"P1": 1, "P2": 2, "P3": 1, "P4": 1, "INFO": 0},
  "report_path": "/tmp/bb-acme/report.md",
  "findings_paths": ["/tmp/bb-acme/findings/FINDING-001.md"]
}
```

---

## Finding Object (added to `state_updates.findings[]`)

```json
{
  "id": "FINDING-001",
  "title": "Reflected XSS in search parameter",
  "severity": "P3",
  "cvss": 6.1,
  "type": "XSS",
  "url": "https://acme.com/search",
  "method": "GET",
  "parameter": "q",
  "payload": "<img src=x onerror=alert(document.domain)>",
  "evidence": "Response contains unescaped payload in HTML body",
  "poc_curl": "curl -sk 'https://acme.com/search?q=<img+src=x+onerror=alert(document.domain)>'",
  "poc_steps": [
    "1. Navigate to https://acme.com/search",
    "2. Enter payload: <img src=x onerror=alert(document.domain)> in the q parameter",
    "3. Submit — JavaScript alert fires with domain"
  ],
  "status": "confirmed",
  "reported": false,
  "notes": "No CSP header present. Affects all browsers."
}
```
