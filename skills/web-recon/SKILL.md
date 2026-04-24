---
name: web-recon
description: Web content discovery and technology fingerprinting using gobuster, ffuf, feroxbuster, katana, httpx, and wafw00f
---

# web-recon

Web reconnaissance workflow for NyxStrike. Use this skill when a user wants to find hidden directories, endpoints, virtual hosts, crawl a web application, or detect the tech stack and WAF.

## Workflow

### 1. WAF detection (wafw00f)

Always check for a WAF first — it influences wordlist choice, rate, and evasion flags.

```
run_tool(tool="wafw00f", url="https://<target>")
```

If a WAF is detected, add evasion flags to subsequent tools (e.g. `--random-agent`, lower thread count).

### 2. HTTP probing and tech detection (httpx)

Fingerprint live hosts, status codes, titles, and tech stack before brute-forcing.

```
run_tool(tool="httpx", target="<target>", probe=true, tech_detect=true, title=true, status_code=true)
```

Use the tech stack findings to choose targeted wordlists:
- WordPress → use `wp-content`, `wp-admin` wordlists
- PHP → look for `.php` extensions
- Apache/Nginx → check for `.htaccess`, server-status

### 3. Directory and file discovery

**Fast sweep (ffuf)** — preferred for vhost and parameter fuzzing as well:

```
run_tool(tool="ffuf", url="https://<target>/FUZZ",
         wordlist="/usr/share/wordlists/dirb/common.txt",
         match_codes="200,204,301,302,307,401,403")
```

**Recursive discovery (feroxbuster)** — use when you need deep recursive scanning:

```
run_tool(tool="feroxbuster", url="https://<target>",
         wordlist="/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt",
         threads=10)
```

**Extension-aware scan (gobuster)** — use when tech stack is known:

```
run_tool(tool="gobuster", url="https://<target>",
         mode="dir",
         wordlist="/usr/share/wordlists/dirb/common.txt",
         additional_args="-x php,html,txt,bak")
```

### 4. Web crawling (katana)

Crawl the application for JS-embedded endpoints, forms, and parameters:

```
run_tool(tool="katana", url="https://<target>")
```

Feed discovered endpoints into vulnerability scanning (see `web-vuln` skill).

### 5. Virtual host enumeration

Use ffuf in vhost mode to discover hidden vhosts:

```
run_tool(tool="ffuf", url="https://<target>",
         mode="vhost",
         wordlist="/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt")
```

### 6. WordPress-specific scan (wpscan)

If WordPress is detected, run wpscan for plugin/theme vulns and user enumeration:

```
run_tool(tool="wpscan", url="https://<target>",
         additional_args="--enumerate u,p,t --plugins-detection aggressive")
```

## Wordlist selection guide

| Target type | Recommended wordlist |
|---|---|
| General dirs | `/usr/share/wordlists/dirb/common.txt` |
| Deep/thorough | `/usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt` |
| Files | `/usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt` |
| API endpoints | `/usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt` |
| Backup files | `/usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt` |
| Vhosts | `/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt` |

## NyxStrike Tool Reference

| Tool | Use case |
|---|---|
| `wafw00f` | WAF detection |
| `httpx` | HTTP probing, tech fingerprint |
| `ffuf` | Fast fuzzing (dirs, vhosts, params) |
| `feroxbuster` | Recursive content discovery |
| `gobuster` | Extension-aware dir/file brute-force |
| `katana` | Web crawling, JS endpoint extraction |
| `dirsearch` | Alternative web path scanner |
| `wpscan` | WordPress-specific enumeration |
