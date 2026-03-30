<div align="center">

<img src="assets/hex_logo.png" alt="HexStrike" width="220"/>

# HexStrike AI - Community Edition
### AI-Powered MCP Cybersecurity Automation Platform

[![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-AGPLv3-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Penetration%20Testing-red.svg)](https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition)

**Advanced AI-powered penetration testing MCP framework, on-demand TTP knowledge, and adaptive scanning intelligence**

[📡 Wiki](https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition/wiki)

<p align="center">
  <a href="https://discord.gg/aC8Q2xJFgp">
    <img src="https://img.shields.io/badge/Discord-Join-7289DA?logo=discord&logoColor=white&style=for-the-badge" alt="Join Discord Community" />
  </a>
</p>

</div>

## 🚀 Differences from HexStrike V6

- Many new tools, workflows, skills and end-to-end agent workflows added!
- **Web Dashboard**: Monitor health, tools, live logs, run tools, export artifacts and much more without touching the terminal.
- **Compact Mode**: Great for running with smaller, local LLMs.
- **Profile Mode**: Specify one or more profiles to load only the relevant ones for your workflow.
- Refactored Codebase: Improved clarity, maintainability, and performance.
- Updated Dependencies: All packages upgraded for security and compatibility.
- Enhanced Tool Usage: Smarter parameter handling, improved documentation, and endpoint references.
- AI Integration: Upgraded MCP compatibility and agent orchestration (FastMCP v3).

### Details

<details>
<summary>Web Dashboard</summary>

Served automatically at `http://localhost:8888` the moment the server starts — no extra setup required.

**What you get:**

- **Dashboard** — KPI cards for tools installed, command telemetry, uptime and more.
- **Tool Run** — Run any tool, straight from the dashboard!
- **Reports** — Searchable, filterable tool run history, with export.
- **Tool Registry** — Searchable, filterable for all registered tools. Click any tool for more details.
- **Server Logs** — near-realtime SSE log stream.
- **Help** — IDE/agent configuration snippets for Claude Desktop, VS Code Copilot, Cursor, and OpenCode.
- **And much more!**

<img src="assets/screenshots/dashboard.png" alt="dashboard" style="margin-bottom: 20px;"/>

<img src="assets/screenshots/reports.png" alt="reports" style="margin-bottom: 20px;"/>

<img src="assets/screenshots/tools.png" alt="reports" style="margin-bottom: 20px;"/>

<img src="assets/screenshots/run_tool.png" alt="reports" style="margin-bottom: 20px;"/>

</details>

<details>
<summary>Compact Mode (--compact)</summary>

> Activate Compact Mode for the MCP server using the `--compact` flag.
> See [Flags](https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition/wiki/Flags) for more info

- 🚦 Only the two essential gateway tools are loaded—perfect for lightweight deployments, automation pipelines, or running on resource-constrained systems.
- 🏃 Great for running with smaller, local LLMs or when you want minimal overhead.

</details>

<details>
<summary>Profile Mode (--profile)</summary>

> Specify one or more profiles to load only the relevant ones for your workflow.
> See [Profile flags](https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition/wiki/Profile-Flags) for more info

- 🚀 Select profiles for targeted workflows to speed up scans and reduce resource usage.
- 🌐 Use --profile full to enable the complete arsenal, it's on default out-the-box for the recommended set.

</details>

<details>
<summary>End-to-end Agents</summary>

> See [Agents](https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition/wiki/Agents) for more info

#### HTB CTF Agent System (@htb-ctf)

A 14-specialist agent system built natively for **OpenCode**, designed to autonomously solve HTB machines and CTF challenges end-to-end.

#### Bug Bounty Agent System (@bugbounty)

A 7-specialist agent system built natively for **OpenCode**, designed for autonomous bug bounty hunting across web, API, and broad wildcard scopes.

#### Recon Agent System (@recon)

A 5-specialist agent system built natively for **OpenCode**, designed for pure read-only information gathering across domains, IP addresses, web applications, and APIs.

</details>

## Installation

### Quick Setup & Run Hexstrike Server

> **Note:** Many tools (nmap, masscan, etc.) require elevated privileges for certain scan types. You can either run the setup as `root`, or grant individual tool capabilities (e.g. `setcap cap_net_raw+ep /usr/bin/nmap`). Running as root is simpler but less secure.

