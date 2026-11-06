# List of tools considered always installed (built-in, code-provided or simulated)
BUILT_IN_TOOLS = ["jwt-analyzer", "api-schema-analyzer", "graphql-scanner",
                   "http-framework",
                  "analyze-target", "preview-attack-chain", "create-attack-chain", "smart-scan",
                  "technology-detection", "ai_analyze_session"]

# Tools that require dpkg check (Debian-based systems)
REQUIRE_DPKG_CHECK = ["hashcat-utils", "sleuthkit", "impacket-scripts"]

# Tools that require pip check (Python packages)
REQUIRE_PIP_CHECK = ["pwntools", "one-gadget", "phaseaccess", "stingxss", "breachsql", "vaultrip"]

# Tools that exit with code 1 to signal "findings found" rather than an error.
# The executor treats these like exit code 0 for logging and success determination.
FINDINGS_EXIT_CODE_TOOLS = frozenset(["breachsql", "stingxss", "phaseaccess", "vaultrip"])

# Tools that require gem check (Ruby packages)
REQUIRE_GEM_CHECK = ["zsteg"]

# Tools that require cargo check (Rust packages)
REQUIRE_CARGO_CHECK = ["pwninit", "x8"]

REQUIRE_GO_CHECK = ["httpx"]

# Binary name overrides for tools where the executable name differs from the tool name
BINARY_NAME_OVERRIDES = {
    "scout-suite": "scout",
    "volatility": "vol",
    "hurl": "hURL",
}

