"""
Tool Registry with compact schemas for the AI agent.

Categorized tool definitions with minimal schemas.
Only 5-8 tools are loaded per task category to fit small model context windows.
Can be increased or decreased as needed, but focus on the most effective tools for each category.
"""

from typing import Dict, List, Optional
import logging
from typing import TypedDict, Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schema definition for tool registry entries.
# Every entry in TOOLS must conform to this shape.
# ---------------------------------------------------------------------------

class ToolDefinition(TypedDict, total=False):
    desc: str          # required
    endpoint: str      # required — must start with "/"
    method: str        # required — e.g. "POST"
    category: str      # required
    params: dict       # required — required parameters
    optional: dict     # required — optional parameters with defaults
    effectiveness: float  # required — 0.0–1.0


_REQUIRED_TOOL_KEYS: tuple = ("desc", "endpoint", "method", "category", "params", "optional", "effectiveness")


def _validate_registry(tools: Dict[str, dict]) -> None:
    """Validate all entries in the TOOLS registry at import time.

    Raises ValueError listing all malformed entries so the server fails fast
    rather than silently serving broken tool definitions at runtime.
    """
    errors: List[str] = []
    for name, defn in tools.items():
        missing = [k for k in _REQUIRED_TOOL_KEYS if k not in defn]
        if missing:
            errors.append(f"  '{name}': missing keys {missing}")
        endpoint = defn.get("endpoint", "")
        if endpoint and not endpoint.startswith("/"):
            errors.append(f"  '{name}': endpoint {endpoint!r} must start with '/'")
        eff = defn.get("effectiveness")
        if eff is not None and not (0.0 <= eff <= 1.0):
            errors.append(f"  '{name}': effectiveness {eff!r} must be between 0.0 and 1.0")
    if errors:
        raise ValueError(
            "tool_registry: the following TOOLS entries are malformed:\n" + "\n".join(errors)
        )

# ---------------------------------------------------------------------------
# Tool definitions - each entry is intentionally compact so the full category
# fits well under the context window of smaller models when serialized.
# ---------------------------------------------------------------------------

