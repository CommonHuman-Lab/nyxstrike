<div align="center">

<img src="assets/nyxstrike-logo.png" alt="NyxStrike" width="220"/>

# NyxStrike
*Formerly known as Hexstrike AI Community Edition*

### AI-Powered Penetration Testing and Bug Bounty Automation Platform

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-AGPLv3-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Penetration%20Testing-red.svg)](https://github.com/CommonHuman-Lab/nyxstrike)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://github.com/CommonHuman-Lab/nyxstrike)

**AI-driven penetration testing and bug bounty automation platform that connects MCP-compatible LLM agents to 185+ real-world offensive security tools through a single REST API and web dashboard.**

[📡 Wiki](https://github.com/CommonHuman-Lab/nyxstrike/wiki)

<p align="center">
  <a href="https://discord.gg/aC8Q2xJFgp">
    <img src="https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white&style=for-the-badge" alt="Join Discord Community" />
  </a>
</p>

</div>

---

## What is NyxStrike?

NyxStrike is an open-source AI penetration testing platform that lets LLM agents — or human operators — orchestrate full security assessments, recon pipelines, exploit chains, and bug bounty workflows from a single interface. It bridges the gap between large language models and the real offensive security tooling professionals use: nmap, nuclei, sqlmap, Metasploit, Hydra, Burp alternatives, and more.

Whether you're running a CTF, a bug bounty campaign, or a professional penetration test, NyxStrike handles the orchestration through an intelligent attack-chain engine — so you can focus on results, not tool management.

### Architecture

```
LLM Agent (OpenCode / Claude / Cursor / VS Code)
      │  stdio
      ▼
nyxstrike_mcp.py  ──HTTP──►  nyxstrike_server.py  ──►  Security Tools
  (MCP client)                  (REST API :8888)         (nmap, nuclei,
                                 + React Dashboard         sqlmap, ...)
                                 + Intelligence Engine
```

---

## What Makes NyxStrike Stand Out?

NyxStrike is the only open-source platform that combines an AI-driven attack-chain planner, 185+ real security tools, and a full operator workbench — all accessible from a single MCP connection or web dashboard.

| Feature | Description |
|---|---|
| **Sessions & Operator Workbench** | Every engagement lives in a structured session with 4-tab workbench (Workflow, Findings, Notes, Timeline), artifact chaining, AI analysis, and report generation. 7 session creation modes including intelligence-planned, manual, and 4 AI-driven variants |
| **185+ Tools, One Interface** | Network recon, web exploitation, WiFi pentesting, binary analysis, cloud auditing, OSINT, password cracking, forensics, and more — all orchestrated through a single MCP connection |
| **Intelligent Attack-Chain Engine** | Catalog-driven planner with contextual learning, smarter tool ranking, attack-chain preview with tool selection reasons, and user-selectable precision (`quick`, `comprehensive`, `stealth`) before a session starts |
| **Artifact Chaining** | Step-by-step tool chaining with operator approval, confidence hints, and output mapping between steps — not just fire-and-forget |
| **Durable Session Handoff** | AI planning and manual dashboard execution share the same session state, so you can switch between agent-driven and hands-on control at any point |
| **Purpose-Built AI Agents** | Standalone agents for bug bounty workflows, CTF solving, CVE intelligence, exploit generation, vulnerability correlation, technology detection, rate-limit detection, and intelligent failure recovery |
| **9 Workflow Skills** | Pre-built playbooks (web recon, SMB enum, binary analysis, subdomain enum, cloud audit, exploitation, password cracking, and more) mounted as MCP resources the agent follows automatically |
| **Built-in Dashboard** | KPI cards, resource monitoring, tool availability by category, live process management (pause/resume/terminate), session workbench, notes, findings tracker, and report generation. No terminal required after setup |
| **Global Command Palette** | `Ctrl/Cmd+K` keyboard-first control: jump pages, trigger tools, compare previous runs |
| **Persistent Run History** | Server-side history survives browser refresh. Clears safely with confirmation |
| **Per-Tool Timeout Policies** | Inactivity watchdog and max runtime cap keep long-running scans from hanging |
| **Theme System** | One-click switcher with live preview: Dark Ops, Candy Pop, Solarized, Unicorn, Forest, and more |
| **LLM Flexibility** | Works with Ollama (local), OpenAI, and Anthropic out of the box |
| **Performance Modes** | `--compact` for lightweight/local LLM usage, `--profile` for targeted tool loading |

---

## Quick Start (Installation)

### Scripted Setup (recommended)

```bash
git clone https://github.com/CommonHuman-Lab/nyxstrike.git
cd nyxstrike

./nyxstrike.sh -a                  # Setup + start server
./nyxstrike.sh -a -t               # + install external tools
./nyxstrike.sh -a -t -ai           # + local AI model (~8.4 GB RAM)
./nyxstrike.sh -a -t -ai-small     # + smaller AI model (~2.5 GB RAM)
```

> Full flag reference: [Wiki — Installation & Flags](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Installation-and-Flags)

### Verify Setup

```bash
curl http://localhost:8888/health
```

Then open [http://localhost:8888](http://localhost:8888) to access the dashboard.

> Some tools (e.g. `nmap`, `masscan`) require elevated privileges for specific scan modes. Use a dedicated test VM and least-privilege setup where possible.

---

## MCP Integrations

Connect NyxStrike to any MCP-compatible AI client.

**Supported clients:** OpenCode, Cursor, Claude Desktop, VS Code Copilot, Roo Code, and any MCP-compatible agent.

### Universal MCP Command

```bash
/path/to/nyxstrike/nyxstrike-env/bin/python3 \
  /path/to/nyxstrike/nyxstrike_mcp.py \
  --server http://127.0.0.1:8888 \
  --profile full
```

### OpenCode

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "nyxstrike": {
      "type": "local",
      "command": [
        "/path/to/nyxstrike/nyxstrike-env/bin/python3",
        "/path/to/nyxstrike/nyxstrike_mcp.py",
        "--server",
        "http://127.0.0.1:8888",
        "--profile",
        "full"
      ],
      "enabled": true
    }
  }
}
```

<details>
<summary>Claude Desktop / Cursor</summary>

Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nyxstrike": {
      "command": "/path/to/nyxstrike/nyxstrike-env/bin/python3",
      "args": [
        "/path/to/nyxstrike/nyxstrike_mcp.py",
        "--server",
        "http://localhost:8888",
        "--profile",
        "full"
      ],
      "description": "NyxStrike",
      "timeout": 300,
      "disabled": false
    }
  }
}
```

</details>

<details>
<summary>VS Code Copilot</summary>

Configure `.vscode/settings.json`:

```json
{
  "servers": {
    "nyxstrike": {
      "type": "stdio",
      "command": "/path/to/nyxstrike/nyxstrike-env/bin/python3",
      "args": [
        "/path/to/nyxstrike/nyxstrike_mcp.py",
        "--server",
        "http://localhost:8888",
        "--profile",
        "full"
      ]
    }
  },
  "inputs": []
}
```

</details>

<details>
<summary>Security Configuration</summary>

By default the server binds to `127.0.0.1` (localhost only).

```bash
# Require Bearer auth on all requests
export NYXSTRIKE_API_TOKEN=your-secret-token

# Optionally expose to the network (NOT recommended without a token)
export NYXSTRIKE_HOST=0.0.0.0

python3 nyxstrike_server.py
```

> Full reference: [Wiki — Security Configuration](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Security-Configuration)

</details>

---

## Tool Arsenal

185+ tools across 12 categories, all accessible via MCP or the dashboard.

| Category | Example Tools | Count |
|---|---|---|
| Network Recon & Scanning | nmap, rustscan, masscan, amass, subfinder, assetfinder, shuffledns, massdns, autorecon, theHarvester, fierce, dnsenum, arp-scan, whois, dig, http-headers | 16 |
| Web Application Security | gobuster, ffuf, feroxbuster, dirsearch, dirb, wfuzz, httpx, testssl, katana, hakrawler, gospider, nuclei, nikto, sqlmap, dalfox, wpscan, jaeles, xsser, dotdotpwn, arjun, paramspider, x8, wafw00f, whatweb, burpsuite, zap, waymore, gau, waybackurls, anew, hurl, qsreplace, uro, commix | 34 |
| WiFi Penetration Testing | aircrack-ng, airmon-ng, airodump-ng, aireplay-ng, airbase-ng, airdecap-ng, hcxdumptool, hcxpcapngtool, eaphammer, wifite2, bettercap, mdk4 | 12 |
| Authentication & Passwords | hydra, john, hashcat, medusa, patator, hashid, ophcrack | 7 |
| SMB & Active Directory | enum4linux, enum4linux-ng, netexec, smbmap, nbtscan, rpcclient, ldapdomaindump, impacket suite | 10 |
| Binary Analysis & RE | gdb, radare2, ghidra, binwalk, checksec, strings, objdump, xxd, ropgadget, one-gadget, ropper, angr, pwntools, pwninit, libc-database, autopsy | 16 |
| Exploitation | metasploit, msfvenom, searchsploit, pwntools, pwninit, commix | 6 |
| Cloud & Container Security | prowler, scout-suite, cloudmapper, pacu, trivy, clair, docker-bench, kube-hunter, kube-bench, checkov, terrascan, falco | 12 |
| OSINT & Bug Bounty | sherlock, spiderfoot, sublist3r, parsero, joomscan, recon-ng, trufflehog | 7 |
| CTF & Forensics | volatility, volatility3, foremost, steghide, exiftool, hashpump, photorec, testdisk, scalpel, bulk_extractor, stegsolve, zsteg, outguess, sleuthkit | 14 |
| API Security | graphql-scanner, jwt-analyzer, api-fuzzer, api-schema-analyzer | 4 |
| Database Interaction | mysql, sqlite | 2 |

> Full per-tool details: [Wiki — Tool Arsenal](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Tool-Arsenal)

---

## Sessions & Operator Workbench

Sessions are the core unit of work in NyxStrike. Every scan, recon run, exploit chain, or bug bounty engagement lives inside a session — with full state, findings, notes, timeline, and AI analysis attached.

### Session Creation Modes

| Mode | What It Does |
|---|---|
| `intelligence` | Intelligent Decision Engine builds the full workflow from your target + objective |
| `manual` | You pick every tool and step yourself |
| `from_template` | Start from a saved session template |
| `ai_recon` | LLM-driven recon pipeline: subdomains → live hosts → ports → web surface |
| `ai_profiling` | Deep technology and service profiling on a known target |
| `ai_vuln` | Vulnerability hunting mode: high-impact CVEs, injection, logic flaws |
| `ai_osint` | OSINT collection: emails, employees, JS secrets, leaked credentials |

### Attack-Chain Preview

Before you start a session, the planner shows the full proposed workflow: step count, estimated time, risk level, and a per-tool breakdown — including objective match %, noise score, and what new capabilities each step unlocks. You can accept, tweak, or regenerate before a single packet is sent.

### Session Workbench (Tab Layout)

Once a session is running, the workbench gives you full operator control:

- **Workflow tab** — live step runner with stop-process, chain suggestions based on prior output, apply/remove tools, and per-tool timeout enforcement
- **Findings tab** — per-session vulnerability records (title, severity, CVE, evidence, recommendation, tags, status), with auto-recalculated risk level
- **Notes tab** — full CRUD notes with folders, full-text search, Markdown editor (SimpleMDE), `.md` file upload/download
- **Timeline tab** — chronological audit trail of every action taken in the session

### Artifact Chaining

After each step, the chain suggestion engine parses tool output for artifacts (URLs, IPs, domains, ports) and automatically maps them to the parameters of logical next steps — with confidence scoring. Sensitive parameters are blocked from auto-chaining. You review and approve before the next step runs.

### AI-Powered Session Features

| Feature | What It Does |
|---|---|
| **AI Session Analysis** | LLM reads the full run log and produces structured findings stored in the DB |
| **AI Follow-up Session** | LLM reviews prior findings and generates a prioritised follow-up workflow with tool, params, and reason for each step |
| **AI Session Report** | LLM writes an executive summary + structured report, saved to session notes. A floating `ReportGenerationBubble` tracks progress across page navigation |
| **Standard Report** | Structured Markdown report without LLM, instant |

> Deep dive: [Wiki — Dashboard and Sessions](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Dashboard-and-Sessions)

---

## Workflow Skills & Playbooks

9 workflow playbooks mounted as MCP resources — the agent follows these automatically:

| Skill | Description |
|---|---|
| `web-recon` | WAF detection → httpx probing → directory fuzzing → crawling → tech fingerprinting |
| `web-vuln` | SQLi, XSS, SSTI, and generic CVE scanning workflow |
| `nmap-recon` | Network scanning with rustscan + nmap + masscan pipeline |
| `subdomain-enum` | Passive + active subdomain discovery and DNS validation |
| `smb-enum` | Windows/SMB enumeration, share discovery, and user enumeration |
| `binary-analysis` | checksec → strings → binwalk → radare2 → gdb workflow |
| `exploitation` | Metasploit, msfvenom, and Exploit-DB exploit development |
| `password-cracking` | Hash identification → john/hashcat cracking → brute-force escalation |
| `cloud-audit` | AWS/GCP/Azure assessment with prowler, trivy, and kube-hunter |

---

## Usage Examples

Here's what a typical NyxStrike session looks like when driven by an LLM agent. Always state authorization, ownership, and scope explicitly when prompting:

```
You: I am an authorized security researcher. My company owns example.com and I want
     to run an authorized penetration test using NyxStrike. Start with recon and web
     vulnerability discovery, then propose next steps based on findings.

AI:  Confirmed. Starting with passive subdomain enumeration via subfinder and amass,
     followed by httpx probing, directory fuzzing with ffuf, and nuclei vulnerability
     scanning. I will summarize findings and recommend validated follow-up actions.
```

> More examples: [Wiki — Usage Examples](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Usage-Examples)

---

## Security Considerations

> **This platform gives AI agents access to powerful offensive security tooling.**

- Run in an isolated environment or dedicated security testing VM.
- AI agents can execute arbitrary commands — maintain operator oversight at all times.
- Monitor activity through the real-time dashboard and log stream.
- Enable `NYXSTRIKE_API_TOKEN` for any non-localhost deployment.

### Legal & Ethical Use

| Allowed | Not Allowed |
|---|---|
| Authorized penetration testing (with written authorization) | Unauthorized testing of any system |
| Bug bounty programs (within program scope and rules) | Malicious, illegal, or harmful activities |
| CTF competitions and educational environments | Unauthorized data access or exfiltration |
| Security research on owned or authorized systems | |
| Red team exercises (with organizational approval) | |

---

## License

Licensed under the [AGPLv3](LICENSE). You are free to use, modify, and distribute this software. If you run it as a service or distribute it, the source must remain open. For commercial licensing that does not require open-sourcing your changes, contact the author.

---

## Credits

NyxStrike is built on top of **[hexstrike-ai](https://github.com/0x4m4/hexstrike-ai)** by **0x4m4**.
