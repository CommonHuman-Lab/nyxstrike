---
description: Internal bug bounty shared contract (tool policy). Not user-selectable.
mode: subagent
hidden: true
---

# Bug Bounty — Tool Policy

Canonical tool selection reference. Every agent uses this table to pick tools for each phase.
All tools are invoked via `run_tool("<tool_name>", { ... })` through the NyxStrike MCP gateway.

---

## RECON Phase

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `subfinder` | Fast passive subdomain enumeration | `domain`, `all` sources |
| 2 | `amass` | Deep subdomain enum + OSINT | `domain`, `passive` mode first |
| 3 | `dnsenum` | DNS zone info + brute | `domain` |
| 4 | `fierce` | DNS recon + zone transfer attempt | `domain` |
| 5 | `httpx` | Probe live hosts, detect tech, status codes | `list` of subdomains, `title`, `tech-detect` |
| 6 | `rustscan` | Fast port scan on live hosts | `target`, common ports first |
| 7 | `nmap` | Deep service fingerprint on open ports | `target`, `-sV -sC`, specific ports |
| 8 | `wafw00f` | WAF detection before active testing | `url` |

---

## OSINT Phase

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `theharvester` | Email, employee, subdomain OSINT | `domain`, all sources |
| 2 | `gau` | Historical URLs from multiple archives | `domain` |
| 3 | `waybackurls` | Wayback Machine URL discovery | `domain` |
| 4 | `katana` | JS file crawl + endpoint extraction | `url`, `-jc` JS crawl mode |
| 5 | `hakrawler` | Fast web crawl for endpoints + JS | `url` |
| 6 | `strings` | Extract secrets from downloaded JS files | `file` |

---

## ENUM Web Phase

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `httpx` | Confirm live hosts, grab response data | `url`, `-title -status-code -tech-detect` |
| 2 | `feroxbuster` | Recursive directory + file discovery | `url`, `wordlist`, `-x php,html,js,txt` |
| 3 | `ffuf` | Fast endpoint + vhost + parameter fuzzing | `url`, `FUZZ`, wordlist |
| 4 | `gobuster` | Directory + DNS + vhost mode | `url`, `wordlist`, `dir` or `vhost` mode |
| 5 | `katana` | Crawl + JS analysis | `url`, `-depth 3` |
| 6 | `nuclei` | Technology and exposure detection | `url`, `-t technologies,exposures` |
| 7 | `whatweb` | Technology fingerprinting | `url` |
| 8 | `wpscan` | WordPress-specific enum (only if WP detected) | `url`, `--enumerate ap,at,u` |

---

## ENUM API Phase

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `httpx` | Probe API base URLs, detect auth headers | `url` |
| 2 | `api_schema_analyzer` | Parse OpenAPI/Swagger/GraphQL schemas | `url` |
| 3 | `graphql_scanner` | GraphQL introspection + field enum | `url` |
| 4 | `arjun` | HTTP parameter discovery | `url`, GET + POST |
| 5 | `jwt_analyzer` | JWT algorithm confusion + weak secrets | `token` |
| 6 | `x8_discover` | Hidden parameter discovery | `url` |
| 7 | `comprehensive_api_audit` | Full automated API security audit | `url` |

---

## FUZZ Phase

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `arjun` | Parameter discovery (GET + POST + JSON) | `url`, all methods |
| 2 | `ffuf` | Parameter fuzzing with injection payloads | `url`, `FUZZ`, injection wordlist |
| 3 | `x8_discover` | Hidden parameter brute force | `url` |
| 4 | `paramspider` | Mine params from Wayback + Common Crawl | `domain` |
| 5 | `wfuzz` | Advanced fuzzing with filter/matcher | `url`, `FUZZ`, payload list |

---

## VULN Phase — Web

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `nuclei` | CVE + misconfiguration + exposure scans | `url`, `-t cves,misconfigs,exposed-panels` |
| 2 | `sqlmap` | SQL injection detection + exploitation | `url`, `params`, `--level 3 --risk 2` |
| 3 | `dalfox` | XSS detection with DOM analysis | `url`, params |
| 4 | `nikto` | Web server misconfiguration scanning | `url` |
| 5 | `tplmap` | SSTI detection + exploitation | `url`, params |
| 6 | `commix` | Command injection testing | `url`, params |
| 7 | `dotdotpwn` | Path traversal / LFI testing | `url`, `traversal` module |
| 8 | `testssl` | SSL/TLS misconfiguration | `host:port` |
| 9 | `jaeles` | Custom signature-based vuln scanning | `url`, signatures |

---

## VULN Phase — API

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `api_fuzzer` | Fuzz all discovered endpoints with injection payloads | `url`, `schema` |
| 2 | `jwt_analyzer` | Algorithm confusion (alg:none, RS→HS), weak secrets | `token` |
| 3 | `sqlmap` | SQL injection via API parameters | `url`, `--data`, JSON body |
| 4 | `comprehensive_api_audit` | IDOR, mass assignment, broken object level auth | `url` |
| 5 | `nuclei` | API-specific templates | `url`, `-t exposures,token-spray` |

---

## OSINT / Credential Phase

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `theharvester` | Email + subdomain harvest | `domain`, sources |
| 2 | `gau` + `waybackurls` | Historical URL leak discovery | `domain` |
| 3 | `hashid` | Identify hash types in leaked data | `hash` |
| 4 | `john` | Crack weak hashes | `hash_file`, `wordlist` |
| 5 | `hashcat` | GPU-based hash cracking | `hash_file`, `attack_mode` |

---

## Severity Classification

| Severity | CVSS Range | Examples |
|----------|-----------|---------|
| P1 — Critical | 9.0–10.0 | RCE, SQLi with data exfil, account takeover, auth bypass |
| P2 — High | 7.0–8.9 | SSRF (internal), stored XSS, IDOR on sensitive data, JWT forgery |
| P3 — Medium | 4.0–6.9 | Reflected XSS, open redirect, info disclosure, CSRF |
| P4 — Low | 0.1–3.9 | Missing security headers, verbose errors, self-XSS |
| INFO | N/A | Interesting findings below P4 threshold |
