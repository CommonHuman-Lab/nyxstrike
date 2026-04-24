---
description: Internal HTB shared contract (tool policy). Not user-selectable.
mode: subagent
hidden: true
---

# HTB CTF — Tool Policy

Maps attack phases to NyxStrike MCP tools. Each specialist agent uses this as its canonical reference for which tools to reach for and in what order.

All tools are invoked via the NyxStrike MCP `run_tool` gateway:
```
run_tool(tool_name="<name>", params={...})
```

---

## RECON Phase

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `rustscan_port_scan` | Fast full-port sweep | `target`, `ports="1-65535"` |
| 2 | `nmap_scan` | Service/version/script on open ports | `target`, `ports=<open>`, `scan_type="-sV -sC"` |
| 3 | `masscan_scan` | Large CIDR / when rustscan slow | `target`, `ports="0-65535"`, `rate=1000` |
| 4 | `autorecon_scan` | Full automated recon suite | `target`, `output_dir="/tmp/htb-<t>/autorecon"` |
| 5 | `whois_lookup` | Domain/IP ownership info | `target` |
| 6 | `theharvester_scan` | OSINT email/host gathering | `domain` |

---

## ENUM — Web (port 80/443/8080/8443/8000)

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `wafw00f_scan` | WAF detection before fuzzing | `target` |
| 2 | `httpx_probe` | Tech fingerprint, headers, status | `target`, `tech_detect=true`, `title=true` |
| 3 | `ffuf_scan` | Directory/file fuzzing | `url`, `wordlist`, `match_codes` |
| 4 | `feroxbuster_scan` | Recursive deep discovery | `url`, `wordlist`, `threads=10` |
| 5 | `katana_crawl` | JS-aware endpoint crawl | `url`, `depth=3`, `js_crawl=true` |
| 6 | `gobuster_scan` | Extension-aware enumeration | `url`, `mode="dir"`, `additional_args="-x php,html,txt,bak"` |
| 7 | `nikto_scan` | Server misconfig & CVE scan | `target` |
| 8 | `nuclei_scan` | Template-based vuln sweep | `target`, `severity="critical,high,medium"` |
| 9 | `wpscan_analyze` | WordPress-specific (if WP detected) | `url`, `additional_args="--enumerate u,p,t"` |
| 10 | `gau_discovery` | Historical URL discovery | `domain` |
| 11 | `waybackurls_discovery` | Wayback Machine URLs | `domain` |
| 12 | `hakrawler_crawl` | Fast endpoint harvester | `url`, `depth=2` |

---

## ENUM — API (GraphQL / REST / JWT)

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `httpx_probe` | Probe API base path | `target` |
| 2 | `arjun_discover` | Hidden parameter discovery | `url`, `method="GET"` |
| 3 | `api_schema_analyzer` | Parse OpenAPI/Swagger docs | `api_url`, `spec_file` |
| 4 | `graphql_scanner` | GraphQL introspection + vulns | `url`, `introspection=true` |
| 5 | `jwt_analyzer` | JWT decode/crack/forge | `token` |
| 6 | `api_fuzzer` | Endpoint fuzzing | `target_url`, `wordlist` |
| 7 | `comprehensive_api_audit` | Full automated API audit | `api_url` |
| 8 | `x8_discover` | Hidden param brute-force | `url`, `wordlist` |

---

## ENUM — Service (SMB / FTP / SSH / RPC)

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `enum4linux_scan` | SMB/Samba full enumeration | `target`, `additional_args="-a"` |
| 2 | `smbmap_scan` | SMB share listing | `target` |
| 3 | `netexec_scan` | CrackMapExec successor | `target`, `protocol="smb"` |
| 4 | `nbtscan_netbios` | NetBIOS name scan | `target` |
| 5 | `rpcclient_enumeration` | RPC domain user enum | `target` |
| 6 | `enum4linux_ng_advanced` | Advanced SMB (with creds) | `target`, `username`, `password` |
| 7 | `nmap_scan` | NSE scripts per service | `target`, `ports`, `additional_args="--script <scripts>"` |

SMB NSE scripts to use: `smb-vuln-*,smb-enum-shares,smb-enum-users`
FTP NSE scripts: `ftp-anon,ftp-bounce`
SSH NSE scripts: `ssh-hostkey,ssh-auth-methods`

---

## FOOTHOLD — Credential Attacks

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `hydra_attack` | Network brute-force | `target`, `service`, `username`, `password` |
| 2 | `medusa_attack` | Parallel brute-force | `target`, `module`, `username`, `password` |
| 3 | `netexec_scan` | SMB/WinRM spray | `target`, `protocol`, `username`, `password` |
| 4 | `patator_attack` | Multi-protocol brute-force | `module`, `target` |

