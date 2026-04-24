from mcp_core.cli_colors import CliColors
from mcp_tools import *

def resolve_profile_dependencies(profiles):
    resolved = set()
    to_process = list(profiles)
    while to_process:
        profile = to_process.pop()
        if profile not in resolved:
            resolved.add(profile)
            deps = PROFILE_DEPENDENCIES.get(profile, [])
            to_process.extend([dep for dep in deps if dep not in resolved])
    return list(resolved)

TOOL_PROFILES = {

    # All Profiles
    ## `compact` (essential gateway tools only)
    ## `full` (all tools registered)

    #Compact mode 
    #Only essential tools for task classification and tool execution, without all the individual tool functions. Allows smaller LLM clients to use the MCP server without running into token limits due to too many registered tools.
    "compact": [
        lambda mcp, client, logger: register_gateway_tools(mcp, client),
    ],

    "active_directory": [
        lambda mcp, client, logger: register_impacket(mcp, client, logger, CliColors),
        lambda mcp, client, logger: register_ldapdomaindump_tool(mcp, client, logger),
    ],

    "api_audit": [
        lambda mcp, client, logger: register_comprehensive_api_audit_tool(mcp, client, logger), #Uses api_fuzz and api_scan tools internally, so they are needed for this profile as well.
    ],

    #OSINT tools for information gathering and reconnaissance e.g. Sherlock)
    "osint": [
        lambda mcp, client, logger: register_osint_sherlock_tool(mcp, client, logger),
        lambda mcp, client, logger: register_osint_spiderfoot_tool(mcp, client, logger),
        lambda mcp, client, logger: register_osint_sublist3r_tool(mcp, client, logger),
        lambda mcp, client, logger: register_osint_parsero_tool(mcp, client, logger),
        lambda mcp, client, logger: register_osint_joomscan_tool(mcp, client, logger),
    ],

    #Tools for steganography analysis (e.g., Steghide).
    "stego_analysis": [
        lambda mcp, client, logger: register_steghide_tool(mcp, client, logger),
    ],

    #Tools for metadata extraction (e.g., ExifTool).
    "metadata_extract": [
        lambda mcp, client, logger: register_exiftool_tool(mcp, client, logger),
    ],

    #Tools for cryptographic attacks (e.g., HashPump).
    "crypto_attack": [
        lambda mcp, client, logger: register_hashpump_tool(mcp, client, logger),
    ],

    #Tools for file carving and data recovery (e.g., Foremost).
    "file_carving": [
        lambda mcp, client, logger: register_foremost_tool(mcp, client, logger),
    ],

    #Tools for API fuzzing and endpoint discovery (e.g., API Fuzzer with intelligent parameter discovery).
    "api_fuzz": [
        lambda mcp, client, logger: register_api_fuzzer_tool(mcp, client, logger),
        lambda mcp, client, logger: register_api_fuzz_schemathesis_tool(mcp, client, logger),
    ],

    #Tools for API scanning (e.g., GraphQL Scanner with enhanced security testing).
    "api_scan": [
        lambda mcp, client, logger: register_graphql_scanner_tool(mcp, client, logger),
        lambda mcp, client, logger: register_jwt_analyzer_tool(mcp, client, logger),
        lambda mcp, client, logger: register_api_schema_analyzer(mcp, client, logger),
    ],

    #Tools for binary debugging
    "binary_debug": [
        lambda mcp, client, logger: register_gdb_tools(mcp, client, logger),
        lambda mcp, client, logger: register_radare2_tools(mcp, client, logger),
    ],

    #Tools for ROP gadget searching and analysis (e.g., ROPgadget, OneGadget, Ropper).
    "gadget_search": [
        lambda mcp, client, logger: register_ropgadget_tool(mcp, client, logger),
        lambda mcp, client, logger: register_one_gadget_tool(mcp, client, logger),
        lambda mcp, client, logger: register_ropper_tool(mcp, client, logger),
    ],

    #Tools for binary analysis (e.g., Binwalk, Checksec, xxd, Strings, Objdump, Libc, Angr, Autopsy).
    "binary_analysis": [
        lambda mcp, client, logger: register_binwalk_tool(mcp, client, logger),
        lambda mcp, client, logger: register_checksec_tool(mcp, client, logger),
        lambda mcp, client, logger: register_xxd_tool(mcp, client, logger),
        lambda mcp, client, logger: register_strings_tool(mcp, client, logger),
        lambda mcp, client, logger: register_objdump_tool(mcp, client, logger),
        lambda mcp, client, logger: register_ghidra_tools(mcp, client, logger),
        lambda mcp, client, logger: register_libc_tools(mcp, client, logger),
        lambda mcp, client, logger: register_angr_tools(mcp, client, logger),
        lambda mcp, client, logger: register_autopsy_tools(mcp, client, logger),
    ],

    #Tools for credential harvesting and network poisoning (e.g., Responder).
    "credential_harvest": [
        lambda mcp, client, logger: register_responder_tool(mcp, client, logger),
    ],

    #Tools for memory forensics analysis (e.g., Volatility, Volatility3).
    "memory_forensics": [
        lambda mcp, client, logger: register_volatility_tool(mcp, client, logger),
        lambda mcp, client, logger: register_volatility3(mcp, client, logger),
    ],

    #Tools for brute-forcing and cracking password hashes (e.g., Hydra, John, Hashcat, Medusa, Patator, HashId, Ophcrack, Aircrack-ng).
    "password_cracking": [
        lambda mcp, client, logger: register_hydra_tool(mcp, client, logger),
        lambda mcp, client, logger: register_john_tool(mcp, client, logger),
        lambda mcp, client, logger: register_hashcat_tool(mcp, client, logger),
        lambda mcp, client, logger: register_medusa_tool(mcp, client, logger),
        lambda mcp, client, logger: register_patator_tool(mcp, client, logger),
        lambda mcp, client, logger: register_hashid_tool(mcp, client, logger),
        lambda mcp, client, logger: register_ophcrack_tool(mcp, client, logger),
    ],

       # WiFi penetration testing and wireless security assessment
    "wifi_pentest": [
        lambda mcp, client, logger: register_aircrack_ng_tools(mcp, client, logger),
        lambda mcp, client, logger: register_airmon_ng_tools(mcp, client, logger),
        lambda mcp, client, logger: register_airodump_ng_tools(mcp, client, logger),
        lambda mcp, client, logger: register_aireplay_ng_tools(mcp, client, logger),
        lambda mcp, client, logger: register_airbase_ng_tools(mcp, client, logger),
        lambda mcp, client, logger: register_airdecap_ng_tools(mcp, client, logger),
        lambda mcp, client, logger: register_hcxpcapngtool_tools(mcp, client, logger),
        lambda mcp, client, logger: register_hcxdumptool_tools(mcp, client, logger),
        lambda mcp, client, logger: register_eaphammer_tools(mcp, client, logger),
        lambda mcp, client, logger: register_wifite2_tools(mcp, client, logger),
        lambda mcp, client, logger: register_bettercap_wifi_tools(mcp, client, logger),
        lambda mcp, client, logger: register_mdk4_tools(mcp, client, logger),
    ],

    #Tools for SMB and network share enumeration (e.g., Enum4linux, NetExec, SMBMap, NBTSCan, RPCClient).
    "smb_enum": [
        lambda mcp, client, logger: register_enum4linux_tool(mcp, client, logger),
        lambda mcp, client, logger: register_netexec_tool(mcp, client, logger),
        lambda mcp, client, logger: register_smbmap_tool(mcp, client, logger),
        lambda mcp, client, logger: register_nbtscan_tool(mcp, client, logger),
        lambda mcp, client, logger: register_rpcclient_tool(mcp, client, logger),
    ],

    #Tools for reconnaissance and subdomain discovery (e.g., Amass, Subfinder, AutoRecon, TheHarvester).
    "recon": [
        lambda mcp, client, logger: register_amass_tool(mcp, client, logger),
        lambda mcp, client, logger: register_subfinder_tool(mcp, client, logger),
        lambda mcp, client, logger: register_assetfinder_tool(mcp, client, logger),
        lambda mcp, client, logger: register_shuffledns_tool(mcp, client, logger),
        lambda mcp, client, logger: register_massdns_tool(mcp, client, logger),
        lambda mcp, client, logger: register_autorecon_tool(mcp, client, logger),
        lambda mcp, client, logger: register_theharvester_tool(mcp, client, logger),
    ],

    #Tools for network scanning and enumeration (e.g., Nmap, ARP-Scan, Masscan, Rustscan).
    "net_scan": [
        lambda mcp, client, logger: register_nmap(mcp, client, logger, CliColors),
        lambda mcp, client, logger: register_arp_scan_tool(mcp, client, logger),
        lambda mcp, client, logger: register_masscan_tool(mcp, client, logger),
        lambda mcp, client, logger: register_rustscan_tool(mcp, client, logger),
    ],

    #Tools for network information gathering and lookups (e.g., WHOIS).
    "net_lookup": [
        lambda mcp, client, logger: register_whois(mcp, client, logger),
        lambda mcp, client, logger: register_http_headers(mcp, client, logger),
        lambda mcp, client, logger: register_dig(mcp, client, logger),
    ],

    #Tools for reconnaissance and enumeration (e.g., BBot).
    "recon_bot": [
        lambda mcp, client, logger: register_bbot_tools(mcp, client),
    ],

    #Tools for web content discovery and fuzzing (e.g., Dirb, FFuf, Dirsearch, Gobuster, Feroxbuster, DotDotPwn, Wfuzz).
    "web_fuzz": [
        lambda mcp, client, logger: register_dirb_tool(mcp, client, logger),
        lambda mcp, client, logger: register_ffuf_tool(mcp, client, logger),
        lambda mcp, client, logger: register_dirsearch_tools(mcp, client, logger),
        lambda mcp, client, logger: register_gobuster(mcp, client, logger, CliColors),
        lambda mcp, client, logger: register_feroxbuster_tool(mcp, client, logger),
        lambda mcp, client, logger: register_dotdotpwn_tool(mcp, client, logger),
        lambda mcp, client, logger: register_wfuzz_tool(mcp, client, logger),
    ],

    #Tools for web crawling and spidering (e.g., Katana, Hakrawler).
    "web_crawl": [
        lambda mcp, client, logger: register_katana_tool(mcp, client, logger),
        lambda mcp, client, logger: register_hakrawler_tools(mcp, client, logger),
        lambda mcp, client, logger: register_gospider_tool(mcp, client, logger),
    ],

    #Tools for web vulnerability scanning and assessment (e.g., Nikto, WPScan, SQLMap, Jaeles, Dalfox, ZAP, Burp Suite, XSSer).
    "web_scan": [
        lambda mcp, client, logger: register_nikto_tool(mcp, client, logger),
        lambda mcp, client, logger: register_sqlmap_tool(mcp, client, logger),
        lambda mcp, client, logger: register_wpscan_tool(mcp, client, logger),
        lambda mcp, client, logger: register_jaeles_tool(mcp, client, logger),
        lambda mcp, client, logger: register_dalfox_tool(mcp, client, logger),
        lambda mcp, client, logger: register_burpsuite_tool(mcp, client, logger, CliColors),
        lambda mcp, client, logger: register_zap_tool(mcp, client, logger),
        lambda mcp, client, logger: register_xsser_tool(mcp, client, logger),
        lambda mcp, client, logger: register_web_scan_interactsh_tool(mcp, client, logger),
    ],

    "fingerprint": [
        lambda mcp, client, logger: register_whatweb_tool(mcp, client, logger),
    ],

    #Tools for web probing and technology detection (e.g., httpx).
    "web_probe": [
        lambda mcp, client, logger: register_httpx_tool(mcp, client, logger),
        lambda mcp, client, logger: register_testssl_tool(mcp, client, logger),
    ],

    #Tools for vulnerability scanning and assessment (e.g., Nuclei).
    "vuln_scan": [
        lambda mcp, client, logger: register_nuclei(mcp, client, logger, CliColors),
    ],

    #Tools for automated exploitation and attack frameworks (e.g., Metasploit, MSFVenom, Pwninit, Pwntools, exploit-db).
    "exploit_framework": [
        lambda mcp, client, logger: register_metasploit_tool(mcp, client, logger),
        lambda mcp, client, logger: register_msfvenom(mcp, client, logger),
        lambda mcp, client, logger: register_pwntools(mcp, client, logger),
        lambda mcp, client, logger: register_pwninit_tool(mcp, client, logger),
        lambda mcp, client, logger: register_exploit_db_tool(mcp, client, logger), #aka. exploit-db
    ],

    #Tools for URL discovery and reconnaissance (e.g., Gau, Waybackurls, Waymore).
    "url_recon": [
        lambda mcp, client, logger: register_gau_tool(mcp, client, logger),
        lambda mcp, client, logger: register_waybackurls_tool(mcp, client, logger),
        lambda mcp, client, logger: register_waymore_tool(mcp, client, logger),
    ],

    #Tools for parameter discovery and fuzzing (e.g., Arju0n, ParamSpider, x8).
    "param_discovery": [
        lambda mcp, client, logger: register_arjun_tool(mcp, client, logger),
        lambda mcp, client, logger: register_paramspider_tool(mcp, client, logger),
        lambda mcp, client, logger: register_x8_tool(mcp, client, logger),
    ],

    #Tools for query string parameter replacement (e.g., qsreplace).
    "param_fuzz": [
        lambda mcp, client, logger: register_qsreplace_tool(mcp, client, logger),
    ],

    #Tools for data processing and unique line filtering (e.g., anew).
    "data_processing": [
        lambda mcp, client, logger: register_anew_tool(mcp, client, logger),
        lambda mcp, client, logger: register_hurl_tool(mcp, client, logger),
    ],

    #Tools for URL filtering and duplicate removal (e.g., uro).
    "url_filter": [
        lambda mcp, client, logger: register_uro_tool(mcp, client, logger),
    ],

    #Tools for web application security testing frameworks (e.g., HTTP Framework, Browser Agent).
    "web_framework": [
        lambda mcp, client, logger: register_http_framework_tool(mcp, client, logger, CliColors),
        lambda mcp, client, logger: register_browser_agent_tool(mcp, client, logger, CliColors),
    ],

    #Tools for WAF detection and fingerprinting (e.g., wafw00f).
    "waf_detect": [
        lambda mcp, client, logger: register_wafw00f_tool(mcp, client, logger),    
    ],

    #Tools for DNS enumeration and subdomain takeover detection (e.g., Fierce, DNSenum).
    "dns_enum": [
        lambda mcp, client, logger: register_fierce_tool(mcp, client, logger),
        lambda mcp, client, logger: register_dnsenum_tool(mcp, client, logger),
    ],
    
    #Tools for error handling and statistics collection to improve reliability and debugging.
    "error_handling": [
        lambda mcp, client, logger: register_error_handling_statistics_tool(mcp, client, logger, CliColors),
        lambda mcp, client, logger: register_test_error_recovery_tool(mcp, client, logger, CliColors),
    ],

    #Tools for cloud assessment and auditing (e.g., Prowler, Scout Suite).
    "cloud_audit": [
        lambda mcp, client, logger: register_prowler_tool(mcp, client, logger),
        lambda mcp, client, logger: register_scout_suite_tool(mcp, client, logger),
    ],

    #Tools for cloud infrastructure visualization and mapping (e.g., CloudMapper).
    "cloud_visual": [
        lambda mcp, client, logger: register_cloudmapper_tool(mcp, client, logger),
    ],

    #Tools for cloud exploitation and attack simulation (e.g., Pacu).
    "cloud_exploit": [
        lambda mcp, client, logger: register_pacu_tool(mcp, client, logger),
    ],

    #Tools for Kubernetes scanning and penetration testing (e.g., kube-hunter, kube-bench).
    "k8s_scan": [
        lambda mcp, client, logger: register_kube_hunter_tool(mcp, client, logger),
        lambda mcp, client, logger: register_kube_bench_tool(mcp, client, logger),
    ],

    #Tools for infrastructure as code security scanning (e.g., Checkov, Terrascan).
    "iac_scan": [
        lambda mcp, client, logger: register_checkov_tool(mcp, client, logger),
        lambda mcp, client, logger: register_terrascan_tool(mcp, client, logger),
    ],

    #Tools for container scanning and vulnerability assessment (e.g., Trivy, Docker Bench, Clair).
    "container_scan": [
        lambda mcp, client, logger: register_trivy_tool(mcp, client, logger),
        lambda mcp, client, logger: register_docker_bench_tool(mcp, client, logger),
        lambda mcp, client, logger: register_clair_vulnerability_tool(mcp, client, logger),
    ],

    #Tools for runtime monitoring and anomaly detection (e.g., Falco).
    "runtime_monitor": [
        lambda mcp, client, logger: register_falco_runtime_monitoring_tool(mcp, client, logger),
    ],

    #Tools for database querying and interaction (e.g., SQLite, MySQL, PostgreSQL).
    "db_query": [
        lambda mcp, client, logger: register_mysql_tools(mcp, client, logger),
        lambda mcp, client, logger: register_sqlite_tools(mcp, client, logger),
        #lambda mcp, client, logger: register_postgresql_tools(mcp, client, logger),
    ],

    #Tools for Python environment interaction and code execution
    "python_env": [
        lambda mcp, client, logger: register_python_env_tools(mcp, client, logger),
    ],

    #Tools for file operations and AI-powered payload generation
    "file_payload": [
        lambda mcp, client, logger: register_file_ops_and_payload_gen_tools(mcp, client, logger),
    ],

    #Tools for wordlist management
    "wordlist": [
        lambda mcp, client, logger: register_wordlist_tools(mcp, client),
    ],

    #Tools for bug bounty workflows and recon automation
    "bug_bounty": [
        lambda mcp, client, logger: register_bug_bounty_recon_tools(mcp, client, logger),
    ],

    #Tools for AI-powered payload generation and testing
    "ai_payload": [
        lambda mcp, client, logger: register_ai_payload_generation_tools(mcp, client, logger),
    ],

    #Tools for intelligent decision making and tool selection based on task context and goals
    "ai_assist": [
        lambda mcp, client, logger: register_intelligent_decision_engine_tools(mcp, client, logger, CliColors),
        lambda mcp, client, logger: register_llm_agent_tools(mcp, client, logger, CliColors),
    ],

    #Tools for vulnerability intelligence gathering and analysis
    "vuln_intel": [
        lambda mcp, client, logger: register_vulnerability_intelligence_tools(mcp, client, logger),
        lambda mcp, client, logger: register_vulnx_tool(mcp, client, logger),
    ],

    #Tools for visual output and reporting
    "visual": [
        lambda mcp, client, logger: register_visual_output_tools(mcp, client, logger),
    ],

    #Tools for system monitoring
    "monitoring": [
        lambda mcp, client, logger: register_system_monitoring_tools(mcp, client, logger),
        lambda mcp, client, logger: register_session_handover_tools(mcp, client, logger),
    ],

    #Tools for process management
    "process_management": [
        lambda mcp, client, logger: register_process_management_tools(mcp, client, logger),
    ],
}

# Profile dependencies
PROFILE_DEPENDENCIES = {
    "api_audit": ["api_fuzz", "api_scan"],
}

# Default profile for easy loading of tool categories
DEFAULT_PROFILE = [
    "credential_harvest",
    "memory_forensics",
    "net_scan",
    "net_lookup",
    "dns_enum",
    "smb_enum",
    "recon",
    "web_probe",
    "web_crawl",
    "web_fuzz",
    "web_scan",
    "vuln_scan",
    "exploit_framework",
    "password_cracking",
    "param_discovery",
    "url_recon",
    "data_processing",
    "error_handling",
    "wifi_pentest",
    "api_audit",

    # System tools"
    "monitoring",
    "process_management",
    "visual",
    "auto_install"
]

# Full profile includes all available tool categories
FULL_PROFILE = list(TOOL_PROFILES.keys())
