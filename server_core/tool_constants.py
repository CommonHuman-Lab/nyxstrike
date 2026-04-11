# List of tools considered always installed (built-in, code-provided or simulated)
BUILT_IN_TOOLS = ["jwt-analyzer", "api-schema-analyzer", "graphql-scanner",
                   "http-framework", "auto_install_missing_apt_tools", 
                  "analyze-target", "preview-attack-chain", "create-attack-chain", "smart-scan",
                  "technology-detection", "ai_analyze_session"]

# Tools that require dpkg check (Debian-based systems)
REQUIRE_DPKG_CHECK = ["hashcat-utils", "sleuthkit", "impacket-scripts"]

# Tools that require pip check (Python packages)
REQUIRE_PIP_CHECK = ["pwntools", "one-gadget"]

# Tools that require gem check (Ruby packages)
REQUIRE_GEM_CHECK = ["zsteg"]

# Tools that require cargo check (Rust packages)
REQUIRE_CARGO_CHECK = ["pwninit", "x8"]

# Binary name overrides for tools where the executable name differs from the tool name
BINARY_NAME_OVERRIDES = {
    "scout-suite": "scout",
    "volatility": "vol",
    "hurl": "hURL",
}

# Comprehensive list of tools categorized by functionality for health monitoring and availability checks
HEALTH_TOOL_CATEGORIES = {
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

    "ops": ["auto_install_missing_apt_tools"],

    "intelligence": ["analyze-target", "preview-attack-chain", "create-attack-chain", "smart-scan", "technology-detection"],
    "ai_assist": ["ai_analyze_session"],

    "data_processing": ["hurl", "anew"],

    #Not in use: httpie, postman, insomnia, "shodan-cli", "censys-cli", "have-i-been-pwned"
    #"active_directory": [
    #    "bloodhound-ce-python"
    #    "certipy-ad", "mitm6", "adidnsdump", "pywerview"
    #]
}
