from .ai_assist import *
from .ai_payload import *
from .tools_catalog import *
from .ui_blueprint import *
from .settings import *
from .ctf import *
from .process import *
from .api_audit import *
from .api_fuzz import *
from .api_scan import *
from .binary_analysis import *
from .binary_debug import *
from .bugbounty_workflow import *
from .cloud_audit import *
from .cloud_exploit import *
from .cloud_visual import *
from .container_scan import *
from .credential_harvest import *
from .crypto_attack import *
from .data_processing import *
from .db_query import *
from .dns_enum import *
from .error_handling import *
from .exploit_framework import *
from .file_carving import *
from .gadget_search import *
from .iac_scan import *
from .k8s_scan import *
from .memory_forensics import *
from .metadata_extract import *
from .net_lookup import *
from .net_scan import *
from .ops import *
from .param_discovery import *
from .param_fuzz import *
from .password_cracking import *
from .recon import *
from .recon_bot import *
from .runtime_monitor import *
from .smb_enum import *
from .stego_analysis import *
from .url_filter import *
from .url_recon import *
from .vuln_intel import *
from .vuln_scan import *
from .waf_detect import *
from .web_crawl import *
from .web_framework import *
from .web_fuzz import *
from .web_probe import *
from .web_scan import *
from .wifi_pentest import *
from .active_directory import *
from .osint import *
from .burp_agent import *