TOOLS: Dict[str, dict] = {
    # ---- AI ----
    "ai_analyze_session": {
        "desc": "Analyse an existing workflow session with the LLM.",
        "endpoint": "/api/intelligence/analyze-session",
        "method": "POST",
        "category": "ai_assist",
        "params": {"session_id": {"required": True}},
        "optional": {},
        "effectiveness": 0.90,
    },
    
    # ---- Vulnerability Intelligence ----
    "vulnx": {
        "desc": "CVE vulnerability intelligence and analysis",
        "endpoint": "/api/vuln-intel/vulnx",
        "method": "POST",
        "category": "vulnerability_intelligence",
        "params": {},
        "optional": {"cve_id": "", "search": "", "auth_key": ""},
        "effectiveness": 0.90,
    },

    # ---- URL Recon ----
    "waymore": {
        "desc": "Find URLs and responses from various archives using waymore.",
        "endpoint": "/api/tools/waymore",
        "method": "POST",
        "category": "osint",
        "params": {"input": {"required": True}},
        "optional": {"mode": "U", "output_urls": "", "output_responses": ""},
        "effectiveness": 0.85,
    },

  # ---- Intelligence ----
    "analyze-target": {
        "desc": "Analyze target and create comprehensive profile using Intelligent Decision Engine",
        "endpoint": "/api/intelligence/analyze-target",
        "method": "POST",
        "category": "intelligence",
        "params": {"target": {"required": True}},
        "optional": {},
        "effectiveness": 0.92,
    },

    "create-attack-chain": {
        "desc": "Create an intelligent attack chain based on target profile",
        "endpoint": "/api/intelligence/create-attack-chain",
        "method": "POST",
        "category": "intelligence",
        "params": {"target": {"required": True}},
        "optional": {"objective": "comprehensive"},
        "effectiveness": 0.90,
    },

    "preview-attack-chain": {
        "desc": "Preview an intelligent attack chain without persisting a session",
        "endpoint": "/api/intelligence/preview-attack-chain",
        "method": "POST",
        "category": "intelligence",
        "params": {"target": {"required": True}},
        "optional": {"objective": "comprehensive"},
        "effectiveness": 0.89,
    },

    "smart-scan": {
        "desc": "Execute an intelligent scan using AI-driven tool selection and parameter optimization with parallel execution",
        "endpoint": "/api/intelligence/smart-scan",
        "method": "POST",
        "category": "intelligence",
        "params": {"target": {"required": True}},
        "optional": {"objective": "comprehensive", "max_tools": 5},
        "effectiveness": 0.93,
    },

    "technology-detection": {
        "desc": "Detect technologies and create technology-specific testing recommendations",
        "endpoint": "/api/intelligence/technology-detection",
        "method": "POST",
        "category": "intelligence",
        "params": {"target": {"required": True}},
        "optional": {},
        "effectiveness": 0.90,
    },

    # "cve-monitor": {
    #     "desc": "Monitor CVE databases for new vulnerabilities with AI analysis.",
    #     "endpoint": "/api/vuln-intel/cve-monitor",
    #     "method": "POST",
    #     "category": "vulnerability_intelligence",
    #     "params": {},
    #     "optional": {
    #         "keywords": ""
    #     },
    #     "effectiveness": 0.90,
    # },
    
    # ---- Network Recon ----
    "nmap": {
        "desc": "Port scan and service detection",
        "endpoint": "/api/tools/nmap",
        "method": "POST",
        "category": "essential",
        "params": {"target": {"required": True}},
        "optional": {"scan_type": "-sCV", "ports": "", "additional_args": "-T4 -Pn"},
        "effectiveness": 0.95,
    },

    "nmap_advanced": {
        "desc": "Advanced Nmap scans with custom NSE scripts and optimized timing",
        "endpoint": "/api/tools/nmap-advanced",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"scan_type": "-sS", "ports": "", "timing": "T4", "nse_scripts": "", "os_detection": False, "version_detection": False, "aggressive": False, "stealth": False, "additional_args": ""},
        "effectiveness": 0.97,
        "parent_tool": "nmap"
    },

    "masscan": {
        "desc": "Fast mass port scanner",
        "endpoint": "/api/tools/masscan",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"ports": "1-65535", "rate": "1000", "additional_args": ""},
        "effectiveness": 0.92,
    },
    "rustscan": {
        "desc": "Ultra-fast port scanner",
        "endpoint": "/api/tools/rustscan",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.90,
    },
    "enum4linux": {
        "desc": "SMB/RPC enumeration on Windows/Samba",
        "endpoint": "/api/tools/enum4linux",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": "-a"},
        "effectiveness": 0.80,
    },
    "smbmap": {
        "desc": "SMB share enumeration",
        "endpoint": "/api/tools/smbmap",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.85,
    },
    "arp-scan": {
        "desc": "ARP-based host discovery on local network",
        "endpoint": "/api/tools/arp-scan",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.85,
    },

    # ---- Web Recon ----
    "gobuster": {
        "desc": "Directory and file brute-forcer",
        "endpoint": "/api/tools/gobuster",
        "method": "POST",
        "category": "essential",
        "params": {"url": {"required": True}},
        "optional": {"mode": "dir", "wordlist": "/usr/share/wordlists/dirb/common.txt", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "ffuf": {
        "desc": "Fast web fuzzer for dirs, vhosts, params",
        "endpoint": "/api/tools/ffuf",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"wordlist": "/usr/share/wordlists/dirb/common.txt", "mode": "directory", "match_codes": "200,204,301,302,307,401,403", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "feroxbuster": {
        "desc": "Recursive content discovery",
        "endpoint": "/api/tools/feroxbuster",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"wordlist": "/usr/share/wordlists/dirb/common.txt", "threads": 10, "additional_args": ""},
        "effectiveness": 0.85,
    },
    "katana": {
        "desc": "Web crawler for endpoint discovery",
        "endpoint": "/api/tools/katana",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.88,
    },
    "gospider": {
        "desc": "Web spider for crawling URLs, sitemap, robots, and third-party sources",
        "endpoint": "/api/tools/gospider",
        "method": "POST",
        "category": "web_recon",
        "params": {},
        "optional": {
            "site": "",
            "sites": "",
            "proxy": "",
            "output": "",
            "user_agent": "web",
            "cookie": "",
            "headers": [],
            "burp": "",
            "blacklist": "",
            "threads": 1,
            "concurrent": 5,
            "depth": 1,
            "delay": 0,
            "random_delay": 0,
            "timeout": 10,
            "sitemap": False,
            "robots": True,
            "other_source": False,
            "include_subs": False,
            "include_other_source": False,
            "debug": False,
            "verbose": False,
            "no_redirect": False,
            "version": False,
            "additional_args": ""
        },
        "effectiveness": 0.84,
    },
    "httpx": {
        "desc": "HTTP probing and tech detection",
        "endpoint": "/api/tools/httpx",
        "method": "POST",
        "category": "web_recon",
        "params": {"target": {"required": True}},
        "optional": {"probe": True, "tech_detect": False, "status_code": False, "title": False, "additional_args": ""},
        "effectiveness": 0.85,
    },
    "hurl": {
        "desc": "Hexadecimal & URL encoder + decoder with support for various encodings and transformations",
        "endpoint": "/api/tools/data_processing/hurl",
        "method": "POST",
        "category": "data_processing",
        "params": {"input": {"required": True}},
        "optional": {"mode": "base64_encode", "suppress": True, "additional_args": ""},
        "effectiveness": 0.84,
    },
    "testssl": {
        "desc": "TLS and SSL analysis with testssl.sh",
        "endpoint": "/api/tools/testssl",
        "method": "POST",
        "category": "web_recon",
        "params": {"target": {"required": True}},
        "optional": {"protocols": True, "server_defaults": True, "quiet": True, "additional_args": ""},
        "effectiveness": 0.89,
    },
    "dirsearch": {
        "desc": "Web path scanner",
        "endpoint": "/api/tools/dirsearch",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.87,
    },
    "wafw00f": {
        "desc": "Web application firewall detection",
        "endpoint": "/api/tools/wafw00f",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
    "wpscan": {
        "desc": "WordPress vulnerability scanner",
        "endpoint": "/api/tools/wpscan",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": "--disable-tls-checks --enumerate u,vp,vt"},
        "effectiveness": 0.95,
    },
    "joomscan": {
        "desc": "Joomla vulnerability scanner",
        "endpoint": "/api/tools/web_recon/joomscan",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.90,
    },

    "interactsh": {
        "desc": "Out-of-band interaction client for detecting blind vulnerabilities (SSRF, XSS, DNS exfiltration)",
        "endpoint": "/api/tools/web_scan/interactsh",
        "method": "POST",
        "category": "web_scan",
        "params": {},
        "optional": {
            "server": "",
            "token": "",
            "n": 1,
            "poll_interval": 5,
            "timeout": 60,
            "additional_args": "",
        },
        "effectiveness": 0.88,
    },

    # ---- Web Vuln ----
    "nuclei": {
        "desc": "Template-based vulnerability scanner",
        "endpoint": "/api/tools/nuclei",
        "method": "POST",
        "category": "web_vuln",
        "params": {"target": {"required": True}},
        "optional": {"severity": "", "tags": "", "template": "", "additional_args": ""},
        "effectiveness": 0.95,
    },
    "nikto": {
        "desc": "Web server vulnerability scanner",
        "endpoint": "/api/tools/nikto",
        "method": "POST",
        "category": "essential",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.85,
    },
    "sqlmap": {
        "desc": "Automatic SQL injection detection and exploitation",
        "endpoint": "/api/tools/sqlmap",
        "method": "POST",
        "category": "essential",
        "params": {"url": {"required": True}},
        "optional": {"data": "", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "dalfox": {
        "desc": "XSS vulnerability scanner",
        "endpoint": "/api/tools/dalfox",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"blind": False, "additional_args": ""},
        "effectiveness": 0.93,
    },
    "xsser": {
        "desc": "Cross-site scripting scanner",
        "endpoint": "/api/tools/xsser",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
    "dotdotpwn": {
        "desc": "Directory traversal scanner",
        "endpoint": "/api/tools/dotdotpwn",
        "method": "POST",
        "category": "web_recon",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.78,
    },
    "jaeles": {
        "desc": "Web security scanning framework",
        "endpoint": "/api/tools/jaeles",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.92,
    },

    # ---- Exploitation ----
    "commix": {
        "desc": "Command injection exploitation tool",
        "endpoint": "/api/tools/exploitation/commix",
        "method": "POST",
        "category": "exploitation",
        "params": {"url": {"required": True}},
        "optional": {"level": "", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "msfvenom": {
        "desc": "Metasploit payload generator",
        "endpoint": "/api/tools/msfvenom",
        "method": "POST",
        "category": "exploitation",
        "params": {"payload": {"required": True}},
        "optional": {"format": "elf", "lhost": "", "lport": "4444", "additional_args": ""},
        "effectiveness": 0.85,
    },
    # ---- Brute Force ----
    "hydra": {
        "desc": "Network login brute-forcer",
        "endpoint": "/api/tools/hydra",
        "method": "POST",
        "category": "essential",
        "params": {"target": {"required": True}, "service": {"required": True}},
        "optional": {"username": "", "username_file": "", "password": "", "password_file": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "hashcat": {
        "desc": "GPU-accelerated password cracker",
        "endpoint": "/api/tools/hashcat",
        "method": "POST",
        "category": "essential",
        "params": {"hash_file": {"required": True}, "hash_type": {"required": True}},
        "optional": {"attack_mode": "0", "wordlist": "/usr/share/wordlists/rockyou.txt", "mask": "", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "john": {
        "desc": "Password cracker with many formats",
        "endpoint": "/api/tools/john",
        "method": "POST",
        "category": "essential",
        "params": {"hash_file": {"required": True}},
        "optional": {"wordlist": "/usr/share/wordlists/rockyou.txt", "format_type": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "medusa": {
        "desc": "Network login brute-forcer",
        "endpoint": "/api/tools/medusa",
        "method": "POST",
        "category": "brute_force",
        "params": {"target": {"required": True}, "module": {"required": True}},
        "optional": {"username": "", "username_file": "", "password": "", "password_file": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "patator": {
        "desc": "Multi-purpose brute-forcer",
        "endpoint": "/api/tools/patator",
        "method": "POST",
        "category": "brute_force",
        "params": {"target": {"required": True}, "module": {"required": True}},
        "optional": {"username": "", "username_file": "", "password": "", "password_file": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "ophcrack": {
        "desc": "Windows hash cracker using rainbow tables",
        "endpoint": "/api/tools/password-cracking/ophcrack",
        "method": "POST",
        "category": "brute_force",
        "params": {"hash_file": {"required": True}},
        "optional": {"tables_dir": "", "tables": "", "additional_args": ""},
        "effectiveness": 0.75,
    },
    "hashid": {
        "desc": "Identify hash types from hash strings",
        "endpoint": "/api/tools/password_cracking/hashid",
        "method": "POST",
        "category": "brute_force",
        "params": {"hash": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
    # ---- Active Directory ----
    "ldapdomaindump": {
        "desc": "Dump LDAP information from Active Directory",
        "endpoint": "/api/tools/active_directory/ldapdomaindump",
        "method": "POST",
        "category": "active_directory",
        "params": {"hostname": {"required": True}},
        "optional": {"username": "", "password": "", "authtype" : "NTLM"},
        "effectiveness": 0.85,
    },
    "impacket-scripts": {
        "desc": "Execute Impacket scripts with dynamic arguments (e.g. GetADUsers, secretsdump, smbclient, psexec)",
        "endpoint": "/api/tool/active_directory/impacket",
        "method": "POST",
        "category": "active_directory",
        "params": {
            "script": {"required": True},
            "target": {"required": True}
        },
        "optional": {
            "options": ""
        },
        "effectiveness": 0.90
    },
    "impacket-spec": {
        "desc": "Retrieve argument specification and usage for a given Impacket script",
        "endpoint": "/api/tool/active_directory/impacket/spec",
        "method": "POST",
        "category": "active_directory",
        "params": {
            "script": {"required": True}
        },
        "optional": {},
        "effectiveness": 0.85,
        "parent_tool": "impacket-scripts"
    },
    "impacket-ad-enum": {
        "desc": "Convenience wrapper for Active Directory enumeration Impacket scripts such as GetADUsers, GetNPUsers, GetUserSPNs, lookupsid, and findDelegation",
        "endpoint": "/api/tool/active_directory/impacket",
        "method": "POST",
        "category": "active_directory",
        "params": {
            "script": {"required": True},
            "target": {"required": True}
        },
        "optional": {
            "dc_ip": "",
            "username": "",
            "password": "",
            "hashes": "",
            "kerberos": False,
            "no_pass": False,
            "aes_key": "",
            "debug": False,
            "extra_options": "",
            "extra_args": ""
        },
        "effectiveness": 0.92,
        "parent_tool": "impacket-scripts"
    },
    "impacket-remote-exec": {
        "desc": "Convenience wrapper for remote execution Impacket scripts such as psexec, wmiexec, smbexec, dcomexec, and atexec",
        "endpoint": "/api/tool/active_directory/impacket",
        "method": "POST",
        "category": "lateral_movement",
        "params": {
            "script": {"required": True},
            "target": {"required": True}
        },
        "optional": {
            "command": "",
            "username": "",
            "password": "",
            "domain": "",
            "hashes": "",
            "kerberos": False,
            "no_pass": False,
            "aes_key": "",
            "share": "",
            "shell_type": "",
            "debug": False,
            "extra_options": "",
            "extra_args": "",
            "use_recovery": True
        },
        "effectiveness": 0.91,
        "parent_tool": "impacket-scripts"
    },
    # ---- OSINT ----
    "parsero": {
        "desc": " Reads the Robots.txt file of a web server and looks at the Disallow entries.",
        "endpoint": "/api/tools/osint/parsero",
        "method": "POST",
        "category": "osint",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.85,
    },
    "whois": {
        "desc": "WHOIS lookup for domains and IPs",
        "endpoint": "/api/tools/whois",
        "method": "POST",
        "category": "osint",
        "params": {"target": {"required": True}},
        "optional": {},
        "effectiveness": 0.80,
    },
    "http-headers": {
        "desc": "Fetch HTTP response headers via curl -sI (security headers, server info, redirects)",
        "endpoint": "/api/tools/http-headers",
        "method": "POST",
        "category": "web_recon",
        "params": {"target": {"required": True}},
        "optional": {"https": False, "follow_redirects": True, "timeout": 10},
        "effectiveness": 0.82,
    },
    "dig": {
        "desc": "DNS record lookup — A, MX, NS, TXT records via dig +short",
        "endpoint": "/api/tools/dig",
        "method": "POST",
        "category": "osint",
        "params": {"target": {"required": True}},
        "optional": {"record_types": ["A", "MX", "NS", "TXT"], "timeout": 15},
        "effectiveness": 0.83,
        "parent_tool": "bind9-dnsutils"
    },
    "amass": {
        "desc": "Subdomain enumeration and OSINT",
        "endpoint": "/api/tools/amass",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"mode": "enum", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "subfinder": {
        "desc": "Passive subdomain discovery",
        "endpoint": "/api/tools/subfinder",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"silent": True, "all_sources": False, "additional_args": ""},
        "effectiveness": 0.82,
    },
    "assetfinder": {
        "desc": "Passive subdomain discovery using certificate and web sources",
        "endpoint": "/api/tools/assetfinder",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"only_subdomains": True, "additional_args": ""},
        "effectiveness": 0.80,
    },
    "shuffledns": {
        "desc": "Active subdomain bruteforce and resolution with wildcard handling",
        "endpoint": "/api/tools/shuffledns",
        "method": "POST",
        "category": "osint",
        "params": {},
        "optional": {
            "domain": "",
            "domains": [],
            "auto_domain": False,
            "list": "",
            "wordlist": "",
            "resolver": "",
            "trusted_resolver": "",
            "raw_input": "",
            "mode": "",
            "threads": 10000,
            "output": "",
            "json": False,
            "wildcard_output": "",
            "massdns": "",
            "massdns_cmd": "",
            "directory": "",
            "retries": 5,
            "strict_wildcard": False,
            "wildcard_threads": 250,
            "silent": False,
            "version": False,
            "verbose": False,
            "no_color": False,
            "update": False,
            "disable_update_check": False,
            "additional_args": ""
        },
        "effectiveness": 0.86,
    },
    "massdns": {
        "desc": "High-performance DNS stub resolver for bulk subdomain resolution",
        "endpoint": "/api/tools/massdns",
        "method": "POST",
        "category": "osint",
        "params": {"domainlist": {"required": True}},
        "optional": {
            "bindto": "",
            "busy_poll": False,
            "resolve_count": 50,
            "drop_group": "",
            "drop_user": "",
            "extended_input": False,
            "filter": "",
            "flush": False,
            "ignore": "",
            "interval": 500,
            "error_log": "",
            "norecurse": False,
            "output": "",
            "predictable": False,
            "processes": 1,
            "quiet": False,
            "rand_src_ipv6": "",
            "rcvbuf": 0,
            "retry": "",
            "resolvers": "",
            "root": False,
            "hashmap_size": 10000,
            "sndbuf": 0,
            "status_format": "",
            "sticky": False,
            "socket_count": 1,
            "record_type": "A",
            "verify_ip": False,
            "outfile": "",
            "additional_args": ""
        },
        "effectiveness": 0.87,
    },
    "sublist3r": {
        "desc": "Subdomain enumeration using OSINT sources",
        "endpoint": "/api/osint/tools/sublist3r",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"threads": 3, "engine": ""},
        "effectiveness": 0.80,
    },
    "fierce": {
        "desc": "DNS reconnaissance tool",
        "endpoint": "/api/tools/fierce",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.75,
    },
    "dnsenum": {
        "desc": "DNS enumeration and zone transfer",
        "endpoint": "/api/tools/dnsenum",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.78,
    },
    "gau": {
        "desc": "Fetch known URLs from AlienVault/Wayback",
        "endpoint": "/api/tools/gau",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.82,
    },
    "waybackurls": {
        "desc": "Fetch URLs from Wayback Machine",
        "endpoint": "/api/tools/waybackurls",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
    "theHarvester": {
        "desc": "Passive information gathering from public sources",
        "endpoint": "/api/tools/recon/theharvester",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
    # ---- WiFi Pentest ----
    "eaphammer" : {
        "desc": "Rogue access point framework for WiFi pentesting",
        "endpoint": "/api/tools/wifi_pentest/eaphammer",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}, "essid": {"required": True}},
        "optional": {"channel": 6, "auth_mode": "", "attack_type": "", "negotiate": "", "cert_path": ""},
        "effectiveness": 0.88,
    },
    "aircrack-ng": {
        "desc": "Crack WPA/WPA2 PSK from captured handshake files using a wordlist.",
        "endpoint": "/api/tools/wifi_pentest/aircrack_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {
            "capture_files": {"required": True},
            "wordlist":      {"required": True},
        },
        "optional": {"bssid": ""},
        "effectiveness": 0.91,
    },
    "airmon-ng": {
        "desc": "Enable or disable monitor mode on a wireless interface.",
        "endpoint": "/api/tools/wifi_pentest/airmon_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {
            "interface": {"required": True},
            "action":    {"required": True},
        },
        "optional": {"channel": ""},
        "effectiveness": 0.95,
    },
    "airodump-ng": {
        "desc": "Passive 802.11 capture — discovers APs/clients, captures WPA handshakes.",
        "endpoint": "/api/tools/wifi_pentest/airodump_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {
            "output_prefix": "capture",
            "bssid":         "",
            "channel":       "",
            "essid":         "",
        },
        "effectiveness": 0.93,
    },
    "aireplay-ng": {
        "desc": "Packet injection — deauth, fake auth, ARP replay, injection test.",
        "endpoint": "/api/tools/wifi_pentest/aireplay_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {
            "interface":   {"required": True},
            "attack_mode": {"required": True},
        },
        "optional": {
            "bssid":      "",
            "client_mac": "",
            "count":      0,
        },
        "effectiveness": 0.90,
    },

    "checksec": {
        "desc": "Check binary security properties (NX, PIE, RELRO)",
        "endpoint": "/api/tools/checksec",
        "method": "POST",
        "category": "binary",
        "params": {"file": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.85,
    },
    "binwalk": {
        "desc": "Firmware analysis and extraction",
        "endpoint": "/api/tools/binwalk",
        "method": "POST",
        "category": "binary",
        "params": {"file": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
    "strings": {
        "desc": "Extract printable strings from binary",
        "endpoint": "/api/tools/strings",
        "method": "POST",
        "category": "forensics",
        "params": {"file": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.70,
    },
    "ropgadget": {
        "desc": "Find ROP gadgets in binary",
        "endpoint": "/api/tools/ropgadget",
        "method": "POST",
        "category": "binary",
        "params": {"file": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.82,
    },
    "radare2": {
        "desc": "Binary analysis and disassembly",
        "endpoint": "/api/tools/radare2",
        "method": "POST",
        "category": "binary",
        "params": {"file": {"required": True}},
        "optional": {"commands": "", "additional_args": ""},
        "effectiveness": 0.88,
    },

    # ---- Cloud ----
    "pacu" : {
        "desc": "AWS exploitation framework for post-compromise activities",
        "endpoint": "/api/tools/pacu",
        "method": "POST",
        "category": "cloud",
        "params": {"session_name": {"required": True}},
        "optional": {"modules": "", "data_services": "", "regions": "", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "cloudmapper" : {
        "desc": "AWS network visualization and security analysis",
        "endpoint": "/api/tools/cloudmapper",
        "method": "POST",
        "category": "cloud",
        "params": {"account": {"required": True}, "action": {"required": True}},
        "optional": {"config": "config.json", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "prowler": {
        "desc": "AWS/Azure/GCP security audit",
        "endpoint": "/api/tools/prowler",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"provider": "aws", "profile": "default", "region": "", "checks": "", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "trivy": {
        "desc": "Container and filesystem vulnerability scanner",
        "endpoint": "/api/tools/trivy",
        "method": "POST",
        "category": "cloud",
        "params": {"target": {"required": True}},
        "optional": {"scan_type": "image", "severity": "", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "kube-hunter": {
        "desc": "Kubernetes penetration testing",
        "endpoint": "/api/tools/kube-hunter",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"additional_args": ""},
        "effectiveness": 0.82,
    },
    # ---- Bots and AI-driven tools ----
    "bbot": {
        "desc": "Reconnaissance and enumeration with BBot",
        "endpoint": "/api/bot/bbot",
        "method": "POST",
        "category": "osint",
        "params": {"target": {"required": True}, "parameters": {"required": True}},
        "optional": {},
        "effectiveness": 0.90,
    },

    # ---- Binary Analysis (extended) ----
    "angr": {
        "desc": "Binary analysis framework — symbolic execution, CFG, static analysis",
        "endpoint": "/api/tools/angr",
        "method": "POST",
        "category": "binary",
        "params": {"binary": {"required": True}},
        "optional": {"script_content": "", "find_address": "", "avoid_addresses": "", "analysis_type": "symbolic", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "ghidra": {
        "desc": "NSA reverse engineering suite — decompile and analyse binaries",
        "endpoint": "/api/tools/ghidra",
        "method": "POST",
        "category": "binary",
        "params": {"binary": {"required": True}},
        "optional": {"project_name": "analysis_project", "script_file": "", "analysis_timeout": 300, "output_format": "xml", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "objdump": {
        "desc": "Disassemble and inspect object files and binaries",
        "endpoint": "/api/tools/objdump",
        "method": "POST",
        "category": "binary",
        "params": {"binary": {"required": True}},
        "optional": {"disassemble": True, "additional_args": ""},
        "effectiveness": 0.78,
    },
    "one-gadget": {
        "desc": "Find one-gadget RCE offsets in libc",
        "endpoint": "/api/tools/one-gadget",
        "method": "POST",
        "category": "binary",
        "params": {"libc_path": {"required": True}},
        "optional": {"level": 1, "additional_args": ""},
        "effectiveness": 0.87,
    },
    "ropper": {
        "desc": "ROP/JOP gadget finder with quality filtering",
        "endpoint": "/api/tools/ropper",
        "method": "POST",
        "category": "binary",
        "params": {"binary": {"required": True}},
        "optional": {"gadget_type": "rop", "quality": 1, "arch": "", "search_string": "", "additional_args": ""},
        "effectiveness": 0.84,
    },
    "libc-database": {
        "desc": "Look up libc version by symbol offsets",
        "endpoint": "/api/tools/libc-database",
        "method": "POST",
        "category": "binary",
        "params": {"symbols": {"required": True}},
        "optional": {"action": "find", "libc_id": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "xxd": {
        "desc": "Hex dump a file with optional offset and length",
        "endpoint": "/api/tools/xxd",
        "method": "POST",
        "category": "forensics",
        "params": {"file_path": {"required": True}},
        "optional": {"offset": "0", "length": "", "additional_args": ""},
        "effectiveness": 0.70,
    },
    "autopsy": {
        "desc": "Digital forensics platform — disk image analysis",
        "endpoint": "/api/tools/binary_analysis/autopsy",
        "method": "POST",
        "category": "forensics",
        "params": {"image_path": {"required": True}},
        "optional": {"case_name": "analysis_case", "additional_args": ""},
        "effectiveness": 0.82,
    },

    # ---- Binary Debug ----
    "gdb": {
        "desc": "GNU debugger — dynamic binary analysis and exploit dev",
        "endpoint": "/api/tools/gdb",
        "method": "POST",
        "category": "binary",
        "params": {"binary": {"required": True}},
        "optional": {"commands": "", "script_file": "", "additional_args": ""},
        "effectiveness": 0.88,
    },
    # ---- Exploitation (extended) ----
    "pwntools": {
        "desc": "Run a pwntools exploit script against a local or remote target",
        "endpoint": "/api/tools/pwntools",
        "method": "POST",
        "category": "binary",
        "params": {"script_content": {"required": True}},
        "optional": {"target_binary": "", "target_host": "", "target_port": 0, "exploit_type": "local", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "pwninit": {
        "desc": "Patch a CTF binary to use the provided libc, generate exploit template",
        "endpoint": "/api/tools/pwninit",
        "method": "POST",
        "category": "binary",
        "params": {"binary": {"required": True}},
        "optional": {"libc": "", "ld": "", "template_type": "python", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "dirb": {
        "desc": "Classic web content scanner using a wordlist",
        "endpoint": "/api/tools/dirb",
        "method": "POST",
        "category": "essential",
        "params": {"url": {"required": True}},
        "optional": {"wordlist": "/usr/share/wordlists/dirb/common.txt", "additional_args": ""},
        "effectiveness": 0.78,
    },
    "hakrawler": {
        "desc": "Fast web crawler — extracts links, forms, and endpoints",
        "endpoint": "/api/tools/hakrawler",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"depth": 2, "forms": True, "robots": True, "sitemap": True, "wayback": False, "additional_args": ""},
        "effectiveness": 0.83,
    },
    "autorecon": {
        "desc": "Automated multi-tool recon — runs nmap, web, and service scanners",
        "endpoint": "/api/tools/autorecon",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"output_dir": "/tmp/autorecon", "port_scans": "top-100-ports", "service_scans": "default", "heartbeat": 60, "timeout": 300, "additional_args": ""},
        "effectiveness": 0.88,
    },
    "wfuzz": {
        "desc": "Web fuzzer for directories, parameters, and authentication",
        "endpoint": "/api/tools/wfuzz",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"wordlist": "/usr/share/wordlists/dirb/common.txt", "additional_args": ""},
        "effectiveness": 0.82,
    },
    "graphql-scanner": {
        "desc": "GraphQL introspection and mutation vulnerability scanner",
        "endpoint": "/api/tools/graphql_scanner",
        "method": "POST",
        "category": "web_vuln",
        "params": {"endpoint": {"required": True}},
        "optional": {"introspection": True, "query_depth": 10, "mutations": True},
        "effectiveness": 0.85,
    },
    "jwt-analyzer": {
        "desc": "Decode and attack JWT tokens — alg:none, RS256→HS256, brute secret",
        "endpoint": "/api/tools/jwt_analyzer",
        "method": "POST",
        "category": "web_vuln",
        "params": {"jwt_token": {"required": True}},
        "optional": {"target_url": ""},
        "effectiveness": 0.85,
    },
    "api-schema-analyzer": {
        "desc": "Analyse OpenAPI/Swagger/GraphQL schemas for security issues",
        "endpoint": "/api/tools/api_schema_analyzer",
        "method": "POST",
        "category": "api",
        "params": {"schema_url": {"required": True}},
        "optional": {"schema_type": "openapi"},
        "effectiveness": 0.82,
    },

    # ---- Parameter Discovery ----
    "arjun": {
        "desc": "HTTP parameter discovery — find hidden GET/POST params",
        "endpoint": "/api/tools/arjun",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"method": "GET", "wordlist": "", "delay": 0, "threads": 25, "stable": False, "additional_args": ""},
        "effectiveness": 0.85,
    },
    "paramspider": {
        "desc": "Mine URL parameters from web archives for a domain",
        "endpoint": "/api/tools/paramspider",
        "method": "POST",
        "category": "web_recon",
        "params": {"domain": {"required": True}},
        "optional": {"level": 2, "exclude": "png,jpg,gif,jpeg,swf,woff,svg,pdf,css,ico", "output": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "x8": {
        "desc": "Hidden HTTP parameter discovery via response diffing",
        "endpoint": "/api/tools/x8",
        "method": "POST",
        "category": "web_recon",
        "params": {"url": {"required": True}},
        "optional": {"wordlist": "/usr/share/wordlists/x8/params.txt", "method": "GET", "body": "", "headers": "", "additional_args": ""},
        "effectiveness": 0.83,
    },

    # ---- Parameter Fuzzing ----
    "qsreplace": {
        "desc": "Replace query-string parameter values in a list of URLs",
        "endpoint": "/api/tools/qsreplace",
        "method": "POST",
        "category": "api",
        "params": {"urls": {"required": True}},
        "optional": {"replacement": "FUZZ", "additional_args": ""},
        "effectiveness": 0.72,
    },

    # ---- URL Recon / Filtering ----
    "anew": {
        "desc": "Append unique lines to a file — deduplication for recon pipelines",
        "endpoint": "/api/tools/anew",
        "method": "POST",
        "category": "data_processing",
        "params": {"input_data": {"required": True}},
        "optional": {"output_file": "", "additional_args": ""},
        "effectiveness": 0.70,
    },
    "uro": {
        "desc": "Filter and deduplicate URL lists — remove noise from recon output",
        "endpoint": "/api/tools/uro",
        "method": "POST",
        "category": "api",
        "params": {"urls": {"required": True}},
        "optional": {"whitelist": "", "blacklist": "", "additional_args": ""},
        "effectiveness": 0.75,
    },

    # ---- SMB Enumeration (extended) ----
    "nbtscan": {
        "desc": "NetBIOS name scanner — discover Windows hosts on a subnet",
        "endpoint": "/api/tools/nbtscan",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"verbose": False, "timeout": 2, "additional_args": ""},
        "effectiveness": 0.78,
    },
    "enum4linux-ng": {
        "desc": "Next-gen enum4linux — SMB/RPC enumeration with JSON output",
        "endpoint": "/api/tools/enum4linux-ng",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"username": "", "password": "", "domain": "", "shares": True, "users": True, "groups": True, "policy": True, "additional_args": ""},
        "effectiveness": 0.85,
    },
    "rpcclient": {
        "desc": "Windows RPC enumeration — users, groups, shares via MSRPC",
        "endpoint": "/api/tools/rpcclient",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"username": "", "password": "", "domain": "", "commands": "enumdomusers;enumdomgroups;querydominfo", "additional_args": ""},
        "effectiveness": 0.82,
    },

    # ---- Credential Harvesting ----
    "responder": {
        "desc": "LLMNR/NBT-NS/MDNS poisoner — harvest NTLMv2 hashes",
        "endpoint": "/api/tools/responder",
        "method": "POST",
        "category": "network_recon",
        "params": {"interface": {"required": True}},
        "optional": {"analyze": False, "wpad": True, "force_wpad_auth": False, "fingerprint": False, "duration": 300, "additional_args": ""},
        "effectiveness": 0.88,
    },

    # ---- Forensics ----
    "volatility": {
        "desc": "Memory forensics framework v2 — analyse RAM dumps",
        "endpoint": "/api/tools/volatility",
        "method": "POST",
        "category": "forensics",
        "params": {"memory_file": {"required": True}, "plugin": {"required": True}},
        "optional": {"profile": "", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "foremost": {
        "desc": "File carving — recover files from disk images by file headers",
        "endpoint": "/api/tools/foremost",
        "method": "POST",
        "category": "forensics",
        "params": {"input_file": {"required": True}},
        "optional": {"output_dir": "/tmp/foremost_output", "file_types": "", "additional_args": ""},
        "effectiveness": 0.82,
    },
    "steghide": {
        "desc": "Steganography — embed or extract hidden data from image/audio files",
        "endpoint": "/api/tools/steghide",
        "method": "POST",
        "category": "forensics",
        "params": {"cover_file": {"required": True}},
        "optional": {"action": "extract", "embed_file": "", "passphrase": "", "output_file": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "exiftool": {
        "desc": "Read and write metadata from image, audio, and document files",
        "endpoint": "/api/tools/exiftool",
        "method": "POST",
        "category": "forensics",
        "params": {"file_path": {"required": True}},
        "optional": {"output_format": "", "tags": "", "additional_args": ""},
        "effectiveness": 0.82,
    },
    "hashpump": {
        "desc": "Hash length extension attack tool",
        "endpoint": "/api/tools/hashpump",
        "method": "POST",
        "category": "forensics",
        "params": {"signature": {"required": True}, "data": {"required": True}, "key_length": {"required": True}, "append_data": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.85,
    },

    # ---- Cloud (extended) ----
    "scout-suite": {
        "desc": "Multi-cloud security auditing — AWS, Azure, GCP, OCI",
        "endpoint": "/api/tools/scout-suite",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"provider": "aws", "profile": "default", "report_dir": "/tmp/scout-suite", "services": "", "exceptions": "", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "clair": {
        "desc": "Container vulnerability scanner — static analysis of OCI/Docker images",
        "endpoint": "/api/tools/clair",
        "method": "POST",
        "category": "cloud",
        "params": {"image": {"required": True}},
        "optional": {"config": "/etc/clair/config.yaml", "output_format": "json", "additional_args": ""},
        "effectiveness": 0.83,
    },
    "docker-bench-security": {
        "desc": "CIS Docker Benchmark checks for container host security",
        "endpoint": "/api/tools/docker-bench-security",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"checks": "", "exclude": "", "output_file": "/tmp/docker-bench-results.json", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "checkov": {
        "desc": "IaC static analysis — Terraform, CloudFormation, Kubernetes manifests",
        "endpoint": "/api/tools/checkov",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"directory": ".", "framework": "", "check": "", "skip_check": "", "output_format": "json", "additional_args": ""},
        "effectiveness": 0.87,
    },
    "terrascan": {
        "desc": "IaC security scanner — detect misconfigs across Terraform/K8s/etc.",
        "endpoint": "/api/tools/terrascan",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"scan_type": "all", "iac_dir": ".", "policy_type": "", "output_format": "json", "severity": "", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "kube-bench": {
        "desc": "CIS Kubernetes Benchmark — check cluster node/master security config",
        "endpoint": "/api/tools/kube-bench",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"targets": "", "version": "", "config_dir": "", "output_format": "json", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "falco": {
        "desc": "Runtime security monitoring — detect anomalous container/host behaviour",
        "endpoint": "/api/tools/falco",
        "method": "POST",
        "category": "cloud",
        "params": {},
        "optional": {"config_file": "/etc/falco/falco.yaml", "rules_file": "", "output_format": "json", "duration": 60, "additional_args": ""},
        "effectiveness": 0.83,
    },

    # ---- Network ----
    "nxc": {
        "desc": "NetExec (nxc) — network service exploitation framework (SMB/WinRM/LDAP)",
        "endpoint": "/api/tools/netexec",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"protocol": "smb", "username": "", "password": "", "module": "", "additional_args": ""},
        "effectiveness": 0.87,
    },
    "evil-winrm": {
        "desc": "WinRM shell for Windows remote management and lateral movement",
        "endpoint": "/api/tools/evil_winrm",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}, "username": {"required": True}},
        "optional": {"password": "", "hash": "", "additional_args": ""},
        "effectiveness": 0.85,
    },

    # ---- Exploitation ----
    "msfconsole": {
        "desc": "Metasploit console — interactive exploitation framework",
        "endpoint": "/api/tools/metasploit",
        "method": "POST",
        "category": "exploitation",
        "params": {"module": {"required": True}},
        "optional": {"options": {}},
        "effectiveness": 0.92,
    },
    "searchsploit": {
        "desc": "Search Exploit-DB offline for public exploits and PoCs",
        "endpoint": "/api/tools/exploit_framework/exploit_db",
        "method": "POST",
        "category": "exploitation",
        "params": {"query": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.88,
    },

    # ---- Web / API ----
    "whatweb": {
        "desc": "Web scanner for technology fingerprinting and version detection",
        "endpoint": "/api/tools/web_recon/whatweb",
        "method": "POST",
        "category": "fingerprint",
        "params": {"url": {"required": True}},
        "optional": {},
        "effectiveness": 0.80,
    },
    "burpsuite": {
        "desc": "Burp Suite web application security testing platform",
        "endpoint": "/api/tools/burpsuite-alternative",
        "method": "POST",
        "category": "web_recon",
        "params": {"target": {"required": True}},
        "optional": {"scan_type": "comprehensive", "headless": True, "max_depth": 3, "max_pages": 50},
        "effectiveness": 0.90,
    },
    "zaproxy": {
        "desc": "OWASP ZAP web application security scanner",
        "endpoint": "/api/tools/zap",
        "method": "POST",
        "category": "web_vuln",
        "params": {"target": {"required": True}},
        "optional": {"scan_type": "baseline", "api_key": "", "port": "8090", "output_format": "xml", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "http-framework": {
        "desc": "HTTP/S request tool — manual probing and PoC verification",
        "endpoint": "/api/tools/http-framework",
        "method": "POST",
        "category": "api",
        "params": {"url": {"required": True}},
        "optional": {"method": "GET", "data": "", "headers": "", "action": "request", "cookies": ""},
        "effectiveness": 0.75,
        "parent_tool": "curl",
    },
    # "httpie": {
    #     "desc": "Human-friendly HTTP client for API testing and inspection",
    #     "endpoint": "/api/tools/http-framework",
    #     "method": "POST",
    #     "category": "api",
    #     "params": {"url": {"required": True}},
    #     "optional": {"method": "GET", "data": "", "headers": ""},
    #     "effectiveness": 0.75,
    # },
    # "postman": {
    #     "desc": "API platform for building and testing HTTP requests",
    #     "endpoint": "/api/tools/http-framework",
    #     "method": "POST",
    #     "category": "api",
    #     "params": {"url": {"required": True}},
    #     "optional": {"method": "GET", "data": "", "headers": ""},
    #     "effectiveness": 0.78,
    # },
    # "insomnia": {
    #     "desc": "REST/GraphQL API client for design and testing",
    #     "endpoint": "/api/tools/http-framework",
    #     "method": "POST",
    #     "category": "api",
    #     "params": {"url": {"required": True}},
    #     "optional": {"method": "GET", "data": "", "headers": ""},
    #     "effectiveness": 0.76,
    # },
    "api_fuzzer": {
        "desc": "Custom API fuzzer for parameter and endpoint fuzzing.",
        "endpoint": "/api/tools/api_fuzzer",
        "method": "POST",
        "category": "api",
        "params": {"base_url": {"required": True}},
        "optional": {"method": "GET", "wordlist": "/usr/share/wordlists/dirb/common.txt", "endpoints": []},
        "effectiveness": 0.80,
        "parent_tool": "ffuf",
    },
    "schemathesis": {
        "desc": "Property-based API testing driven by OpenAPI/GraphQL schemas (schemathesis)",
        "endpoint": "/api/tools/api_fuzz/schemathesis",
        "method": "POST",
        "category": "api",
        "params": {"schema": {"required": True}},
        "optional": {
            "base_url": "",
            "checks": "all",
            "workers": 1,
            "max_examples": 100,
            "headers": "",
            "auth": "",
            "request_timeout": 10,
            "timeout": 600,
            "phases": "",
            "mode": "",
            "rate_limit": "",
            "report_formats": "",
            "report_dir": "",
            "include_operation_id": "",
            "exclude_operation_id": "",
            "max_failures": 0,
            "additional_args": "",
        },
        "effectiveness": 0.88,
    },

    # ---- OSINT ----
    "sherlock": {
        "desc": "Username investigation across 400+ social networks",
        "endpoint": "/api/tools/osint/sherlock",
        "method": "POST",
        "category": "osint",
        "params": {"username": {"required": True}},
        "optional": {},
        "effectiveness": 0.85,
    },
    # "social-analyzer": {
    #     "desc": "Social media presence analysis and OSINT gathering",
    #     "endpoint": "/api/tools/osint/social_analyzer",
    #     "method": "POST",
    #     "category": "osint",
    #     "params": {"username": {"required": True}},
    #     "optional": {"additional_args": ""},
    #     "effectiveness": 0.80,
    # },
    "recon-ng": {
        "desc": "Web reconnaissance framework with modular architecture",
        "endpoint": "/api/tools/recon_ng",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"modules": "", "additional_args": ""},
        "effectiveness": 0.83,
    },
    "maltego": {
        "desc": "Link analysis and data mining for OSINT investigations",
        "endpoint": "/api/tools/maltego",
        "method": "POST",
        "category": "osint",
        "params": {"target": {"required": True}},
        "optional": {"transforms": "", "additional_args": ""},
        "effectiveness": 0.82,
    },
    "spiderfoot": {
        "desc": "OSINT automation with 200+ data-gathering modules",
        "endpoint": "/api/tools/osint/spiderfoot",
        "method": "POST",
        "category": "osint",
        "params": {"target": {"required": True}},
        "optional": {},
        "effectiveness": 0.85,
    },
    # "shodan-cli": {
    #     "desc": "Shodan CLI — search internet-connected devices and services",
    #     "endpoint": "/api/tools/shodan",
    #     "method": "POST",
    #     "category": "osint",
    #     "params": {"query": {"required": True}},
    #     "optional": {"additional_args": ""},
    #     "effectiveness": 0.88,
    # },
    # "censys-cli": {
    #     "desc": "Censys CLI — internet asset discovery and certificate analysis",
    #     "endpoint": "/api/tools/censys",
    #     "method": "POST",
    #     "category": "osint",
    #     "params": {"query": {"required": True}},
    #     "optional": {"additional_args": ""},
    #     "effectiveness": 0.85,
    # },
    # "have-i-been-pwned": {
    #     "desc": "Check if credentials or domains appear in breach data",
    #     "endpoint": "/api/tools/hibp",
    #     "method": "POST",
    #     "category": "osint",
    #     "params": {"query": {"required": True}},
    #     "optional": {"additional_args": ""},
    #     "effectiveness": 0.80,
    # },

    # ---- Password ----
    "hashcat-utils": {
        "desc": "Hashcat utility tools — cap2hccapx, combinator, expander, etc.",
        "endpoint": "/api/tools/hashcat",
        "method": "POST",
        "category": "brute_force",
        "params": {"hash_file": {"required": True}, "hash_type": {"required": True}},
        "optional": {"attack_mode": "0", "wordlist": "/usr/share/wordlists/rockyou.txt", "additional_args": ""},
        "effectiveness": 0.80,
    },

    # ---- Forensics ----
    "vol": {
        "desc": "Volatility memory forensics (vol shorthand) — analyse RAM dumps",
        "endpoint": "/api/tools/volatility",
        "method": "POST",
        "category": "forensics",
        "params": {"memory_file": {"required": True}, "plugin": {"required": True}},
        "optional": {"profile": "", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "photorec": {
        "desc": "File recovery — carve deleted files from disk images or drives",
        "endpoint": "/api/tools/photorec",
        "method": "POST",
        "category": "forensics",
        "params": {"input_file": {"required": True}},
        "optional": {"output_dir": "/tmp/photorec_output", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "testdisk": {
        "desc": "Disk partition recovery and repair tool",
        "endpoint": "/api/tools/testdisk",
        "method": "POST",
        "category": "forensics",
        "params": {"disk": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.78,
    },
    "scalpel": {
        "desc": "File carving tool with configurable headers and footers",
        "endpoint": "/api/tools/scalpel",
        "method": "POST",
        "category": "forensics",
        "params": {"input_file": {"required": True}},
        "optional": {"output_dir": "/tmp/scalpel_output", "config": "", "additional_args": ""},
        "effectiveness": 0.78,
    },
    "bulk_extractor": {
        "desc": "Extract features (emails, URLs, credit cards) from disk images or files",
        "endpoint": "/api/tools/bulk_extractor",
        "method": "POST",
        "category": "forensics",
        "params": {"input_file": {"required": True}},
        "optional": {"output_dir": "/tmp/bulk_extractor_output", "scanners": "", "additional_args": ""},
        "effectiveness": 0.82,
    },
    "stegsolve": {
        "desc": "Steganography analysis — visual inspection and bit-plane analysis",
        "endpoint": "/api/tools/stegsolve",
        "method": "POST",
        "category": "forensics",
        "params": {"file_path": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.75,
    },
    "zsteg": {
        "desc": "PNG/BMP steganography detection and extraction",
        "endpoint": "/api/tools/zsteg",
        "method": "POST",
        "category": "forensics",
        "params": {"file_path": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.78,
    },
    "outguess": {
        "desc": "Universal steganographic tool for JPEG images",
        "endpoint": "/api/tools/outguess",
        "method": "POST",
        "category": "forensics",
        "params": {"file_path": {"required": True}},
        "optional": {"action": "extract", "passphrase": "", "output_file": "", "additional_args": ""},
        "effectiveness": 0.74,
    },
    "file": {
        "desc": "Identify file type by magic bytes — essential for forensics triage",
        "endpoint": "/api/tools/file_type",
        "method": "POST",
        "category": "forensics",
        "params": {"file_path": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.70,
    },
    "sleuthkit": {
        "desc": "Collection of command-line digital forensics tools (fls, icat, mmls…)",
        "endpoint": "/api/tools/sleuthkit",
        "method": "POST",
        "category": "forensics",
        "params": {"image_path": {"required": True}},
        "optional": {"command": "fls", "additional_args": ""},
        "effectiveness": 0.83,
    },

    # ---- Wireless  ----
    "wireshark": {
        "desc": "Network protocol analyser — capture and dissect packets",
        "endpoint": "/api/tools/wireshark",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {"capture_filter": "", "duration": 60, "output_file": "", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "tshark": {
        "desc": "Terminal-based Wireshark — scriptable packet capture and analysis",
        "endpoint": "/api/tools/tshark",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {"capture_filter": "", "display_filter": "", "duration": 60, "output_file": "", "additional_args": ""},
        "effectiveness": 0.88,
    },
    "tcpdump": {
        "desc": "Low-level packet capture and analysis",
        "endpoint": "/api/tools/tcpdump",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {"filter": "", "count": 0, "output_file": "", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "kismet": {
        "desc": "Wireless network detector, sniffer, and IDS",
        "endpoint": "/api/tools/kismet",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {"log_prefix": "kismet", "duration": 60, "additional_args": ""},
        "effectiveness": 0.85,
    },
    "airbase-ng": {
        "desc": "Rogue access point framework for WiFi attacks",
        "endpoint": "/api/tools/wifi_pentest/airbase_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}, "essid": {"required": True}},
        "optional": {"channel": 6, "bssid": "", "wpa_mode": ""},
        "effectiveness": 0.80,
    },
    "aircrack-ng": {
        "desc": "WiFi password cracking tool for WEP/WPA/WPA2 handshakes",
        "endpoint": "/api/tools/password_cracking/aircrack_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"capture_files": {"required": True}, "wordlist": {"required": True}},
        "optional": {"bssid": ""},
        "effectiveness": 0.85,
    },
    "airdecap-ng": {
        "desc": "Decrypt WEP/WPA/WPA2 capture files with known keys",
        "endpoint": "/api/tools/wifi_pentest/airdecap_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"capture_file": {"required": True}},
        "optional": {"password": "", "wep_key": "", "bssid": "", "essid": ""},
        "effectiveness": 0.80,
    },
    "bettercap" : {
        "desc": "Advanced network attack framework for MITM, sniffing, and spoofing",
        "endpoint": "/api/tools/wifi_pentest/bettercap_wifi",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {"mode": "", "target_bssid": "", "caplet": ""},
        "effectiveness": 0.88,
    },
    "hcxdumptool": {
        "desc": "Capture raw 802.11 frames for offline analysis and cracking",
        "endpoint": "/api/tools/wifi_pentest/hcxdumptool",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {"output_file": "", "target_bssid": "", "duration": 1, "additional_args": ""},
        "effectiveness": 0.85,
    },
    "wifite": {
        "desc": "Automated wireless attack tool for WEP/WPA/WPA2 networks",
        "endpoint": "/api/tools/wifi_pentest/wifite2",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {"target_essid": "", "target_bssid": "attack_wps", "attack_pmkid": True, "attack_handshake": True, "wordlist": "", "timeout": 300},
        "effectiveness": 0.85,
    },
    "mdk4": {
        "desc": "WiFi DoS and attack tool for deauth, fake auth, beacon flood, and more",
        "endpoint": "/api/tools/wifi_pentest/mdk4",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}, "attack_mode": {"required": True}, "target_bssid": {"required": True}},
        "optional": {"ssid_wordlist": "", "burst_rate": 50},
        "effectiveness": 0.80,
    },  
    "hcxpcapngtool": {
        "desc": "Convert and filter 802.11 capture files for cracking and analysis",
        "endpoint": "/api/tools/wifi_pentest/hcxpcapngtool",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"input_file": {"required": True}, "output_file": {"required": True}},
        "optional": {},
        "effectiveness": 0.82,
    },
    
    # ---- Database ----
    "mysql": {
        "desc": "MySQL command-line client for database management and querying",
        "endpoint": "/api/tools/mysql",
        "method": "POST",
        "category": "database",
        "params": {"query": {"required": True}, "host": {"required": True}, "user": {"required": True}, "password": {"required": True}, "database": {"required": True}},
        "optional": {},
        "effectiveness": 0.90,
    },
    "sqlite3": {
        "desc": "SQLite command-line client for database management and querying",
        "endpoint": "/api/tools/sqlite3",
        "method": "POST",
        "category": "database",
        "params": {"db_path": {"required": True}, "query": {"required": True}},
        "optional": {},
        "effectiveness": 0.90,
    },
}

# Validate registry at import time
_validate_registry(TOOLS)

# Meta-tool for ending the agent loop
# can be skipped if not using agentic mode in your LLM connection when ran locally.
FINAL_ANSWER_TOOL = {
    "name": "final_answer",
    "desc": "Return your final answer to the user. Use when the task is complete.",
    "params": {"answer": {"required": True}},
}

# ---------------------------------------------------------------------------
# Category metadata
# ---------------------------------------------------------------------------

CATEGORIES = {
    "essential": "Essential tools",
    "network_recon": "Network scanning, port discovery, service enumeration",
    "web_recon": "Web directory brute-forcing, crawling, tech detection",
    "web_vuln": "Web vulnerability scanning (SQLi, XSS, template-based)",
    "brute_force": "Password cracking and login brute-forcing",
    "binary": "Binary analysis, reverse engineering, ROP gadgets",
    "forensics": "Memory forensics, file carving, steganography, metadata",
    "cloud": "Cloud security auditing (AWS, containers, Kubernetes, IaC)",
    "osint": "Subdomain enumeration, DNS recon, URL harvesting",
    "exploitation": "Exploit execution, payload generation, module search",
    "api": "API testing and schema analysis",
    "wifi_pentest": "WiFi pentesting and wireless attacks",
    "database": "Database management and querying",
    "active_directory": "Active Directory enumeration and exploitation",
    "vulnerability_intelligence": "Vulnerability research and intelligence gathering",
}

# ---------------------------------------------------------------------------
# Intent detection keywords -> category
# This is a simple heuristic mapping of common keywords to categories for 
# initial intent classification.
# In future, we could think about doing embedding-based similarity 
# or a small fine-tuned classifier for better accuracy, but this is a 
# good start and very cheap to compute.
# ---------------------------------------------------------------------------

_INTENT_KEYWORDS: Dict[str, List[str]] = {
    "network_recon": [
        "scan", "port", "host", "network", "service", "smb",
        "enum4linux", "discovery", "arp", "netbios", "smbmap",
    ],
    "active_directory": [
        "active directory", "ad", "ldap", "kerberos", "domain",
        "dc", "gpo", "group policy", "bloodhound", "impacket",
    ],
    "web_recon": [
        "directory", "dir", "brute", "fuzz", "ffuf", "crawl",
        "spider", "gospider", "wordpress", "wpscan", "vhost", "content", "ferox",
    ],
    "web_vuln": [
        "vuln", "vulnerability", "nuclei", "sql", "sqli", "xss",
        "injection", "exploit", "dalfox", "traversal",
    ],
    "exploitation": [
        "exploit", "metasploit", "msf", "payload", "msfvenom", "exploit-db",
        "cve", "shell", "reverse", "module",
    ],
    "brute_force": [
        "brute", "crack", "password", "login", "credential",
        "hash", "wordlist", "medusa", "patator", "ophcrack"
    ],
    "osint": [
        "subdomain", "dns", "osint", "amass", "subfinder", "assetfinder", "shuffledns", "massdns", "domain", "recon",
        "url", "fierce", "enumerate", "whois", "bbot", "theharvester", 
        "gau", "waybackurls", "waymore"
    ],
    "binary": [
        "binary", "reverse", "rop", "gadget", "checksec", "firmware", "elf",
        "disassemble", "radare", "strings", "binwalk",
    ],
    "cloud": [
        "cloud", "aws", "azure", "gcp", "container", "docker", "kubernetes",
        "k8s", "trivy", "prowler",
    ],
    "wifi_pentest": [
        "wifi", "wireless", "wpa", "wpa2", "wep", "handshake", "pmkid",
        "aircrack", "airmon", "airodump", "aireplay", "deauth", "beacon",
        "bssid", "essid", "ssid", "monitor", "eap", "evil twin", "rogue ap",
        "hcxdumptool", "wifite", "bettercap", "mdk4", "eaphammer",
    ],
    "forensics": [
        "forensics", "memory", "volatility", "ram", "dump", "carve", "recover",
        "steghide", "stego", "steganography", "metadata", "exiftool", "foremost",
        "hashpump", "length extension", "hash extension", "file recovery",
    ],
    "database": ["mysql", "sqlite3"],
    "essential": ["nmap", "gobuster", "dirb", "nikto", "sqlmap", "hydra", "john", "hashcat"],
    "vulnerability_intelligence": ["vulnx", "vulnerability intelligence", "vulnerability research", "cve search", "exploit research"]

}


SUGGESTED_APPROACHES: Dict[str, str] = {
    "network_recon": (
        "Run port scans (nmap/masscan/rustscan) and service fingerprinting. "
        "Enumerate SMB, RPC, and SNMP if open. Identify OS, banners, and software versions."
    ),
    "web_recon": (
        "Run directory/content discovery (gobuster/feroxbuster/ffuf). "
        "Crawl for endpoints and check for common misconfigurations. "
        "Fingerprint technologies and check for exposed admin panels or backup files."
    ),
    "web_vuln": (
        "Scan discovered endpoints for SQLi, XSS, SSRF, LFI, and template injection "
        "using nuclei, sqlmap, and dalfox. Check headers and cookies for misconfigurations."
    ),
    "exploitation": (
        "Search Exploit-DB and Metasploit for matching CVEs. "
        "Generate payloads with msfvenom and attempt initial access. "
        "Validate exploitability against the detected service versions."
    ),
    "brute_force": (
        "Brute-force login endpoints or crack captured hashes using hydra, medusa, "
        "john, or hashcat with an appropriate wordlist. Target SSH, FTP, HTTP basic auth, "
        "and web login forms."
    ),
    "osint": (
        "Enumerate subdomains (subfinder/amass/dnsenum), harvest emails via theHarvester, "
        "pull historical URLs (gau/waybackurls), and extract secrets from JS files. "
        "Check certificate transparency logs and WHOIS records."
    ),
    "active_directory": (
        "Run BloodHound/SharpHound collection. Enumerate AD objects via LDAP. "
        "Look for kerberoastable accounts, AS-REP roastable users, and misconfigured ACLs. "
        "Use impacket tools for lateral movement."
    ),
    "binary": (
        "Analyse the binary with checksec, strings, and radare2. "
        "Identify exploitable functions (gets, strcpy, system). "
        "Build ROP chains if NX is enabled. Use GDB/pwndbg for dynamic analysis."
    ),
    "cloud": (
        "Run prowler/trivy against the cloud environment. "
        "Check for public S3 buckets, over-permissive IAM roles, exposed metadata endpoints, "
        "and container image vulnerabilities."
    ),
    "wifi_pentest": (
        "Capture WPA handshakes with airodump-ng or attempt the PMKID attack with hcxdumptool. "
        "Crack captured hashes with aircrack-ng or hashcat. "
        "Check for evil twin or rogue AP opportunities."
    ),
    "forensics": (
        "Extract memory artefacts with volatility. Carve files with foremost/binwalk. "
        "Check for steganography with steghide/stegsolve. "
        "Inspect file metadata with exiftool. Look for hash length extension vulnerabilities."
    ),
    "database": (
        "Connect to the database and enumerate tables, columns, and user privileges. "
        "Look for sensitive credential or config tables. "
        "Attempt privilege escalation via UDFs or misconfigurations."
    ),
    "essential": (
        "Run the core toolkit in sequence: nmap (ports) -> gobuster (content) -> "
        "nikto (web vulns) -> sqlmap (SQLi) -> hydra (brute-force). "
        "Covers basic recon through common exploitation vectors."
    ),
    "vulnerability_intelligence": (
        "Search CVE databases and Exploit-DB for the target stack. "
        "Cross-reference discovered service versions with known vulnerabilities. "
        "Prioritise CVEs with public PoC or Metasploit modules."
    ),
}


_CLASSIFY_PROMPT = """Classify this security task into exactly one category.
Categories: network_recon, web_recon, web_vuln, exploitation, brute_force, osint, binary, cloud, wifi_pentest, forensics
Task: {input}
Category:"""


def _classify_with_llm(user_input: str, llm_client) -> str:
    """Use a single cheap LLM call to classify ambiguous input."""
    prompt = _CLASSIFY_PROMPT.format(input=user_input)
    try:
        response = llm_client.chat(
            [{"role": "user", "content": prompt}],
            stop=["\n"],
        )
        parts = response.lower().split("category:")
        final_resp = parts[1].strip() if len(parts) > 1 else response.lower().strip()
        return final_resp
    except Exception as exc:
        logger.warning("LLM intent classification failed for input %r: %s", user_input, exc)
        return ""


def classify_intent(user_input: str, llm_client=None) -> tuple:
    """Return (category, confidence) using keywords, with optional LLM fallback.

    Confidence values:
        1.0  - clear keyword winner (margin >= 2 over runner-up)
        0.75 - keyword winner but narrow margin
        0.5  - no llm_client available and low/zero keyword signal
    """
    text = user_input.lower()
    scores: Dict[str, int] = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in _INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best, best_score = ranked[0]
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0

    if best_score == 0:
        # No keyword matches at all
        if llm_client:
            category = _classify_with_llm(user_input, llm_client)
            if category in CATEGORIES:
                return (category, 0.75)
        return ("network_recon", 0.5)  # safe default

    margin = best_score - runner_up_score
    if margin >= 2:
        return (best, 1.0)

    # try LLM if available
    if llm_client:
        category = _classify_with_llm(user_input, llm_client)
        if category in list(CATEGORIES.keys()):
            return (category, 0.75)

    return ("network_recon", 0.5)

def get_tools_for_category(category: str) -> List[dict]:
    """Return compact tool schemas for a category, sorted by effectiveness."""
    tools = [
        {
            "name": name,
            "desc": t["desc"],
            "endpoint": t["endpoint"],
            "method": t["method"],
            "params": {
                **{k: "REQUIRED" for k in t["params"]},
                **{k: f"default={v}" for k, v in t["optional"].items()},
            }
        }
        for name, t in TOOLS.items()
        if t["category"] == category
    ]
    # Sort by effectiveness descending
    tools.sort(
        key=lambda x: TOOLS[x["name"]]["effectiveness"],
        reverse=True,
    )
    return tools


def get_tool(name: str) -> Optional[dict]:
    """Return full tool definition by name, or None."""
    return TOOLS.get(name)


def get_all_categories() -> Dict[str, str]:
    """Return category name -> description mapping."""
    return dict(CATEGORIES)


def format_tools_for_prompt(tools: List[dict]) -> str:
    """Format a tool list into a compact string for LLM system prompts."""
    lines = []
    for t in tools:
        params_str = ", ".join(f"{k}={v}" for k, v in t["params"].items())
        lines.append(f"- {t['name']}: {t['desc']} | params: {params_str}")
    # Always include final_answer
    # can be skipped if not using agentic mode in you LLM connection when ran locally.
    lines.append(f"- final_answer: {FINAL_ANSWER_TOOL['desc']} | params: answer=REQUIRED")
    return "\n".join(lines)