---

## FOOTHOLD — Exploitation

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `search_exploit_db` | Find public exploits | `query="<service> <version>"` |
| 2 | `nuclei_scan` | CVE template exploitation | `target`, `tags="cve"`, `severity="critical"` |
| 3 | `sqlmap_scan` | SQL injection to shell | `url`, `additional_args="--batch --os-shell"` |
| 4 | `metasploit_run` | Framework exploitation | `module`, `options` |
| 5 | `msfvenom_generate` | Payload generation | `payload`, `lhost`, `lport`, `format` |
| 6 | `pwntools_execute` | Custom exploit script | `script`, `remote_host` |

---

## FOOTHOLD — Web Exploitation

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `sqlmap_scan` | SQLi detection + dump | `url`, `data`, `additional_args="--batch --dbs"` |
| 2 | `dalfox_xss_scan` | XSS to session theft | `url` |
| 3 | `dotdotpwn_scan` | Path traversal | `target`, `additional_args="-m http"` |
| 4 | `jaeles_vulnerability_scan` | Multi-step vuln chains | `url` |
| 5 | `http_framework_test` | Custom HTTP exploitation | `url`, `method`, `data`, `action` |
| 6 | `browser_agent_inspect` | JS-heavy app interaction | `url`, `active_tests=true` |

---

## PRIVESC — Linux

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `file_operations` | Upload/run linpeas.sh | `operation="write"` |
| 2 | `metasploit_run` | Post exploitation modules | `module="post/multi/recon/local_exploit_suggester"` |
| 3 | `search_exploit_db` | Kernel CVE lookup | `query="Linux kernel <version>"` |
| 4 | `pwntools_execute` | Custom privesc exploit | `script` |

---

## PRIVESC — Windows

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `file_operations` | Upload/run winpeas.exe | `operation="write"` |
| 2 | `metasploit_run` | Post exploitation modules | `module="post/multi/recon/local_exploit_suggester"` |
| 3 | `netexec_scan` | Lateral movement | `target`, `protocol="smb"` |
| 4 | `smbmap_scan` | Share access with new creds | `target`, `username`, `password` |
| 5 | `search_exploit_db` | Windows kernel CVE | `query="Windows <version>"` |

---

## HASH / CRYPTO

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `hashid` | Identify hash type | `hash_value` |
| 2 | `john_crack` | Fast crack with rules | `hash_file`, `wordlist`, `format_type` |
| 3 | `hashcat_crack` | GPU crack | `hash_file`, `hash_type`, `attack_mode`, `wordlist` |
| 4 | `hashpump_attack` | Hash length extension | `signature`, `data`, `key_length` |
| 5 | `ophcrack_crack` | NTLM rainbow tables | `hash_file`, `tables_dir` |

---

## FORENSICS / STEGO

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `binwalk_scan` | Embedded file extraction | `file_path`, `extract=true` |
| 2 | `strings_extract` | Printable string extraction | `file_path` |
| 3 | `exiftool_extract` | Metadata extraction | `file_path` |
| 4 | `steghide_analysis` | Stego embed/extract | `action`, `cover_file`, `passphrase` |
| 5 | `foremost_carve` | File carving | `image_file`, `output_dir` |
| 6 | `volatility3_analyze` | Memory forensics | `memory_image`, `plugin` |
| 7 | `xxd_hexdump` | Hex inspection | `file_path`, `bytes_to_read` |

---

## BINARY / PWN

| Priority | Tool | Purpose | Key Params |
|----------|------|---------|------------|
| 1 | `checksec_analyze` | Mitigation check | `binary_path` |
| 2 | `strings_extract` | Quick recon | `file_path` |
| 3 | `ghidra_analyze` | Full decompilation | `binary_path` |
| 4 | `gdb_debug` | Dynamic analysis | `binary_path`, `commands` |
| 5 | `angr_analysis` | Symbolic execution | `binary_path`, `find_addr` |
| 6 | `ropgadget_search` | ROP chain building | `binary_path` |
| 7 | `ropper_search` | Gadget search | `binary_path`, `search` |
| 8 | `one_gadget_search` | One-gadget RCE | `libc_path` |
| 9 | `libc_database_search` | Libc offset lookup | `search_type`, `value` |
| 10 | `pwninit_patch` | Patch binary with target libc | `binary_path`, `libc_path` |
| 11 | `pwntools_execute` | Run exploit script | `script`, `remote_host` |
