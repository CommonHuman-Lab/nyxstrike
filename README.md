<div align="center">

<img src="assets/nyxstrike-logo.png" alt="NyxStrike" width="220"/>

# NyxStrike
*Previously: Hexstrike AI Community Edition**

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

Connect NyxStrike to any MCP-compatible AI client — OpenCode, Cursor, Claude Desktop, VS Code Copilot, Roo Code, and more.

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

> Config snippets for Claude Desktop, Cursor, VS Code Copilot, and security options: [Wiki — MCP Setup](https://github.com/CommonHuman-Lab/nyxstrike/wiki/MCP-Setup)

---

## What Makes NyxStrike Stand Out?

| Feature | Description |
|---|---|
| **Built-in AI Assistant** | Chat widget available on every page — start a conversation without leaving your workflow. Powered by Ollama, OpenAI, or Anthropic |
| **185+ Tools, One Interface** | Network recon, web exploitation, WiFi pentesting, binary analysis, cloud auditing, OSINT, password cracking, forensics, and more — all orchestrated through a single MCP connection |
| **Intelligent Attack-Chain Engine** | Catalog-driven planner with contextual learning, attack-chain preview with tool selection reasons, and user-selectable precision (`quick`, `comprehensive`, `stealth`) before a session starts |
| **Sessions & Operator Workbench** | Every engagement lives in a structured session with 4-tab workbench (Workflow, Findings, Notes, Timeline), artifact chaining, AI analysis, and report generation |
| **Purpose-Built AI Agents** | Standalone agents for bug bounty, CTF, CVE intelligence, exploit generation, OSINT, and more — with intelligent failure recovery |

> [Full feature breakdown](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Features)

---

## Tool Arsenal

185+ tools across 12 categories — network recon, web exploitation, WiFi pentesting, binary analysis, cloud auditing, SMB/AD, OSINT, password cracking, CTF forensics, API security, exploitation, and more.

> [Full tool list by category](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Tool-Arsenal)

---

## Sessions & Operator Workbench

Every engagement lives in a structured session with a 4-tab workbench (Workflow, Findings, Notes, Timeline), artifact chaining, AI analysis, and report generation. Choose from 7 session creation modes — including intelligence-planned, manual, and 4 AI-driven variants. After each step, the chain engine maps tool output to the next logical action for operator review and approval.

> [Full session & workbench docs](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Dashboard-and-Sessions)

---

## Workflow Skills & Playbooks

9 pre-built playbooks (web recon, web vuln, nmap recon, subdomain enum, SMB enum, binary analysis, exploitation, password cracking, cloud audit) mounted as MCP resources — the agent follows these automatically.

> [Full playbook details](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Skills)

---

## Usage Examples

Always state authorization, ownership, and scope explicitly when prompting. See the wiki for full prompt examples across recon, exploitation, bug bounty, and CTF workflows.

> [Usage examples](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Usage-Examples)

---

## Architecture

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

Originally inspired by [hexstrike-ai](https://github.com/0x4m4/hexstrike-ai).
