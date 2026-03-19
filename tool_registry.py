"""
Tool Registry with Compact Schemas for HexStrike AI Agent

Categorized tool definitions with minimal schemas.
Only 5-8 tools are loaded per task category to fit small model context windows.
Can be increased or decreased as needed, but focus on the most effective tools for each category.
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions - each entry is intentionally compact so the full category
# fits well under the context window of smaller models when serialized.
# ---------------------------------------------------------------------------

TOOLS: Dict[str, dict] = {
    # ---- Network Recon ----
    "nmap": {
        "desc": "Port scan and service detection",
        "endpoint": "/api/tools/nmap",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"scan_type": "-sCV", "ports": "", "additional_args": "-T4 -Pn"},
        "effectiveness": 0.95,
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
    "nbtscan": {
        "desc": "NetBIOS name scanner",
        "endpoint": "/api/tools/nbtscan",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.75,
    },
    "netexec": {
        "desc": "Network service exploitation (SMB/WinRM/LDAP)",
        "endpoint": "/api/tools/netexec",
        "method": "POST",
        "category": "network_recon",
        "params": {"target": {"required": True}},
        "optional": {"protocol": "smb", "username": "", "password": "", "module": "", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "mysql": {
        "desc": "Query a MySQL database",
        "endpoint": "/api/tools/mysql",
        "method": "POST",
        "category": "network_recon",
        "params": {"host": {"required": True}, "user": {"required": True}, "database": {"required": True}, "query": {"required": True}},
        "optional": {"password": ""},
        "effectiveness": 0.80,
    },
    "postgresql": {
        "desc": "Query a PostgreSQL database",
        "endpoint": "/api/tools/postgresql",
        "method": "POST",
        "category": "network_recon",
        "params": {"host": {"required": True}, "user": {"required": True}, "database": {"required": True}, "query": {"required": True}},
        "optional": {"password": ""},
        "effectiveness": 0.80,
    },
    "sqlite": {
        "desc": "Query a SQLite database file",
        "endpoint": "/api/tools/sqlite",
        "method": "POST",
        "category": "network_recon",
        "params": {"db_path": {"required": True}, "query": {"required": True}},
        "optional": {},
        "effectiveness": 0.75,
    },

    # ---- Web Recon ----
    "gobuster": {
        "desc": "Directory and file brute-forcer",
        "endpoint": "/api/tools/gobuster",
        "method": "POST",
        "category": "web_recon",
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
    "httpx": {
        "desc": "HTTP probing and tech detection",
        "endpoint": "/api/tools/httpx",
        "method": "POST",
        "category": "web_recon",
        "params": {"target": {"required": True}},
        "optional": {"probe": True, "tech_detect": False, "status_code": False, "title": False, "additional_args": ""},
        "effectiveness": 0.85,
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
        "optional": {"additional_args": ""},
        "effectiveness": 0.95,
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
        "category": "web_vuln",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.85,
    },
    "sqlmap": {
        "desc": "Automatic SQL injection detection and exploitation",
        "endpoint": "/api/tools/sqlmap",
        "method": "POST",
        "category": "web_vuln",
        "params": {"url": {"required": True}},
        "optional": {"data": "", "additional_args": ""},
        "effectiveness": 0.90,
    },
    "dalfox": {
        "desc": "XSS vulnerability scanner",
        "endpoint": "/api/tools/dalfox",
        "method": "POST",
        "category": "web_vuln",
        "params": {"url": {"required": True}},
        "optional": {"blind": False, "additional_args": ""},
        "effectiveness": 0.93,
    },
    "xsser": {
        "desc": "Cross-site scripting scanner",
        "endpoint": "/api/tools/xsser",
        "method": "POST",
        "category": "web_vuln",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
    "dotdotpwn": {
        "desc": "Directory traversal scanner",
        "endpoint": "/api/tools/dotdotpwn",
        "method": "POST",
        "category": "web_vuln",
        "params": {"target": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.78,
    },
    "jaeles": {
        "desc": "Web security scanning framework",
        "endpoint": "/api/tools/jaeles",
        "method": "POST",
        "category": "web_vuln",
        "params": {"url": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.92,
    },

    # ---- Exploitation ----
    "metasploit": {
        "desc": "Exploitation framework - run modules with options",
        "endpoint": "/api/tools/metasploit",
        "method": "POST",
        "category": "exploitation",
        "params": {"module": {"required": True}},
        "optional": {"options": {}},
        "effectiveness": 0.90,
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
    "exploit_db": {
        "desc": "Search Exploit-DB for public exploits",
        "endpoint": "/api/tools/exploit_framework/exploit_db",
        "method": "POST",
        "category": "exploitation",
        "params": {"query": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.88,
    },

    # ---- Brute Force ----
    "hydra": {
        "desc": "Network login brute-forcer",
        "endpoint": "/api/tools/hydra",
        "method": "POST",
        "category": "brute_force",
        "params": {"target": {"required": True}, "service": {"required": True}},
        "optional": {"username": "", "username_file": "", "password": "", "password_file": "", "additional_args": ""},
        "effectiveness": 0.80,
    },
    "hashcat": {
        "desc": "GPU-accelerated password cracker",
        "endpoint": "/api/tools/hashcat",
        "method": "POST",
        "category": "brute_force",
        "params": {"hash_file": {"required": True}, "hash_type": {"required": True}},
        "optional": {"attack_mode": "0", "wordlist": "/usr/share/wordlists/rockyou.txt", "mask": "", "additional_args": ""},
        "effectiveness": 0.85,
    },
    "john": {
        "desc": "Password cracker with many formats",
        "endpoint": "/api/tools/john",
        "method": "POST",
        "category": "brute_force",
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

    # ---- OSINT ----
    "whois": {
        "desc": "WHOIS lookup for domains and IPs",
        "endpoint": "/api/tools/whois",
        "method": "POST",
        "category": "osint",
        "params": {"target": {"required": True}},
        "optional": {},
        "effectiveness": 0.80,
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
    "theharvester": {
        "desc": "Passive information gathering from public sources",
        "endpoint": "/api/tools/recon/theharvester",
        "method": "POST",
        "category": "osint",
        "params": {"domain": {"required": True}},
        "optional": {"additional_args": ""},
        "effectiveness": 0.80,
    },
 # ---- WiFi Pentest ----
    "hcxdumptool": {
        "desc": "Clientless PMKID capture and WPA/WPA2 handshake collection via hcxdumptool. Output feeds hashcat -m 22000.",
        "endpoint": "/api/tools/wifi_pentest/hcxdumptool",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {
            "output_file": "pmkid_capture.pcapng",
            "target_bssid": "",
            "duration": 60,
            "additional_args": "",
        },
        "effectiveness": 0.93,
    },
    "eaphammer": {
        "desc": "WPA-Enterprise Evil Twin attack. Harvests MSCHAPV2/GTC credentials from 802.1X clients via rogue AP.",
        "endpoint": "/api/tools/wifi_pentest/eaphammer",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {
            "interface": {"required": True},
            "essid":     {"required": True},
        },
        "optional": {
            "channel":       6,
            "auth_mode":     "wpa-eap",
            "attack_type":   "creds",
            "negotiate":     "gtc-downgrade",
            "cert_path":     "",
            "additional_args": "",
        },
        "effectiveness": 0.87,
    },
    "wifite2": {
        "desc": "Automated WiFi auditing. Orchestrates PMKID, 4-way handshake deauth, and WPS Pixie-Dust attacks.",
        "endpoint": "/api/tools/wifi_pentest/wifite2",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {
            "target_essid":     "",
            "target_bssid":     "",
            "attack_wps":       False,
            "attack_pmkid":     True,
            "attack_handshake": True,
            "wordlist":         "",
            "timeout":          300,
            "additional_args":  "",
        },
        "effectiveness": 0.90,
    },
    "bettercap_wifi": {
        "desc": "Wireless recon and deauth using Bettercap wifi module. Discovers APs, clients, and probe requests.",
        "endpoint": "/api/tools/wifi_pentest/bettercap_wifi",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"interface": {"required": True}},
        "optional": {
            "mode":          "recon",
            "target_bssid":  "",
            "deauth_all":    False,
            "channel_hop":   True,
            "caplet":        "",
            "additional_args": "",
        },
        "effectiveness": 0.88,
    },
    "mdk4": {
        "desc": "802.11 protocol stress testing. Beacon flood, deauth flood, auth DoS for WIDS/WIPS validation.",
        "endpoint": "/api/tools/wifi_pentest/mdk4",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {
            "interface":   {"required": True},
            "attack_mode": {"required": True},
        },
        "optional": {
            "target_bssid":  "",
            "ssid_wordlist": "",
            "burst_rate":    50,
            "additional_args": "",
        },
        "effectiveness": 0.82,
    },
    "aircrack_ng": {
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
    "airmon_ng": {
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
    "airodump_ng": {
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
    "aireplay_ng": {
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
    "airbase_ng": {
        "desc": "Create a rogue/soft access point for Evil Twin or client capture.",
        "endpoint": "/api/tools/wifi_pentest/airbase_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {
            "interface": {"required": True},
            "essid":     {"required": True},
        },
        "optional": {
            "channel":  6,
            "bssid":    "",
            "wpa_mode": "",
        },
        "effectiveness": 0.85,
    },
    "airdecap_ng": {
        "desc": "Decrypt WEP/WPA/WPA2 encrypted pcap capture files.",
        "endpoint": "/api/tools/wifi_pentest/airdecap_ng",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {"capture_file": {"required": True}},
        "optional": {
            "password": "",
            "wep_key":  "",
            "bssid":    "",
            "essid":    "",
        },
        "effectiveness": 0.88,
    },
    "hcxpcapngtool": {
        "desc": "Convert hcxdumptool pcapng captures to hashcat -m 22000 format.",
        "endpoint": "/api/tools/wifi_pentest/hcxpcapngtool",
        "method": "POST",
        "category": "wifi_pentest",
        "params": {
            "input_file":  {"required": True},
            "output_file": {"required": True},
        },
        "optional": {},
        "effectiveness": 0.92,
    },

    # ---- Binary Analysis ----
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
        "category": "binary",
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
}

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
    "network_recon": "Network scanning, port discovery, service enumeration",
    "web_recon": "Web directory brute-forcing, crawling, tech detection",
    "web_vuln": "Web vulnerability scanning (SQLi, XSS, template-based)",
    "exploitation": "Exploit execution, payload generation, module search",
    "brute_force": "Password cracking and login brute-forcing",
    "osint": "Subdomain enumeration, DNS recon, URL harvesting",
    "binary": "Binary analysis, reverse engineering, ROP gadgets",
    "cloud": "Cloud security auditing (AWS, containers, Kubernetes)",
    "wifi_pentest": "Wifi Pentesting Tools"

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
        "scan", "port", "nmap", "host", "network", "service", "smb",
        "enum4linux", "discovery", "arp", "netbios", "smbmap",
    ],
    "web_recon": [
        "directory", "dir", "brute", "fuzz", "gobuster", "ffuf", "crawl",
        "spider", "wordpress", "wpscan", "vhost", "content", "ferox",
    ],
    "web_vuln": [
        "vuln", "vulnerability", "nuclei", "nikto", "sql", "sqli", "xss",
        "injection", "exploit", "dalfox", "traversal",
    ],
    "exploitation": [
        "exploit", "metasploit", "msf", "payload", "msfvenom", "exploit-db",
        "cve", "shell", "reverse", "module",
    ],
    "brute_force": [
        "brute", "crack", "password", "hydra", "hashcat", "login", "credential",
        "hash", "wordlist","john", "medusa", "patator", "ophcrack"
    ],
    "osint": [
        "subdomain", "dns", "osint", "amass", "subfinder", "domain", "recon",
        "url", "fierce", "enumerate", "whois", "bbot", "theharvester", 
        "gau", "waybackurls"
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
}


_CLASSIFY_PROMPT = """Classify this security task into exactly one category.
Categories: network_recon, web_recon, web_vuln, exploitation, brute_force, osint, binary, cloud, wifi_pentest
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
            },
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
