<div align="center">
<img src="assets/nyxstrike-logo.png" alt="NyxStrike" width="220"/>

# NyxStrike

### AI-powered offensive security orchestration engine

</div>

## What is NyxStrike?

NyxStrike connects LLM agents to real offensive security tools and executes full attack chains — from recon to exploitation.

**200+ tools · 50+ categories · AI decision engine · Tamper-evident evidence chain**

---

## 🚀 Quick Start (Installation)

> Get a full offensive security environment running in minutes.

```bash
git clone https://github.com/CommonHuman-Lab/nyxstrike.git
cd nyxstrike

./nyxstrike.sh -a               # Setup + start server
./nyxstrike.sh -a -t            # + install external tools

```

> Full flag reference: [Wiki — Installation & Flags](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Installation-and-Flags)

### macOS: Apple Silicon and Intel

The launcher and Python lockfile include support for `arm64` and `x86_64` macOS.
The shell scripts work with macOS's bundled Bash 3.2. A complete tool installation
on Intel/macOS 12 still needs verification; individual tools may require newer
macOS releases or features available only on Linux.

Install Xcode Command Line Tools (`xcode-select --install`, if missing) and
[Homebrew](https://docs.brew.sh/Installation) before setup. Homebrew's
[support tiers](https://docs.brew.sh/Support-Tiers) affect which packages have
prebuilt binaries and which need a source build.

| Mac architecture | Homebrew prefix | Terminal / Python architecture |
| --- | --- | --- |
| Apple Silicon | `/opt/homebrew` | `arm64` (native terminal) |
| Intel | `/usr/local` | `x86_64` |

Keep Homebrew and Python on the same architecture. Create `nyxstrike-env` on each
Mac rather than copying it between machines. Setup uses the same command on both:

```bash
./nyxstrike.sh -a -t
```

To select Python explicitly, append `-p 3.12` or pass a Python executable to `-p`.
Without it, the launcher uses `python3`.

The macOS installer uses a shared tool catalog and checks existing installations
before deciding whether to repair them. Managed commands take precedence in the
launcher's PATH, and tools with conflicting dependencies use separate runtimes
where needed. Re-running the setup command retries failed installations. Details
are written to `install_log.txt`.

A few platform differences matter:

- On Intel, the launcher prepares Rust 1.91 or newer and OpenSSL for the locked
  cryptography and angr source builds. An explicit `OPENSSL_DIR` is respected.
  The angr build also gets the C++ header it needs with Apple's compiler.
- BBOT uses Homebrew on macOS. Wfuzz, WhatWeb, WAFW00F, Sublist3r and several other
  tools use managed runtimes under `~/.local/share/nyxstrike-tools`. Additional
  Python tools cannot replace packages already installed in the server environment;
  unresolved dependency conflicts are reported as failures.
- The catalog installs `kube-bench` through Homebrew, but installing its CLI does
  not provide a Linux Kubernetes host to audit. `docker-bench-security` and other
  tools without a suitable macOS backend are reported as unsupported.
- GDB is built from source; on Apple Silicon, it targets x86_64 Darwin. Attaching
  to macOS processes still requires appropriate code signing. LLDB remains an
  option for native Apple Silicon debugging.

See [macOS installation notes](MACOS_INSTALLATION_CHANGES.md) for the tool-specific
recipes and verification limits. The offline installer tests simulate package
managers and failure cases; they do not establish that every external tool builds
or runs on either architecture.

### Verify Setup

Open [http://localhost:8888](http://localhost:8888) to access the dashboard.

> Some tools (e.g. `nmap`, `masscan`) require elevated privileges for specific scan modes. Use a dedicated test VM and least-privilege setup where possible.

---

## 🔌 AI Agent Integrations (MCP)

Connect NyxStrike to any MCP-compatible AI client — OpenCode, Cursor, Claude Desktop, VS Code Copilot, Roo Code, and more.

> Open [http://localhost:8888/#/help](http://localhost:8888/#/help) for help with configurations.

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

## 🔧 Features

NyxStrike does not just run tools — it orchestrates full attack chains using AI decision-making.

- AI agents that chain tools automatically, guided by a decision engine that ranks and re-scores tools mid-scan
- 200+ offensive security tools, all agent-controllable
- Full attack workflow: recon → enumeration → exploitation → reporting
- Local payload & data workbench — 40+ crypto, encoding, and analysis operations, no target required
- Every tool run hash-chained for tamper-evident, verifiable evidence
- Real-time dashboard — live output, network topology maps
- MCP-compatible — plug into any AI client you already use

> [Full feature breakdown](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Features) · [Session & workbench docs](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Dashboard-and-Sessions)

---

## 🧰 Tool Arsenal

200+ offensive security tools across 50+ categories — all dynamically orchestrated by AI agents in real time.

- Network & wireless reconnaissance
- Web & API exploitation
- OSINT & intelligence gathering
- Password & credential attacks
- Binary exploitation & reverse engineering
- Cloud, container & IaC security
- Digital forensics & incident response

> [Full tool list by category](https://github.com/CommonHuman-Lab/nyxstrike/wiki/Tool-Arsenal)

---

## ⚠️ Security Considerations

> NyxStrike gives AI agents direct access to offensive security tooling.

- Run only in isolated environments or dedicated security testing VMs  
- AI agents may execute real commands — maintain operator oversight  
- Monitor activity via dashboard and logs in real time  
- Use `NYXSTRIKE_API_TOKEN` for any non-local deployment

### Legal & Ethical Use

| Allowed | Not Allowed |
|---|---|
| Authorized penetration testing (with written authorization) | Unauthorized testing of any system |
| Bug bounty programs (within program scope and rules) | Malicious, illegal, or harmful activities |
| CTF competitions and educational environments | Unauthorized data access or exfiltration |
| Security research on owned or authorized systems | |
| Red team exercises (with organizational approval) | |

---

## 📜 License

Licensed under the [AGPLv3](LICENSE).
You are free to use, modify, and distribute this software. If you run it as a service or distribute it, the source must remain open.

For commercial licensing, contact the author.

---

## ⭐ Support the project

If NyxStrike is useful to your workflow:

- Star the repository
- Share it with others
- Contribute improvements

It makes a real difference.

---

## Credits

Originally inspired by [hexstrike-ai](https://github.com/0x4m4/hexstrike-ai).