# macOS installation policy shared by the installer and availability reporting.
# A GUI application counts only when its CLI wrapper is available to the server.
# Pins favor compatibility with macOS 12, including Intel hosts.
MACOS_TOOL_INSTALLATION = {
    "airbase-ng": {
        "category": "network", "binary": "airbase-ng",
        "method": "brew", "target": "aircrack-ng", "probe": "--help",
        "source_url": "https://www.aircrack-ng.org/doku.php?id=install_aircrack",
    },
    "aircrack-ng": {
        "category": "network", "binary": "aircrack-ng",
        "method": "brew", "target": "aircrack-ng", "probe": "--help",
        "source_url": "https://www.aircrack-ng.org/doku.php?id=install_aircrack",
    },
    "airdecap-ng": {
        "category": "network", "binary": "airdecap-ng",
        "method": "brew", "target": "aircrack-ng", "probe": "--help",
        "source_url": "https://www.aircrack-ng.org/doku.php?id=install_aircrack",
    },
    "aireplay-ng": {
        "category": "network", "binary": "aireplay-ng",
        "method": "brew", "target": "aircrack-ng", "probe": "--help",
        "source_url": "https://www.aircrack-ng.org/doku.php?id=install_aircrack",
    },
    "airmon-ng": {
        "category": "network", "binary": "airmon-ng",
        "method": "unsupported", "target": "", "probe": "--help",
        "source_url": "https://www.aircrack-ng.org/doku.php?id=airmon-ng",
        "reason": "Requires Linux wireless interface and driver management; no native macOS airmon-ng.",
    },
    "airodump-ng": {
        "category": "network", "binary": "airodump-ng",
        "method": "brew", "target": "aircrack-ng", "probe": "--help",
        "source_url": "https://www.aircrack-ng.org/doku.php?id=install_aircrack",
    },
    "anew": {
        "category": "web", "binary": "anew",
        "method": "go", "target": "github.com/tomnomnom/anew@v0.1.1", "probe": "-h",
        "source_url": "https://github.com/tomnomnom/anew",
    },
    "assetfinder": {
        "category": "osint", "binary": "assetfinder",
        "method": "go", "target": "github.com/tomnomnom/assetfinder@v0.1.1", "probe": "-h",
        "source_url": "https://github.com/tomnomnom/assetfinder",
    },
    "autopsy": {
        "category": "ctf", "binary": "autopsy",
        "method": "native", "target": "autopsy", "probe": "@file",
        "source_url": "https://github.com/sleuthkit/autopsy",
    },
    "bettercap": {
        "category": "network", "binary": "bettercap",
        "method": "brew", "target": "bettercap", "probe": "-version",
        "source_url": "https://www.bettercap.org/installation/",
    },
    "breachsql": {
        "category": "web", "binary": "breachsql",
        "method": "server-python", "target": "breachsql>=0.1.0,<1.0.0", "probe": "--help",
        "source_url": "https://pypi.org/project/breachsql/",
    },
    "bulk_extractor": {
        "category": "ctf", "binary": "bulk_extractor",
        "method": "brew", "target": "bulk_extractor", "probe": "-V",
        "source_url": "https://github.com/simsong/bulk_extractor",
    },
    "burpsuite": {
        "category": "web", "binary": "burpsuite",
        "method": "cask", "target": "burp-suite", "probe": "@file",
        "source_url": "https://portswigger.net/burp/documentation/desktop/getting-started/download-and-install",
    },
    "clair": {
        "category": "cloud", "binary": "clair",
        "method": "unsupported", "target": "", "probe": "--help",
        "source_url": "https://quay.github.io/clair/",
        "reason": "Clair is a vulnerability indexing service requiring service configuration and PostgreSQL; deploy its Linux/container service. clairctl alone is not Clair.",
    },
    "cloudmapper": {
        "category": "cloud", "binary": "cloudmapper",
        "method": "python-source", "target": "cloudmapper", "probe": "collect --help",
        "source_url": "https://github.com/duo-labs/cloudmapper",
        "source_revision": "ec8fbf201b8b43e66720cd3ee9079a801e49c61c",
        "interpreter": "3.9",
    },
    "dirb": {
        "category": "web", "binary": "dirb",
        "method": "native", "target": "dirb", "probe": "--help",
        "source_url": "https://dirb.sourceforge.net/",
    },
    "dnsenum": {
        "category": "network", "binary": "dnsenum",
        "method": "native", "target": "dnsenum", "probe": "--help",
        "source_url": "https://github.com/fwaeytens/dnsenum",
    },
    "docker-bench-security": {
        "category": "cloud", "binary": "docker-bench-security",
        "method": "unsupported", "target": "", "probe": "--help",
        "source_url": "https://github.com/docker/docker-bench-security",
        "reason": "Audits the Linux Docker host and its namespaces/filesystem; run inside the Docker Desktop Linux VM or a Linux host, not the macOS host.",
    },
    "dotdotpwn": {
        "category": "web", "binary": "dotdotpwn",
        "method": "native", "target": "dotdotpwn", "probe": "-h",
        "source_url": "https://github.com/wireghoul/dotdotpwn",
    },
    "eaphammer": {
        "category": "network", "binary": "eaphammer",
        "method": "unsupported", "target": "", "probe": "--help",
        "source_url": "https://github.com/s0lst1c3/eaphammer",
        "reason": "Requires Linux hostapd and wireless drivers; use a Linux host with a supported wireless adapter.",
    },
    "enum4linux-ng": {
        "category": "network", "binary": "enum4linux-ng",
        "method": "existing", "target": "enum4linux-ng", "probe": "--help",
        "source_url": "https://github.com/cddmp/enum4linux-ng",
    },
    "evil-winrm": {
        "category": "auth", "binary": "evil-winrm",
        "method": "gem", "target": "evil-winrm", "probe": "--help",
        "source_url": "https://github.com/Hackplayers/evil-winrm",
    },
    "falco": {
        "category": "cloud", "binary": "falco",
        "method": "unsupported", "target": "", "probe": "--version",
        "source_url": "https://falco.org/docs/getting-started/",
        "reason": "Runtime event collection requires a supported Linux kernel driver or eBPF; run Falco on the Linux host or VM.",
    },
    "gdb": {
        "category": "binary", "binary": "gdb",
        "method": "native", "target": "gdb", "probe": "--version",
        "source_url": "https://sourceware.org/gdb/wiki/PermissionsDarwin",
    },
    "ghidra": {
        "category": "binary", "binary": "analyzeHeadless",
        "method": "brew", "target": "ghidra", "probe": "@file",
        "source_url": "https://github.com/NationalSecurityAgency/ghidra",
    },
    "gospider": {
        "category": "web", "binary": "gospider",
        "method": "go", "target": "github.com/jaeles-project/gospider@v1.1.6", "probe": "--help",
        "source_url": "https://github.com/jaeles-project/gospider",
    },
    "hashcat-utils": {
        "category": "auth", "binary": "cap2hccapx.bin",
        "method": "native", "target": "hashcat-utils", "probe": "--help",
        "source_url": "https://github.com/hashcat/hashcat-utils",
    },
    "hashpump": {
        "category": "ctf", "binary": "hashpump",
        "method": "native", "target": "hashpump", "probe": "-h",
        "source_url": "https://pypi.org/project/hashpumpy/",
    },
    "hcxdumptool": {
        "category": "network", "binary": "hcxdumptool",
        "method": "unsupported", "target": "", "probe": "--help",
        "source_url": "https://github.com/ZerBea/hcxdumptool",
        "reason": "Requires Linux kernel wireless interfaces and a supported adapter; no native macOS capture backend.",
    },
    "hcxpcapngtool": {
        "category": "network", "binary": "hcxpcapngtool",
        "method": "brew", "target": "hcxtools", "probe": "--version",
        "source_url": "https://github.com/ZerBea/hcxtools",
    },
    "httpx": {
        "category": "web", "binary": "httpx",
        "method": "go", "target": "github.com/projectdiscovery/httpx/cmd/httpx@v1.8.1", "probe": "-version",
        "source_url": "https://github.com/projectdiscovery/httpx",
    },
    "hurl": {
        "category": "web", "binary": "hURL",
        "method": "native", "target": "hurl", "probe": "--help",
        "source_url": "https://github.com/fnord0/hURL",
    },
    "impacket-scripts": {
        "category": "network", "binary": "smbclient.py",
        "method": "python", "target": "impacket==0.13.1", "probe": "-h",
        "source_url": "https://github.com/fortra/impacket",
    },
    "jaeles": {
        "category": "web", "binary": "jaeles",
        "method": "go", "target": "github.com/jaeles-project/jaeles@beta-v0.17.1", "probe": "--help",
        "source_url": "https://github.com/jaeles-project/jaeles",
    },
    "joomscan": {
        "category": "web", "binary": "joomscan",
        "method": "native", "target": "joomscan", "probe": "--help",
        "source_url": "https://github.com/OWASP/joomscan",
    },
    "kismet": {
        "category": "network", "binary": "kismet",
        "method": "brew", "target": "kismetwireless/kismet/kismet", "probe": "--version",
        "source_url": "https://www.kismetwireless.net/docs/readme/installing/osx/",
    },
    "kube-bench": {
        "category": "cloud", "binary": "kube-bench",
        "method": "brew", "target": "kube-bench", "probe": "version",
        "source_url": "https://github.com/aquasecurity/kube-bench",
    },
    "kube-hunter": {
        "category": "cloud", "binary": "kube-hunter",
        "method": "python", "target": "kube-hunter==0.6.8", "probe": "--help",
        "source_url": "https://github.com/aquasecurity/kube-hunter",
    },
    "libc-database": {
        "category": "binary", "binary": "libc-database",
        "method": "native", "target": "libc-database", "probe": "--help",
        "source_url": "https://github.com/niklasb/libc-database",
    },
    "maltego": {
        "category": "osint", "binary": "maltego",
        "method": "cask", "target": "maltego", "probe": "@file",
        "source_url": "https://www.maltego.com/downloads/",
    },
    "massdns": {
        "category": "osint", "binary": "massdns",
        "method": "brew", "target": "massdns", "probe": "--help",
        "source_url": "https://github.com/blechschmidt/massdns",
    },
    "mdk4": {
        "category": "network", "binary": "mdk4",
        "method": "unsupported", "target": "", "probe": "--help",
        "source_url": "https://github.com/aircrack-ng/mdk4",
        "reason": "Requires Linux wireless injection interfaces and drivers; no native macOS backend.",
    },
    "msfconsole": {
        "category": "auth", "binary": "msfconsole",
        "method": "native", "target": "msfconsole", "probe": "--version",
        "source_url": "https://docs.metasploit.com/docs/using-metasploit/getting-started/nightly-installers.html",
    },
    "msfvenom": {
        "category": "auth", "binary": "msfvenom",
        "method": "native", "target": "msfvenom", "probe": "--help",
        "source_url": "https://docs.metasploit.com/docs/using-metasploit/getting-started/nightly-installers.html",
    },
    "nbtscan": {
        "category": "network", "binary": "nbtscan",
        "method": "native", "target": "nbtscan", "probe": "-h",
        "source_url": "https://github.com/resurrecting-open-source-projects/nbtscan",
    },
    "nxc": {
        "category": "network", "binary": "nxc",
        "method": "existing", "target": "nxc", "probe": "--help",
        "source_url": "https://github.com/Pennyw0rth/NetExec",
    },
    "one-gadget": {
        "category": "binary", "binary": "one_gadget",
        "method": "gem", "target": "one_gadget", "probe": "--version",
        "source_url": "https://github.com/david942j/one_gadget",
    },
    "ophcrack": {
        "category": "auth", "binary": "ophcrack",
        "method": "brew", "target": "ophcrack", "probe": "--help",
        "source_url": "https://ophcrack.sourceforge.io/",
    },
    "outguess": {
        "category": "ctf", "binary": "outguess",
        "method": "native", "target": "outguess", "probe": "-h",
        "source_url": "https://github.com/resurrecting-open-source-projects/outguess",
    },
    "pacu": {
        "category": "cloud", "binary": "pacu",
        "method": "python", "target": "pacu==1.7.0", "probe": "--help",
        "source_url": "https://github.com/RhinoSecurityLabs/pacu",
    },
    "parsero": {
        "category": "osint", "binary": "parsero",
        "method": "python", "target": "parsero==0.81", "probe": "-h",
        "source_url": "https://github.com/behindthefirewalls/Parsero",
    },
    "patator": {
        "category": "auth", "binary": "patator",
        "method": "python",
        "target": "git+https://github.com/lanjelot/patator.git@964e87c4932fc20f3d0c3226a8e409eae527e831",
        "probe": "http_fuzz --help",
        "source_url": "https://github.com/lanjelot/patator",
        "interpreter": "3.13",
    },
    "phaseaccess": {
        "category": "web", "binary": "phaseaccess",
        "method": "server-python", "target": "phaseaccess>=0.1.0,<1.0.0", "probe": "--help",
        "source_url": "https://pypi.org/project/phaseaccess/",
    },
    "prowler": {
        "category": "cloud", "binary": "prowler",
        "method": "python", "target": "prowler==5.42.0", "probe": "--version",
        "source_url": "https://docs.prowler.com/projects/prowler-open-source/en/latest/",
    },
    "pwninit": {
        "category": "binary", "binary": "pwninit",
        "method": "cargo", "target": "pwninit@3.3.3", "probe": "--help",
        "source_url": "https://github.com/io12/pwninit",
    },
    "pwntools": {
        "category": "binary", "binary": "pwn",
        "method": "server-python", "target": "pwntools==4.15.0", "probe": "--help",
        "source_url": "https://docs.pwntools.com/en/stable/install.html",
    },
    "qsreplace": {
        "category": "web", "binary": "qsreplace",
        "method": "go", "target": "github.com/tomnomnom/qsreplace@v0.0.3", "probe": "-h",
        "source_url": "https://github.com/tomnomnom/qsreplace",
    },
    "rpcclient": {
        "category": "network", "binary": "rpcclient",
        "method": "brew", "target": "samba", "probe": "--help",
        "source_url": "https://www.samba.org/samba/docs/current/man-html/rpcclient.1.html",
    },
    "scalpel": {
        "category": "ctf", "binary": "scalpel",
        "method": "native", "target": "scalpel", "probe": "-h",
        "source_url": "https://github.com/sleuthkit/scalpel",
    },
    "scout-suite": {
        "category": "cloud", "binary": "scout",
        "method": "python", "target": "ScoutSuite==5.14.0", "probe": "--help",
        "source_url": "https://github.com/nccgroup/ScoutSuite",
    },
    "shuffledns": {
        "category": "osint", "binary": "shuffledns",
        "method": "go", "target": "github.com/projectdiscovery/shuffledns/cmd/shuffledns@v1.2.1", "probe": "-version",
        "source_url": "https://github.com/projectdiscovery/shuffledns",
    },
    "sleuthkit": {
        "category": "ctf", "binary": "fls",
        "method": "brew", "target": "sleuthkit", "probe": "-V",
        "source_url": "https://www.sleuthkit.org/sleuthkit/",
    },
    "sslscan": {
        "category": "web", "binary": "sslscan",
        "method": "native", "target": "sslscan", "probe": "--version",
        "source_url": "https://github.com/rbsec/sslscan",
        "source_revision": "9c3fefa0a4b6b743c820e4f813ae2f8b695ab67e",
    },
    "spiderfoot": {
        "category": "osint", "binary": "spiderfoot",
        "method": "python-source", "target": "spiderfoot", "probe": "--help",
        "source_url": "https://github.com/smicallef/spiderfoot",
        "source_revision": "b9c345de5b085debc7444fc10e0e26e7745df5f2",
    },
    "steghide": {
        "category": "ctf", "binary": "steghide",
        "method": "native", "target": "steghide", "probe": "--version",
        "source_url": "https://steghide.sourceforge.net/",
    },
    "stingxss": {
        "category": "web", "binary": "stingxss",
        "method": "server-python", "target": "stingxss>=0.1.0,<1.0.0", "probe": "--help",
        "source_url": "https://pypi.org/project/stingxss/",
    },
    "sublist3r": {
        "category": "network", "binary": "sublist3r",
        "method": "existing", "target": "sublist3r", "probe": "--help",
        "source_url": "https://github.com/aboul3la/Sublist3r",
    },
    "terrascan": {
        "category": "cloud", "binary": "terrascan",
        "method": "brew", "target": "terrascan", "probe": "version",
        "source_url": "https://github.com/tenable/terrascan",
    },
    "testssl": {
        "category": "web", "binary": "testssl.sh",
        "method": "native", "target": "testssl", "probe": "--version",
        "source_url": "https://github.com/testssl/testssl.sh",
    },
    "tshark": {
        "category": "network", "binary": "tshark",
        "method": "native", "target": "tshark", "probe": "--version",
        "source_url": "https://www.wireshark.org/docs/man-pages/tshark.html",
    },
    "vaultrip": {
        "category": "auth", "binary": "vaultrip",
        "method": "server-python", "target": "vaultrip>=0.1.0,<1.0.0", "probe": "--help",
        "source_url": "https://pypi.org/project/vaultrip/",
    },
    "vulnx": {
        "category": "web", "binary": "vulnx",
        "method": "go", "target": "github.com/projectdiscovery/vulnx/v2/cmd/vulnx@v2.0.2", "probe": "version --disable-update-check",
        "source_url": "https://github.com/projectdiscovery/vulnx",
    },
    "wafw00f": {
        "category": "web", "binary": "wafw00f",
        "method": "existing", "target": "wafw00f", "probe": "--version",
        "source_url": "https://github.com/EnableSecurity/wafw00f",
    },
    "wfuzz": {
        "category": "web", "binary": "wfuzz",
        "method": "existing", "target": "wfuzz", "probe": "--version",
        "source_url": "https://github.com/xmendez/wfuzz",
    },
    "whatweb": {
        "category": "web", "binary": "whatweb",
        "method": "existing", "target": "whatweb", "probe": "--version",
        "source_url": "https://github.com/urbanadventurer/WhatWeb",
    },
    "wifite": {
        "category": "network", "binary": "wifite",
        "method": "unsupported", "target": "", "probe": "--help",
        "source_url": "https://github.com/derv82/wifite2",
        "reason": "Requires Linux wireless tooling, airmon-ng and compatible injection drivers; use a Linux host.",
    },
    "wpscan": {
        "category": "web", "binary": "wpscan",
        "method": "existing", "target": "wpscan", "probe": "--version",
        "source_url": "https://github.com/wpscanteam/wpscan",
    },
    "x8": {
        "category": "web", "binary": "x8",
        "method": "cargo", "target": "x8", "probe": "--help",
        "source_url": "https://github.com/Sh1Yo/x8",
    },
    "xsser": {
        "category": "web", "binary": "xsser",
        "method": "python-source", "target": "xsser", "probe": "--help",
        "source_url": "https://github.com/epsylon/xsser",
        "source_revision": "dc72706d2c0dcfe52e355194d1be3b1aed4afca2",
    },
    "zaproxy": {
        "category": "web", "binary": "zaproxy",
        "method": "native", "target": "zaproxy", "probe": "-version",
        "source_url": "https://www.zaproxy.org/download/",
    },
}