def register_blueprints(app):
  """Register all API blueprints with the Flask app."""

  # OPS — System Monitoring & File Ops
  app.register_blueprint(api_system_monitoring_bp)
  app.register_blueprint(api_file_ops_and_payload_gen_bp)
  app.register_blueprint(api_logs_bp)
  app.register_blueprint(api_web_dashboard_bp)
  app.register_blueprint(api_runs_bp)
  app.register_blueprint(api_sessions_bp)
  app.register_blueprint(api_session_notes_bp)
  app.register_blueprint(api_session_findings_bp)
  app.register_blueprint(api_session_reports_bp)

  #OSINT
  app.register_blueprint(api_osint_sherlock_bp)
  app.register_blueprint(api_osint_spiderfoot_bp)
  app.register_blueprint(api_osint_sublist3r_bp)
  app.register_blueprint(api_osint_parsero_bp)

  # Database
  app.register_blueprint(api_database_bp)

  #Active Directory
  app.register_blueprint(api_tools_impacket_bp)
  app.register_blueprint(api_tool_active_directory_ldapdomaindump_bp)

  # OPS — General
  app.register_blueprint(api_visual_bp)
  app.register_blueprint(api_process_management_bp)
  app.register_blueprint(api_process_execute_async_bp)
  app.register_blueprint(api_process_get_task_result_bp)
  app.register_blueprint(api_process_pool_stats_bp)
  app.register_blueprint(api_process_cache_stats_bp)
  app.register_blueprint(api_process_clear_cache_bp)
  app.register_blueprint(api_process_resource_usage_bp)
  app.register_blueprint(api_process_performance_dashboard_bp)
  app.register_blueprint(api_process_terminate_gracefully_bp)
  app.register_blueprint(api_wordlist_store_bp)
  app.register_blueprint(api_ops_python_env_bp)
  app.register_blueprint(api_process_auto_scaling_bp)
  app.register_blueprint(api_process_scale_pool_bp)
  app.register_blueprint(api_process_health_check_bp)

  # Password Cracking
  app.register_blueprint(api_password_cracking_medusa_bp)
  app.register_blueprint(api_password_cracking_patator_bp)
  app.register_blueprint(api_password_cracking_hashid_bp)
  app.register_blueprint(api_password_cracking_ophcrack_bp)
  app.register_blueprint(api_password_cracking_aircrack_ng_bp)
  app.register_blueprint(api_password_cracking_hydra_bp)
  app.register_blueprint(api_password_cracking_john_bp)
  app.register_blueprint(api_password_cracking_hashcat_bp)

  # Reconnaissance
  app.register_blueprint(api_recon_theharvester_bp)
  app.register_blueprint(api_recon_amass_bp)
  app.register_blueprint(api_recon_subfinder_bp)
  app.register_blueprint(api_recon_assetfinder_bp)
  app.register_blueprint(api_recon_shuffledns_bp)
  app.register_blueprint(api_recon_massdns_bp)
  app.register_blueprint(api_recon_autorecon_bp)
  app.register_blueprint(api_recon_bot_bbot_bp)

  # Exploitation
  app.register_blueprint(api_exploit_framework_exploit_db_bp)
  app.register_blueprint(api_exploit_framework_pwninit_bp)
  app.register_blueprint(api_exploit_framework_msfvenom_bp)
  app.register_blueprint(api_exploit_framework_metasploit_bp)
  app.register_blueprint(api_exploit_framework_pwntools_bp)
  app.register_blueprint(api_exploit_framework_commix_bp)

  # Binary Analysis
  app.register_blueprint(api_binary_analysis_autopsy_bp)
  app.register_blueprint(api_binary_analysis_xxd_bp)
  app.register_blueprint(api_binary_analysis_strings_bp)
  app.register_blueprint(api_binary_analysis_objdump_bp)
  app.register_blueprint(api_binary_analysis_ghidra_bp)
  app.register_blueprint(api_binary_analysis_one_gadget_bp)
  app.register_blueprint(api_binary_analysis_libc_database_bp)
  app.register_blueprint(api_binary_analysis_angr_bp)
  app.register_blueprint(api_binary_analysis_ropper_bp)
  app.register_blueprint(api_binary_analysis_binwalk_bp)
  app.register_blueprint(api_binary_analysis_checksec_bp)

  # Binary Debug
  app.register_blueprint(api_binary_debug_gdb_bp)
  app.register_blueprint(api_binary_debug_gdb_peda_bp)
  app.register_blueprint(api_binary_debug_radare2_bp)

  # Gadget Search
  app.register_blueprint(api_gadget_search_ropgadget_bp)

  # Wi-Fi Pentest
  app.register_blueprint(api_wifi_pentest_aircrack_ng_bp)
  app.register_blueprint(api_wifi_pentest_airmon_ng_bp)
  app.register_blueprint(api_wifi_pentest_airodump_ng_bp)
  app.register_blueprint(api_wifi_pentest_aireplay_ng_bp)
  app.register_blueprint(api_wifi_pentest_airbase_ng_bp)
  app.register_blueprint(api_wifi_pentest_airdecap_ng_bp)
  app.register_blueprint(api_wifi_pentest_hcxpcapngtool_bp)
  app.register_blueprint(api_wifi_pentest_hcxdumptool_bp)
  app.register_blueprint(api_wifi_pentest_eaphammer_bp)
  app.register_blueprint(api_wifi_pentest_wifite2_bp)
  app.register_blueprint(api_wifi_pentest_bettercap_wifi_bp)
  app.register_blueprint(api_wifi_pentest_mdk4_bp)

  # Web Fuzzing
  app.register_blueprint(api_web_fuzz_feroxbuster_bp)
  app.register_blueprint(api_web_fuzz_dotdotpwn_bp)
  app.register_blueprint(api_web_fuzz_wfuzz_bp)
  app.register_blueprint(api_web_fuzz_dirsearch_bp)
  app.register_blueprint(api_web_fuzz_gobuster_bp)
  app.register_blueprint(api_web_fuzz_dirb_bp)
  app.register_blueprint(api_web_fuzz_ffuf_bp)

  # Web Scanning
  app.register_blueprint(api_web_scan_xsser_bp)
  app.register_blueprint(api_web_scan_jaeles_bp)
  app.register_blueprint(api_web_scan_dalfox_bp)
  app.register_blueprint(api_web_scan_burpsuite_bp)
  app.register_blueprint(api_web_scan_zap_bp)
  app.register_blueprint(api_web_scan_nikto_bp)
  app.register_blueprint(api_web_scan_sqlmap_bp)
  app.register_blueprint(api_web_scan_wpscan_bp)
  app.register_blueprint(api_web_scan_joomscan_bp)
  app.register_blueprint(api_web_scan_whatweb_bp)
  app.register_blueprint(api_web_scan_interactsh_bp)

  # Web Crawl
  app.register_blueprint(api_web_crawl_katana_bp)
  app.register_blueprint(api_web_crawl_hakrawler_bp)
  app.register_blueprint(api_web_crawl_gospider_bp)

  # Web Probe
  app.register_blueprint(api_web_probe_httpx_bp)
  app.register_blueprint(api_web_probe_testssl_bp)

  # Web Framework
  app.register_blueprint(api_web_framework_http_framework_bp)
  app.register_blueprint(api_web_framework_browser_agent_bp)

  # URL Recon
  app.register_blueprint(api_url_recon_gau_bp)
  app.register_blueprint(api_url_recon_waybackurls_bp)
  app.register_blueprint(api_web_probe_waymore_bp)

  # URL Filter
  app.register_blueprint(api_url_filter_uro_bp)

  # Parameter Discovery
  app.register_blueprint(api_param_discovery_arjun_bp)
  app.register_blueprint(api_param_discovery_paramspider_bp)
  app.register_blueprint(api_param_discovery_x8_bp)

  # Parameter Fuzzing
  app.register_blueprint(api_param_fuzz_qsreplace_bp)

  # WAF Detection
  app.register_blueprint(api_waf_detect_wafw00f_bp)

  # DNS Enumeration
  app.register_blueprint(api_dns_enum_fierce_bp)
  app.register_blueprint(api_dns_enum_dnsenum_bp)

  # AI Payload
  app.register_blueprint(api_ai_payload_generate_payload_bp)
  app.register_blueprint(api_ai_payload_test_payload_bp)

  # API Fuzzing
  app.register_blueprint(api_api_fuzz_api_fuzzer_bp)
  app.register_blueprint(api_api_fuzz_schemathesis_bp)

  # API Scanning
  app.register_blueprint(api_api_scan_graphql_scanner_bp)
  app.register_blueprint(api_api_scan_jwt_analyzer_bp)
  app.register_blueprint(api_api_scan_api_schema_analyzer_bp)

  # SMB Enumeration
  app.register_blueprint(api_smb_enum_nbtscan_bp)
  app.register_blueprint(api_smb_enum_enum4linux_bp)
  app.register_blueprint(api_smb_enum_netexec_bp)
  app.register_blueprint(api_smb_enum_smbmap_bp)
  app.register_blueprint(api_smb_enum_enum4linux_ng_bp)
  app.register_blueprint(api_smb_enum_rpcclient_bp)

  # Network Scanning
  app.register_blueprint(api_net_scan_arp_scan_bp)
  app.register_blueprint(api_net_scan_nmap_bp)
  app.register_blueprint(api_net_scan_rustscan_bp)
  app.register_blueprint(api_net_scan_masscan_bp)
  app.register_blueprint(api_net_scan_nmap_advanced_bp)

  # Network Lookup
  app.register_blueprint(api_net_lookup_whois_bp)
  app.register_blueprint(api_net_lookup_http_headers_bp)
  app.register_blueprint(api_net_lookup_dig_bp)

  # Credential Harvesting
  app.register_blueprint(api_credential_harvest_responder_bp)

  # Memory Forensics
  app.register_blueprint(api_memory_forensics_volatility_bp)
  app.register_blueprint(api_memory_forensics_volatility3_bp)

  # File Carving
  app.register_blueprint(api_file_carving_foremost_bp)

  # Steganography Analysis
  app.register_blueprint(api_stego_analysis_steghide_bp)

  # Metadata Extraction
  app.register_blueprint(api_metadata_extract_exiftool_bp)

  # Crypto Attack
  app.register_blueprint(api_crypto_attack_hashpump_bp)

  # Data Processing
  app.register_blueprint(api_data_processing_anew_bp)
  app.register_blueprint(api_data_processing_hurl_bp)

  # Container Scanning
  app.register_blueprint(api_container_scan_trivy_bp)
  app.register_blueprint(api_container_scan_docker_bench_bp)
  app.register_blueprint(api_container_scan_clair_bp)

  # Cloud Audit
  app.register_blueprint(api_cloud_audit_scout_suite_bp)
  app.register_blueprint(api_cloud_audit_prowler_bp)

  # Cloud Exploitation
  app.register_blueprint(api_cloud_exploit_cloudmapper_bp)
  app.register_blueprint(api_cloud_exploit_pacu_bp)

  # Kubernetes Scanning
  app.register_blueprint(api_k8s_scan_kube_hunter_bp)
  app.register_blueprint(api_k8s_scan_kube_bench_bp)

  # Runtime Monitoring
  app.register_blueprint(api_runtime_monitor_falco_bp)

  # IaC Scanning
  app.register_blueprint(api_iac_scan_checkov_bp)
  app.register_blueprint(api_iac_scan_terrascan_bp)

  # Vulnerability Scanning
  app.register_blueprint(api_vuln_scan_nuclei_bp)

  # Vulnerability Intelligence
  app.register_blueprint(api_vulnerability_intelligence_bp)
  app.register_blueprint(api_vuln_intel_cve_monitor_bp)
  app.register_blueprint(api_vuln_intel_exploit_generate_bp)
  app.register_blueprint(api_vuln_intel_attack_chains_bp)
  app.register_blueprint(api_vuln_intel_threat_feeds_bp)
  app.register_blueprint(api_vuln_intel_zero_day_research_bp)
  app.register_blueprint(api_vuln_intel_vulnx_bp)

  # Bug Bounty Workflow
  app.register_blueprint(api_bugbounty_workflow_bug_bounty_recon_bp)

  # AI Assist
  app.register_blueprint(api_chat_bp)
  app.register_blueprint(api_ai_assist_advanced_payload_generation_bp)
  app.register_blueprint(api_ai_assist_llm_agent_bp)
  app.register_blueprint(api_ai_assist_ai_recon_session_bp)
  app.register_blueprint(api_ai_assist_ai_profiling_session_bp)
  app.register_blueprint(api_ai_assist_ai_vuln_session_bp)
  app.register_blueprint(api_ai_assist_ai_osint_session_bp)
  app.register_blueprint(api_ai_assist_ai_followup_session_bp)

  # Tools Catalog
  app.register_blueprint(api_tools_catalog_bp)

  # Settings
  app.register_blueprint(api_settings_bp)

  # Web UI
  app.register_blueprint(api_ui_bp)

  # Plugins
  app.register_blueprint(api_plugins_bp)

  # CTF
  app.register_blueprint(api_ctf_create_challenge_workflow_bp)
  app.register_blueprint(api_ctf_auto_solve_challenge_bp)
  app.register_blueprint(api_ctf_team_strategy_bp)
  app.register_blueprint(api_ctf_suggest_tools_bp)
  app.register_blueprint(api_ctf_cryptography_solver_bp)
  app.register_blueprint(api_ctf_forensics_analyzer_bp)
  app.register_blueprint(api_ctf_binary_analyzer_bp)

  # Burp Agent Loop
  app.register_blueprint(api_burp_agent_bp)

  # Intelligent Error Handling
  app.register_blueprint(api_error_handling_statistics_bp)
  app.register_blueprint(api_error_handling_test_recovery_bp)
  app.register_blueprint(api_error_handling_fallback_chains_bp)
  app.register_blueprint(api_error_handling_execute_with_recovery_bp)
  app.register_blueprint(api_error_handling_classify_error_bp)
  app.register_blueprint(api_error_handling_parameter_adjustments_bp)
  app.register_blueprint(api_error_handling_alternative_tools_bp)
