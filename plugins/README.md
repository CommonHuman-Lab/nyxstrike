NyxStrike Plugin System
=======================

Plugins extend NyxStrike without touching the core codebase.
Drop a folder into the right type directory, add an entry to
plugins.yaml, and restart the server.

Directory layout
----------------

  plugins/
  ├── plugins.yaml          ← root manifest (edit this)
  ├── tools/                ← tool plugins (API endpoint + MCP tool)
  │   └── example_net_ping/ ← copy this as a starting point
  │       ├── plugin.yaml
  │       ├── server_api.py
  │       └── mcp_tool.py
  └── README                ← this file

Plugin types
------------

tools
  Adds a Flask API endpoint AND a FastMCP tool that AI agents can call.
  Files required:
    plugin.yaml    — metadata (see example_net_ping/plugin.yaml)
    server_api.py  — Flask Blueprint; must expose a module-level `blueprint`
    mcp_tool.py    — FastMCP registration; must expose `register(mcp, api_client, logger)`

(Future types: workflows, agents, reports — each will have its own subdirectory
 and its own section in plugins.yaml.)

plugin.yaml fields
------------------

  name            display / registry key
  version         semver string
  description     one-line description shown in the dashboard
  author          author name or handle
  category        tool category used for the dashboard availability row.
                  Reuse an existing key to slot into that row, or introduce
                  a new one to create a dedicated row.
                  Existing keys: essential, network_recon, web_recon, web_vuln,
                  brute_force, binary, forensics, cloud, osint, exploitation,
                  api, wifi_pentest, database, active_directory, fingerprint,
                  intelligence, ai_assist, data_processing, ops.
  tags            list of freeform tags
  endpoint        Flask route, e.g. /api/plugins/my_tool
  mcp_tool_name   Python identifier exposed to AI agents, e.g. nyxstrike_my_tool
  effectiveness   float 0.0–1.0  (used by the Intelligent Decision Engine)
  check           required — how to verify the underlying tool is installed.
                  See "check block" section below.
  params          required parameters (name: {required: true, description: …})
  optional        optional parameters (name: {default: …, description: …})

check block (required)
----------------------

  Declares how NyxStrike should verify that the underlying binary or package
  is installed.  Omitting this block will cause the plugin to be rejected at
  load time.

  check:
    type     (required) how to probe — one of:
               builtin  always available, no probe — use for pure-Python plugins
                        that need no external binary
               which    `which <binary>` — for tools on $PATH
               dpkg     `dpkg -s <package>` — Debian/Ubuntu apt packages
               pip      `pip list` contains <package> — Python packages
               gem      `gem list` contains <package> — Ruby gems
               cargo    `cargo install --list` contains <package> — Rust crates
    binary   (optional) executable or package name to probe.
             Omit when it matches mcp_tool_name.
             Use this when the binary name differs, e.g.:
               mcp_tool_name: nyxstrike_net_ping
               binary: ping
    install  (optional) human-readable hint shown in the dashboard when the
             tool is reported as missing, e.g.:
               install: "apt install iputils-ping"

  Examples:

    # Pure-Python plugin — always available, no check needed
    # (omit the check block entirely, or use type: builtin)

    # Binary on $PATH
    check:
      type: which
      binary: nmap
      install: "apt install nmap"

    # Debian package
    check:
      type: dpkg
      binary: hashcat-utils
      install: "apt install hashcat-utils"

    # Python package
    check:
      type: pip
      binary: pwntools
      install: "pip install pwntools"

    # Ruby gem
    check:
      type: gem
      binary: zsteg
      install: "gem install zsteg"

    # Rust crate
    check:
      type: cargo
      binary: x8
      install: "cargo install x8"

Error handling
--------------

Any plugin that fails to load (bad yaml, import error, duplicate endpoint, …)
is skipped with a warning logged to the server console.  The server always
starts cleanly regardless of plugin errors.