MACOS_UNSUPPORTED_TOOLS = {
    name: spec["reason"] for name, spec in MACOS_TOOL_INSTALLATION.items()
    if spec["method"] == "unsupported"
}

# Comprehensive list of tools categorized by functionality for health monitoring and availability checks
HEALTH_TOOL_CATEGORIES = {
    "By_NyxStrike": ["phaseaccess", "stingxss", "breachsql", "vaultrip"],
    "essential": ["nmap", "gobuster", "dirb", "nikto", "sqlmap", "hydra", "john", "hashcat"],
    "network_recon": ["rustscan", "masscan", "autorecon", "nbtscan", "arp-scan", "responder",
                "nxc", "enum4linux-ng", "rpcclient", "enum4linux", "smbmap", "evil-winrm"],
    "web_recon": ["ffuf", "feroxbuster", "dirsearch", "dotdotpwn", "xsser", "wfuzz",
                      "arjun", "paramspider", "x8", "jaeles", "dalfox",
                     "httpx", "wafw00f", "burpsuite", "katana", "hakrawler", "gospider", "wpscan", "joomscan", "testssl"],
    "web_vuln": ["nuclei", "graphql-scanner", "jwt-analyzer", "zaproxy"],
    "brute_force": ["medusa", "patator", "hashid", "ophcrack", "hashcat-utils"],
    "binary": ["gdb", "radare2", "binwalk", "ROPgadget", "checksec", "objdump",
               "ghidra", "pwntools", "one-gadget", "ropper", "angr", "libc-database", "pwninit"],
    "forensics": ["vol", "steghide", "hashpump", "foremost", "exiftool",
                  "strings", "xxd", "file", "photorec", "testdisk", "scalpel",
                  "bulk_extractor", "stegsolve", "zsteg", "outguess", "volatility", "sleuthkit", "autopsy"],
    "cloud": ["prowler", "scout-suite", "trivy", "kube-hunter", "kube-bench",
              "docker-bench-security", "checkov", "terrascan", "falco", "clair",
              "cloudmapper", "pacu"],
    "osint": ["amass", "subfinder", "fierce", "dnsenum", "theHarvester", "sherlock",
               "social-analyzer", "recon-ng", "maltego", "spiderfoot",
              "whois", "bbot", "gau", "waybackurls", "waymore", "sublist3r", "assetfinder", "shuffledns", "massdns", "parsero", "dig"],
    "exploitation": ["msfconsole", "msfvenom", "searchsploit", "commix"],
    "api": ["api-schema-analyzer", "curl", "http-framework", "qsreplace", "uro"],
    "wifi_pentest": ["kismet", "wireshark", "tshark", "tcpdump",
                 "airbase-ng", "airdecap-ng", "hcxdumptool", "hcxpcapngtool",
                 "mdk4", "eaphammer", "wifite", "bettercap", "airmon-ng", 
                 "airodump-ng", "aireplay-ng", "aircrack-ng"],
    "database": ["mysql", "sqlite3"],
    "active_directory": [
        "impacket-scripts", "ldapdomaindump"
    ],
    "vulnerability_intelligence": ["vulnx"],
    "fingerprint": ["whatweb"],

    "intelligence": ["analyze-target", "preview-attack-chain", "create-attack-chain", "smart-scan", "technology-detection"],
    "ai_assist": ["ai_analyze_session"],

    "data_processing": ["hurl", "anew"],

    #Not in use: httpie, postman, insomnia, "shodan-cli", "censys-cli", "have-i-been-pwned"
}
