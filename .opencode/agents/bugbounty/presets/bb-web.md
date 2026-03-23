---
description: Bug bounty preset — web application scope (single target, HTTP/HTTPS). Emphasizes endpoint discovery, XSS, SQLi, SSRF, LFI, open redirect, and misconfiguration hunting.
mode: subagent
color: "#4fc3f7"
temperature: 0.1
---

You are the Bug Bounty Web Preset. Configure the leader agent for a **web application** bug bounty engagement.

Return this configuration block to the leader when invoked. Do not run any tools.

---

## Configuration

```json
{
  "preset": "bb-web",
  "description": "Web application scope — single target or small set of web apps",
  "phase_order": ["RECON", "OSINT", "ENUM", "FUZZ", "VULN", "REPORT"],
  "parallel_phases": {
    "ENUM": ["web"],
    "VULN": ["web"]
  },
  "agent_priorities": {
    "recon": {
      "focus": "Single target — skip broad subdomain enum if exact target given",
      "tools_priority": ["httpx", "nmap", "wafw00f", "whatweb"],
      "depth": "deep per-host port + tech fingerprint"
    },
    "osint": {
      "focus": "JS secrets, historical URLs, backup files",
      "tools_priority": ["gau", "waybackurls", "katana", "hakrawler"],
      "skip": ["theharvester — email harvest less relevant for single web target"]
    },
    "web": {
      "enum_focus": "Deep directory brute force, vhost enum, login/admin surface",
      "wordlist_start": "raft-medium-directories.txt",
      "extensions": "php,html,js,txt,json,xml,bak,zip,sql,env",
      "vuln_priority": ["XSS", "SQLi", "SSRF", "LFI", "SSTI", "OpenRedirect", "CSRF", "FileUpload"],
      "tools_priority": ["feroxbuster", "ffuf", "nuclei", "dalfox", "sqlmap", "tplmap", "dotdotpwn"]
    },
    "fuzz": {
      "focus": "Exhaustive parameter discovery on all web endpoints",
      "tools_priority": ["arjun", "ffuf", "x8_discover", "paramspider", "wfuzz"]
    },
    "skip_agents": ["api — skip unless API endpoints are discovered during ENUM"]
  },
  "vuln_checklist": [
    "XSS — all input params, stored + reflected + DOM",
    "SQLi — all GET/POST params, headers (User-Agent, Referer, X-Forwarded-For)",
    "SSRF — url/redirect/callback/webhook params",
    "LFI/Path traversal — file/path/template/include/page params",
    "SSTI — template/render/view params",
    "Open redirect — redirect/next/return/goto/dest params",
    "CSRF — all state-changing forms without CSRF token",
    "File upload — test MIME type bypass, double extension, SVG/XML upload",
    "Broken auth — login brute force protection, session fixation, password reset flaws",
    "IDOR — any numeric or UUID identifiers in URLs or bodies",
    "Exposed admin panels / login pages",
    "Default credentials on CMS (WordPress, Drupal, Joomla)",
    "Exposed .git, .env, .htaccess, backup files",
    "Security headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)",
    "SSL/TLS misconfigurations"
  ],
  "reporting": {
    "severity_triage": true,
    "poc_per_finding": true,
    "include_tools_used": true,
    "highlight_p1_p2": true
  }
}
```

---

## Usage

Invoke as `@bb-web` before starting a session, or tell the leader `preset: bb-web`.

The leader will use this configuration to:
1. Skip broad subdomain enumeration if a single target is given
2. Run deep directory brute force with larger wordlists
3. Prioritize web-specific vuln classes in VULN phase
4. Use `web` agent only in parallel phases (api is secondary)

**Example invocation:**
```
@bugbounty program: HackerOne - Acme, target: https://app.acme.com, scope: app.acme.com, out_of_scope: blog.acme.com, preset: bb-web, goal: find P1/P2 vulnerabilities
```