```bash
# 1. Clone the repository
git clone https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition.git
cd hexstrike-ai-community-edition

# 2. Create virtual environment
python3 -m venv hexstrike-env
source hexstrike-env/bin/activate        # Linux/Mac
# sudo source hexstrike-env/bin/activate # Linux as root
# hexstrike-env\Scripts\activate         # Windows

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Start the API server
python3 hexstrike_server.py

# 5. Dashboard automatically at http://localhost:8888

# 6. In a separate terminal, start the MCP client
# (use the venv python to ensure dependencies are available)
hexstrike-env/bin/python3 hexstrike_mcp.py --server http://localhost:8888 --profile full
```

> See [Flags](https://github.com/CommonHuman-Lab/hexstrike-ai-community-edition/wiki/Flags) on how to customize the experience.

### Verify Installation

```bash
# Browse to http://localhost:8888

# Test server API health
curl http://localhost:8888/health
```

### Use Hexstrike

#### Installation & Demo Video

Watch the full installation and setup walkthrough here: [YouTube - HexStrike AI Installation & Demo](https://www.youtube.com/watch?v=pSoftCagCm8)

<details>
<summary>Supported AI Clients for Running & Integration</summary>

You can install and run HexStrike AI MCPs with various AI clients, including:

- **5ire (Latest version v0.14.0 not supported for now)**
- **VS Code Copilot**
- **Roo Code**
- **Cursor**
- **Claude Desktop**
- **OpenCode**
- **Any MCP-compatible agent**

Refer to the video above for step-by-step instructions and integration examples for these platforms.

</details>

<details>
<summary>Claude Desktop Integration or Cursor</summary>

Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hexstrike-ai": {
      "command": "/path/to/hexstrike-ai/hexstrike-env/bin/python3",
      "args": [
        "/path/to/hexstrike-ai/hexstrike_mcp.py",
        "--server",
        "http://localhost:8888",
        "--profile",
        "full"
      ],
      "description": "HexStrike AI Community Edition",
      "timeout": 300,
      "disabled": false
    }
  }
}
```
</details>

<details>
<summary>VS Code Copilot Integration</summary>

Configure VS Code settings in `.vscode/settings.json`:

```json
{
  "servers": {
    "hexstrike": {
      "type": "stdio",
      "command": "/path/to/hexstrike-ai/hexstrike-env/bin/python3",
      "args": [
        "/path/to/hexstrike-ai/hexstrike_mcp.py",
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
<summary>OpenCode Integration</summary>

Configure OpenCode settings in `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "hexstrike-ai": {
      "type": "local",
      "command": ["/path/to/hexstrike-ai/hexstrike_env/bin/python3",
        "/path/to/hexstrike-ai/hexstrike_mcp.py",
        "--server",
        "http://localhost:8888",
        "--profile",
        "full"
      ],
      "enabled": true
    }
  }
}
```
</details>

---

### Security Configuration

<details>
<summary>Network Binding</summary>

By default, the server binds to `127.0.0.1` (localhost only). To configure security:

```bash
# Set an API token (server will require Bearer auth on all requests)
export HEXSTRIKE_API_TOKEN=your-secret-token

# Optionally bind to all interfaces (NOT recommended without a token)
export HEXSTRIKE_HOST=0.0.0.0

# Start the server
python3 hexstrike_server.py
```

</details>

## Features

### Security Tools Arsenal

**Categories:**

<details>
<summary><b>🤖 Automated Recon & Enumeration</b></summary>

- **BBot** – AI-powered reconnaissance and enumeration framework supporting subdomain discovery, module filtering, and safe/fast scanning

</details>

<details>
<summary><b>🗄️ Database Interaction & Querying</b></summary>

- **MySQL Query** – Direct SQL querying and enumeration for MySQL/MariaDB databases
- **PostgreSQL Query** – Direct SQL querying and enumeration for PostgreSQL databases
- **SQLite Query** – Local file-based SQL querying for SQLite databases

</details>

<details>
<summary><b>🔍 Network Reconnaissance & Scanning</b></summary>

- **Nmap** - Advanced port scanning with custom NSE scripts and service detection
- **Rustscan** - Ultra-fast port scanner with intelligent rate limiting
- **Masscan** - High-speed Internet-scale port scanning with banner grabbing
- **AutoRecon** - Comprehensive automated reconnaissance with 35+ parameters
- **Amass** - Advanced subdomain enumeration and OSINT gathering
- **Subfinder** - Fast passive subdomain discovery with multiple sources
- **Fierce** - DNS reconnaissance and zone transfer testing
- **DNSEnum** - DNS information gathering and subdomain brute forcing
- **TheHarvester** - Email and subdomain harvesting from multiple sources
- **ARP-Scan** - Network discovery using ARP requests
- **NBTScan** - NetBIOS name scanning and enumeration
- **RPCClient** - RPC enumeration and null session testing
- **Whois** - Domain and IP registration lookup for ownership and OSINT
- **Enum4linux** - SMB enumeration with user, group, and share discovery
- **Enum4linux-ng** - Advanced SMB enumeration with enhanced logging
- **SMBMap** - SMB share enumeration and exploitation
- **Responder** - LLMNR, NBT-NS and MDNS poisoner for credential harvesting
- **NetExec** - Network service exploitation framework (formerly CrackMapExec)

</details>

<details>
<summary><b>📡 WiFi Penetration Testing</b></summary>

- Aircrack-ng Suite:
- Aircrack-ng - WPA/WPA2 PSK cracking from captured handshakes using dictionary attacks
- Airmon-ng - Enable/disable monitor mode and kill interfering processes
- Airodump-ng - Passive 802.11 packet capture for AP discovery and WPA handshake collection
- Aireplay-ng - Packet injection for deauthentication, fake authentication, and ARP replay attacks
- Airbase-ng - Rogue/soft access point creation for Evil Twin and client capture attacks
- Airdecap-ng - Decrypt WEP/WPA/WPA2 encrypted pcap capture files

*Modern WiFi Tools:*

- hcxdumptool - Clientless PMKID capture and WPA/WPA2 handshake collection (v7.0.0+)
- hcxpcapngtool - Convert hcxdumptool pcapng output to hashcat -m 22000 format
- EAPHammer - WPA-Enterprise Evil Twin for harvesting 802.1X EAP credentials
- Wifite2 - Automated WiFi auditing with PMKID, handshake, and WPS attack support
- Bettercap - WiFi recon, deauthentication, and Evil Twin via Bettercap wifi module
- mdk4 - 802.11 protocol stress testing and WIDS/WIPS evasion validation

</details>

<details>
<summary><b>🌐 Web Application Security Testing</b></summary>

- **Gobuster** - Directory, file, and DNS enumeration with intelligent wordlists
- **Dirsearch** - Advanced directory and file discovery with enhanced logging
- **Feroxbuster** - Recursive content discovery with intelligent filtering
- **FFuf** - Fast web fuzzer with advanced filtering and parameter discovery
- **Dirb** - Comprehensive web content scanner with recursive scanning
- **HTTPx** - Fast HTTP probing and technology detection
- **Katana** - Next-generation crawling and spidering with JavaScript support
- **Hakrawler** - Fast web endpoint discovery and crawling
- **Gau** - Get All URLs from multiple sources (Wayback, Common Crawl, etc.)
- **Waybackurls** - Historical URL discovery from Wayback Machine
- **Nuclei** - Fast vulnerability scanner with 4000+ templates
- **Nikto** - Web server vulnerability scanner with comprehensive checks
- **SQLMap** - Advanced automatic SQL injection testing with tamper scripts
- **WPScan** - WordPress security scanner with vulnerability database
- **Arjun** - HTTP parameter discovery with intelligent fuzzing
- **ParamSpider** - Parameter mining from web archives
- **X8** - Hidden parameter discovery with advanced techniques
- **Jaeles** - Advanced vulnerability scanning with custom signatures
- **Dalfox** - Advanced XSS vulnerability scanning with DOM analysis
- **Wafw00f** - Web application firewall fingerprinting
- **TestSSL** - SSL/TLS configuration testing and vulnerability assessment
- **SSLScan** - SSL/TLS cipher suite enumeration
- **SSLyze** - Fast and comprehensive SSL/TLS configuration analyzer
- **Anew** - Append new lines to files for efficient data processing
- **QSReplace** - Query string parameter replacement for systematic testing
- **Uro** - URL filtering and deduplication for efficient testing
- **Whatweb** - Web technology identification with fingerprinting
- **JWT-Tool** - JSON Web Token testing with algorithm confusion
- **GraphQL-Voyager** - GraphQL schema exploration and introspection testing
- **Burp Suite Extensions** - Custom extensions for advanced web testing
- **ZAP Proxy** - OWASP ZAP integration for automated security scanning
- **Wfuzz** - Web application fuzzer with advanced payload generation
- **Commix** - Command injection exploitation tool with automated detection
- **NoSQLMap** - NoSQL injection testing for MongoDB, CouchDB, etc.
- **Tplmap** - Server-side template injection exploitation tool

**🌐 Advanced Browser Agent:**

- **Headless Chrome Automation** - Full Chrome browser automation with Selenium
- **Screenshot Capture** - Automated screenshot generation for visual inspection
- **DOM Analysis** - Deep DOM tree analysis and JavaScript execution monitoring
- **Network Traffic Monitoring** - Real-time network request/response logging
- **Security Header Analysis** - Comprehensive security header validation
- **Form Detection & Analysis** - Automatic form discovery and input field analysis
- **JavaScript Execution** - Dynamic content analysis with full JavaScript support
- **Proxy Integration** - Seamless integration with Burp Suite and other proxies
- **Multi-page Crawling** - Intelligent web application spidering and mapping
- **Performance Metrics** - Page load times, resource usage, and optimization insights

</details>

<details>
<summary><b>🔐 Authentication & Password Security</b></summary>

- **Hydra** - Network login cracker supporting 50+ protocols
- **John the Ripper** - Advanced password hash cracking with custom rules
- **Hashcat** - World's fastest password recovery tool with GPU acceleration
- **Medusa** - Speedy, parallel, modular login brute-forcer
- **Patator** - Multi-purpose brute-forcer with advanced modules
- **NetExec** - Swiss army knife for pentesting networks
- **SMBMap** - SMB share enumeration and exploitation tool
- **Evil-WinRM** - Windows Remote Management shell with PowerShell integration
- **HashID** - Advanced hash algorithm identifier with confidence scoring
- **CrackStation** - Online hash lookup integration
- **Ophcrack** - Windows password cracker using rainbow tables

</details>

<details>
<summary><b>🔬 Binary Analysis & Reverse Engineering</b></summary>

- **GDB** - GNU Debugger with Python scripting and exploit development support
- **GDB-PEDA** - Python Exploit Development Assistance for GDB
- **GDB-GEF** - GDB Enhanced Features for exploit development
- **Radare2** - Advanced reverse engineering framework with comprehensive analysis
- **Ghidra** - NSA's software reverse engineering suite with headless analysis
- **IDA Free** - Interactive disassembler with advanced analysis capabilities
- **Binary Ninja** - Commercial reverse engineering platform
- **Binwalk** - Firmware analysis and extraction tool with recursive extraction
- **ROPgadget** - ROP/JOP gadget finder with advanced search capabilities
- **Ropper** - ROP gadget finder and exploit development tool
- **One-Gadget** - Find one-shot RCE gadgets in libc
- **Checksec** - Binary security property checker with comprehensive analysis
- **Strings** - Extract printable strings from binaries with filtering
- **Objdump** - Display object file information with Intel syntax
- **Readelf** - ELF file analyzer with detailed header information
- **XXD** - Hex dump utility with advanced formatting
- **Hexdump** - Hex viewer and editor with customizable output
- **Pwntools** - CTF framework and exploit development library
- **Angr** - Binary analysis platform with symbolic execution
- **Libc-Database** - Libc identification and offset lookup tool
- **Pwninit** - Automate binary exploitation setup
- **Volatility** - Advanced memory forensics framework
- **MSFVenom** - Metasploit payload generator with advanced encoding
- **UPX** - Executable packer/unpacker for binary analysis

</details>

<details>
<summary><b>☁️ Cloud & Container Security</b></summary>

- **Prowler** - AWS/Azure/GCP security assessment with compliance checks
- **Scout Suite** - Multi-cloud security auditing for AWS, Azure, GCP, Alibaba Cloud
- **CloudMapper** - AWS network visualization and security analysis
- **Pacu** - AWS exploitation framework with comprehensive modules
- **Trivy** - Comprehensive vulnerability scanner for containers and IaC
- **Clair** - Container vulnerability analysis with detailed CVE reporting
- **Kube-Hunter** - Kubernetes penetration testing with active/passive modes
- **Kube-Bench** - CIS Kubernetes benchmark checker with remediation
- **Docker Bench Security** - Docker security assessment following CIS benchmarks
- **Falco** - Runtime security monitoring for containers and Kubernetes
- **Checkov** - Infrastructure as code security scanning
- **Terrascan** - Infrastructure security scanner with policy-as-code
- **CloudSploit** - Cloud security scanning and monitoring
- **AWS CLI** - Amazon Web Services command line with security operations
- **Azure CLI** - Microsoft Azure command line with security assessment
- **GCloud** - Google Cloud Platform command line with security tools
- **Kubectl** - Kubernetes command line with security context analysis
- **Helm** - Kubernetes package manager with security scanning
- **Istio** - Service mesh security analysis and configuration assessment
- **OPA** - Policy engine for cloud-native security and compliance

</details>

<details>
<summary><b>🏆 CTF & Forensics Tools</b></summary>

- **Volatility** - Advanced memory forensics framework with comprehensive plugins
- **Volatility3** - Next-generation memory forensics with enhanced analysis
- **Foremost** - File carving and data recovery with signature-based detection
- **PhotoRec** - File recovery software with advanced carving capabilities
- **TestDisk** - Disk partition recovery and repair tool
- **Steghide** - Steganography detection and extraction with password support
- **Stegsolve** - Steganography analysis tool with visual inspection
- **Zsteg** - PNG/BMP steganography detection tool
- **Outguess** - Universal steganographic tool for JPEG images
- **ExifTool** - Metadata reader/writer for various file formats
- **Binwalk** - Firmware analysis and reverse engineering with extraction
- **Scalpel** - File carving tool with configurable headers and footers
- **Bulk Extractor** - Digital forensics tool for extracting features
- **Autopsy** - Digital forensics platform with timeline analysis
- **Sleuth Kit** - Collection of command-line digital forensics tools

**Cryptography & Hash Analysis:**

- **John the Ripper** - Password cracker with custom rules and advanced modes
- **Hashcat** - GPU-accelerated password recovery with 300+ hash types
- **HashID** - Hash type identification with confidence scoring
- **CyberChef** - Web-based analysis toolkit for encoding and encryption
- **Cipher-Identifier** - Automatic cipher type detection and analysis
- **Frequency-Analysis** - Statistical cryptanalysis for substitution ciphers
- **RSATool** - RSA key analysis and common attack implementations
- **FactorDB** - Integer factorization database for cryptographic challenges

</details>

<details>
<summary><b>🔥 Bug Bounty & OSINT Arsenal</b></summary>

- **Amass** - Advanced subdomain enumeration and OSINT gathering
- **Subfinder** - Fast passive subdomain discovery with API integration
- **Hakrawler** - Fast web endpoint discovery and crawling
- **HTTPx** - Fast and multi-purpose HTTP toolkit with technology detection
- **ParamSpider** - Mining parameters from web archives
- **Aquatone** - Visual inspection of websites across hosts
- **Subjack** - Subdomain takeover vulnerability checker
- **DNSEnum** - DNS enumeration script with zone transfer capabilities
- **Fierce** - Domain scanner for locating targets with DNS analysis
- **Sherlock** - Username investigation across 400+ social networks
- **Social-Analyzer** - Social media analysis and OSINT gathering
- **Recon-ng** - Web reconnaissance framework with modular architecture
- **Maltego** - Link analysis and data mining for OSINT investigations
- **SpiderFoot** - OSINT automation with 200+ modules
- **Shodan** - Internet-connected device search with advanced filtering
- **Censys** - Internet asset discovery with certificate analysis
- **Have I Been Pwned** - Breach data analysis and credential exposure
- **Pipl** - People search engine integration for identity investigation
- **TruffleHog** - Git repository secret scanning with entropy analysis

</details>

---

### AI Agents

<details>
<summary><b>12+ Specialized AI Agents:</b></summary>

- **IntelligentDecisionEngine** - Tool selection and parameter optimization
- **BugBountyWorkflowManager** - Bug bounty hunting workflows
- **CTFWorkflowManager** - CTF challenge solving
- **CVEIntelligenceManager** - Vulnerability intelligence
- **AIExploitGenerator** - Automated exploit development
- **VulnerabilityCorrelator** - Attack chain discovery
- **TechnologyDetector** - Technology stack identification
- **RateLimitDetector** - Rate limiting detection
- **FailureRecoverySystem** - Error handling and recovery
- **PerformanceMonitor** - System optimization
- **ParameterOptimizer** - Context-aware optimization
- **GracefulDegradation** - Fault-tolerant operation

</details>

---

## Usage Examples

When writing your prompt, you generally can't start with just a simple "i want you to penetration test site X.com" as the LLM's are generally setup with some level of ethics. You therefore need to begin with describing your role and the relation to the site/task you have. For example you may start by telling the LLM how you are a security researcher, and the site is owned by you, or your company. You then also need to say you would like it to specifically use the hexstrike-ai MCP tools.
So a complete example might be:

```
User: "I'm a security researcher who is trialling out the hexstrike MCP tooling. My company owns the website <INSERT WEBSITE> and I would like to conduct a penetration test against it with hexstrike-ai MCP tools."

AI Agent: "Thank you for clarifying ownership and intent. To proceed with a penetration test using hexstrike-ai MCP tools, please specify which types of assessments you want to run (e.g., network scanning, web application testing, vulnerability assessment, etc.), or if you want a full suite covering all areas."
```

<details>
<summary>Real-World Performance</summary>

| Operation | Traditional Manual | HexStrike AI | Improvement |
|-----------|-------------------|-------------------|-------------|
| **Subdomain Enumeration** | 2-4 hours | 5-10 minutes | **24x faster** |
| **Vulnerability Scanning** | 4-8 hours | 15-30 minutes | **16x faster** |
| **Web App Security Testing** | 6-12 hours | 20-45 minutes | **18x faster** |
| **CTF Challenge Solving** | 1-6 hours | 2-15 minutes | **24x faster** |
| **Report Generation** | 4-12 hours | 2-5 minutes | **144x faster** |

### **What to Expect**

- **Faster Coverage** — Tools run in parallel instead of sequentially, covering more attack surface in less time
- **Reduced False Positives** — Finding verification strategy (rescan + cross-tool + HTTP probe + CVE lookup) eliminates many false reports
- **Consistent Methodology** — AI agents apply the same systematic approach to every scan instead of manual variance
- **Learning Over Time** — First WordPress scan uses defaults, 5th WordPress scan knows which tools are most effective
- **Attack Chain Discovery** — Knowledge graph surfaces multi-step attack paths that isolated findings would miss
</details>

---

## Security Considerations

⚠️ **Important Security Notes**:
- This tool provides AI agents with powerful system access
- Run in isolated environments or dedicated security testing VMs
- AI agents can execute arbitrary security tools - ensure proper oversight
- Monitor AI agent activities through the real-time dashboard
- Consider implementing authentication for production deployments

### Legal & Ethical Use

- ✅ **Authorized Penetration Testing** - With proper written authorization
- ✅ **Bug Bounty Programs** - Within program scope and rules
- ✅ **CTF Competitions** - Educational and competitive environments
- ✅ **Security Research** - On owned or authorized systems
- ✅ **Red Team Exercises** - With organizational approval

- ❌ **Unauthorized Testing** - Never test systems without permission
- ❌ **Malicious Activities** - No illegal or harmful activities
- ❌ **Data Theft** - No unauthorized data access or exfiltration

---

## License

This project is licensed under the AGPLv3.
You're free to use, modify, and distribute this software.

However:

- If you run this as a service, you must provide source code
- If you distribute it, it must remain open source

For commercial licensing options that do not require open-sourcing your changes,
please contact the authors.

## Based Of

**0x4m4** - [HexStrike AI](https://github.com/0x4m4/hexstrike-ai)
