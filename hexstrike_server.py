#!/usr/bin/env python3
"""
HexStrike AI - Advanced Penetration Testing Framework Server

Enhanced with AI-Powered Intelligence & Automation
🚀 Bug Bounty | CTF | Red Team | Security Research

Framework: FastMCP integration for AI agent communication
"""

import argparse
import logging
import os
from typing import Dict, Any, Optional
from flask import Flask, request, abort
import server_core.config_core as config_core
from server_core import *
from server_api import *

# ============================================================================
# LOGGING CONFIGURATION (MUST BE FIRST)
# ============================================================================

from server_core.setup_logging import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

# Flask app configuration
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# API Configuration
API_PORT = int(os.environ.get('HEXSTRIKE_PORT', 8888))
API_HOST = os.environ.get('HEXSTRIKE_HOST', '127.0.0.1')  # e.g. export HEXSTRIKE_HOST=0.0.0.0
API_TOKEN = os.environ.get("HEXSTRIKE_API_TOKEN", None)  # e.g. export API_TOKEN=secret-token

#Wordlists
ROCKYOU_PATH = config_core.get_word_list_path("rockyou")
COMMON_DIRB_PATH = config_core.get_word_list_path("common_dirb")
COMMON_DIRSEARCH_PATH = config_core.get_word_list_path("common_dirsearch")

session_store = SessionStore()
wordlist_store = WordlistStore()

# Global decision engine instance
decision_engine = IntelligentDecisionEngine()

# Global error handler and degradation manager instances
error_handler = IntelligentErrorHandler()
degradation_manager = GracefulDegradation()

# Global bug bounty workflow manager
bugbounty_manager = BugBountyWorkflowManager()
fileupload_framework = FileUploadTestingFramework()

# Global instances
tech_detector = TechnologyDetector()
rate_limiter = RateLimitDetector()
failure_recovery = FailureRecoverySystem()
performance_monitor = PerformanceMonitor()
parameter_optimizer = ParameterOptimizer()
enhanced_process_manager = EnhancedProcessManager()

# Global CTF framework instances
ctf_manager = CTFWorkflowManager()
ctf_tools = CTFToolManager()
ctf_automator = CTFChallengeAutomator()
ctf_coordinator = CTFTeamCoordinator()

# Configuration (using existing API_PORT from top of file)
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes", "y")
COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # 5 minutes default timeout
CACHE_SIZE = config_core.get("CACHE_SIZE", 1000)
CACHE_TTL = config_core.get("CACHE_TTL", 3600)  # 1 hour default TTL

# Global cache instance
cache = HexStrikeCache()

# Global telemetry collector — reuse the instance from enhanced_command_executor
from server_core.enhanced_command_executor import telemetry

# Global intelligence managers
cve_intelligence = CVEIntelligenceManager()
exploit_generator = AIExploitGenerator()
vulnerability_correlator = VulnerabilityCorrelator()

def execute_command(command: str, use_cache: bool = True, cache=cache, timeout: int = COMMAND_TIMEOUT) -> Dict[str, Any]:
    """Server-level execute_command wrapper that passes the global cache instance."""
    return _execute_command(command, use_cache=use_cache, cache=cache, timeout=timeout)

def execute_command_with_recovery(
  tool_name: str,
  command: str,
  parameters: Optional[Dict[str, Any]] = None,
  use_cache: bool = True,
  max_attempts: int = 3
) -> Dict[str, Any]:
  return _execute_command_with_recovery(
    tool_name=tool_name,
    command=command,
    parameters=parameters,
    use_cache=use_cache,
    max_attempts=max_attempts,
    execute_command_fn=execute_command,
    error_handler=error_handler,
    degradation_manager=degradation_manager,
    rebuild_command_with_params_fn= _rebuild_command_with_params,
    determine_operation_type_fn= _determine_operation_type,
    recovery_action_enum=RecoveryAction,
    logger=logger,
  )

@app.before_request
def optional_bearer_auth():
    # If no token is configured, allow all requests
    if not API_TOKEN:
        return

    auth_header = request.headers.get("Authorization", "")
    prefix = "Bearer "

    if not auth_header.startswith(prefix):
        abort(401, description="Unexpected authorization header format")

    token = auth_header[len(prefix):]
    if token != API_TOKEN:
        abort(401, description="Unauthorized!")
        
# !NEW BLUEPRINTS GOES BELOW HERE IN FITTING CATEGORIES! #

# ============================================================================
# OPS — SYSTEM MONITORING & FILE OPS BLUEPRINTS
# ============================================================================
app.register_blueprint(api_system_monitoring_bp)
app.register_blueprint(api_file_ops_and_payload_gen_bp)

# ============================================================================
# DATABASE INTERACTION API ENDPOINTS
# ============================================================================
app.register_blueprint(api_database_bp)

# ============================================================================
# OPS API ENDPOINTS
# ============================================================================
app.register_blueprint(api_visual_bp)
app.register_blueprint(api_auto_tool_bp)
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

# ============================================================================
# PASSWORD CRACKING API ENDPOINTS
# ============================================================================
app.register_blueprint(api_password_cracking_medusa_bp)
app.register_blueprint(api_password_cracking_patator_bp)
app.register_blueprint(api_password_cracking_hashid_bp)
app.register_blueprint(api_password_cracking_ophcrack_bp)
app.register_blueprint(api_password_cracking_aircrack_ng_bp)

# ============================================================================
# RECONNAISSANCE API ENDPOINTS
# ============================================================================
app.register_blueprint(api_recon_theharvester_bp)

# ============================================================================
# EXPLOITATION API ENDPOINTS
# ============================================================================
app.register_blueprint(api_exploit_framework_exploit_db_bp)

# ============================================================================
# BINARY ANALYSIS API ENDPOINTS
# ============================================================================
app.register_blueprint(api_binary_analysis_autopsy_bp)
app.register_blueprint(api_binary_analysis_xxd_bp)
app.register_blueprint(api_binary_analysis_strings_bp)
app.register_blueprint(api_binary_analysis_objdump_bp)
app.register_blueprint(api_binary_analysis_ghidra_bp)
app.register_blueprint(api_binary_analysis_one_gadget_bp)
app.register_blueprint(api_binary_analysis_libc_database_bp)
app.register_blueprint(api_binary_analysis_angr_bp)
app.register_blueprint(api_binary_analysis_ropper_bp)

# ============================================================================
# WIFI PENTEST API ENDPOINTS
# ============================================================================
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

# ============================================================================
# EXPLOIT FRAMEWORK API ENDPOINTS
# ============================================================================
app.register_blueprint(api_exploit_framework_pwninit_bp)

# ============================================================================
# WEB FUZZ API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_fuzz_feroxbuster_bp)
app.register_blueprint(api_web_fuzz_dotdotpwn_bp)
app.register_blueprint(api_web_fuzz_wfuzz_bp)
app.register_blueprint(api_web_fuzz_dirsearch_bp)

# ============================================================================
# WEB SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_scan_xsser_bp)

# ============================================================================
# WEB CRAWL API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_crawl_katana_bp)

# ============================================================================
# URL RECON API ENDPOINTS
# ============================================================================
app.register_blueprint(api_url_recon_gau_bp)
app.register_blueprint(api_url_recon_waybackurls_bp)

# ============================================================================
# PARAM DISCOVERY API ENDPOINTS
# ============================================================================
app.register_blueprint(api_param_discovery_arjun_bp)
app.register_blueprint(api_param_discovery_paramspider_bp)
app.register_blueprint(api_param_discovery_x8_bp)

# ============================================================================
# WEB SCAN API ENDPOINTS (BATCH 2)
# ============================================================================
app.register_blueprint(api_web_scan_jaeles_bp)
app.register_blueprint(api_web_scan_dalfox_bp)

# ============================================================================
# WEB PROBE API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_probe_httpx_bp)

# ============================================================================
# DATA PROCESSING API ENDPOINTS
# ============================================================================
app.register_blueprint(api_data_processing_anew_bp)

# ============================================================================
# PARAM FUZZ API ENDPOINTS
# ============================================================================
app.register_blueprint(api_param_fuzz_qsreplace_bp)

# ============================================================================
# URL FILTER API ENDPOINTS
# ============================================================================
app.register_blueprint(api_url_filter_uro_bp)

# ============================================================================
# WEB FRAMEWORK API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_framework_http_framework_bp)
app.register_blueprint(api_web_framework_browser_agent_bp)

# ============================================================================
# WEB SCAN API ENDPOINTS (BATCH 3)
# ============================================================================
app.register_blueprint(api_web_scan_burpsuite_bp)
app.register_blueprint(api_web_scan_zap_bp)

# ============================================================================
# WAF DETECT API ENDPOINTS
# ============================================================================
app.register_blueprint(api_waf_detect_wafw00f_bp)

# ============================================================================
# DNS ENUM API ENDPOINTS
# ============================================================================
app.register_blueprint(api_dns_enum_fierce_bp)
app.register_blueprint(api_dns_enum_dnsenum_bp)

# ============================================================================
# OPS API ENDPOINTS (PYTHON ENV)
# ============================================================================
app.register_blueprint(api_ops_python_env_bp)

# ============================================================================
# AI PAYLOAD API ENDPOINTS
# ============================================================================
app.register_blueprint(api_ai_payload_generate_payload_bp)
app.register_blueprint(api_ai_payload_test_payload_bp)

# ============================================================================
# API FUZZ ENDPOINTS
# ============================================================================
app.register_blueprint(api_api_fuzz_api_fuzzer_bp)

# ============================================================================
# SMB ENUM API ENDPOINTS
# ============================================================================
app.register_blueprint(api_smb_enum_nbtscan_bp)

# ============================================================================
# NET SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_net_scan_arp_scan_bp)

# ============================================================================
# CREDENTIAL HARVEST API ENDPOINTS
# ============================================================================
app.register_blueprint(api_credential_harvest_responder_bp)

# ============================================================================
# MEMORY FORENSICS API ENDPOINTS
# ============================================================================
app.register_blueprint(api_memory_forensics_volatility_bp)

# ============================================================================
# EXPLOIT FRAMEWORK API ENDPOINTS
# ============================================================================
app.register_blueprint(api_exploit_framework_msfvenom_bp)

# ============================================================================
# BINARY DEBUG API ENDPOINTS
# ============================================================================
app.register_blueprint(api_binary_debug_gdb_bp)
app.register_blueprint(api_binary_debug_gdb_peda_bp)
app.register_blueprint(api_binary_debug_radare2_bp)

# ============================================================================
# BINARY ANALYSIS API ENDPOINTS
# ============================================================================
app.register_blueprint(api_binary_analysis_binwalk_bp)
app.register_blueprint(api_binary_analysis_checksec_bp)

# ============================================================================
# GADGET SEARCH API ENDPOINTS
# ============================================================================
app.register_blueprint(api_gadget_search_ropgadget_bp)

# ============================================================================
# CONTAINER SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_container_scan_trivy_bp)
app.register_blueprint(api_container_scan_docker_bench_bp)
app.register_blueprint(api_container_scan_clair_bp)

# ============================================================================
# CLOUD AUDIT API ENDPOINTS
# ============================================================================
app.register_blueprint(api_cloud_audit_scout_suite_bp)

# ============================================================================
# CLOUD EXPLOIT API ENDPOINTS
# ============================================================================
app.register_blueprint(api_cloud_exploit_cloudmapper_bp)
app.register_blueprint(api_cloud_exploit_pacu_bp)

# ============================================================================
# K8S SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_k8s_scan_kube_hunter_bp)
app.register_blueprint(api_k8s_scan_kube_bench_bp)

# ============================================================================
# RUNTIME MONITOR API ENDPOINTS
# ============================================================================
app.register_blueprint(api_runtime_monitor_falco_bp)

# ============================================================================
# IAC SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_iac_scan_checkov_bp)
app.register_blueprint(api_iac_scan_terrascan_bp)

# ============================================================================
# NET LOOKUP API ENDPOINTS
# ============================================================================
app.register_blueprint(api_net_lookup_whois_bp)

# ============================================================================
# NET SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_net_scan_nmap_bp)

# ============================================================================
# WEB FUZZ API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_fuzz_gobuster_bp)

# ============================================================================
# VULN SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_vuln_scan_nuclei_bp)

# ============================================================================
# CLOUD AUDIT API ENDPOINTS
# ============================================================================
app.register_blueprint(api_cloud_audit_prowler_bp)

# ============================================================================
# RECON BOT API ENDPOINTS
# ============================================================================
app.register_blueprint(api_recon_bot_bbot_bp)

# ============================================================================
# INTELLIGENCE & VULNERABILITY INTELLIGENCE API ENDPOINTS
# ============================================================================
app.register_blueprint(api_vulnerability_intelligence_bp)

# ============================================================================
# BUG BOUNTY WORKFLOW API ENDPOINTS
# ============================================================================
app.register_blueprint(api_bugbounty_workflow_bug_bounty_recon_bp)

# ============================================================================
# WEB FUZZ API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_fuzz_dirb_bp)
app.register_blueprint(api_web_fuzz_ffuf_bp)

# ============================================================================
# WEB SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_scan_nikto_bp)
app.register_blueprint(api_web_scan_sqlmap_bp)
app.register_blueprint(api_web_scan_wpscan_bp)

# ============================================================================
# EXPLOIT FRAMEWORK API ENDPOINTS
# ============================================================================
app.register_blueprint(api_exploit_framework_metasploit_bp)
app.register_blueprint(api_exploit_framework_pwntools_bp)

# ============================================================================
# PASSWORD CRACKING API ENDPOINTS
# ============================================================================
app.register_blueprint(api_password_cracking_hydra_bp)
app.register_blueprint(api_password_cracking_john_bp)

# ============================================================================
# SMB ENUM API ENDPOINTS
# ============================================================================
app.register_blueprint(api_smb_enum_enum4linux_bp)
app.register_blueprint(api_smb_enum_netexec_bp)

# ============================================================================
# RECON API ENDPOINTS
# ============================================================================
app.register_blueprint(api_recon_amass_bp)
app.register_blueprint(api_recon_subfinder_bp)
app.register_blueprint(api_recon_autorecon_bp)

# ============================================================================
# PASSWORD CRACKING API ENDPOINTS
# ============================================================================
app.register_blueprint(api_password_cracking_hashcat_bp)

# ============================================================================
# SMB ENUM API ENDPOINTS
# ============================================================================
app.register_blueprint(api_smb_enum_smbmap_bp)
app.register_blueprint(api_smb_enum_enum4linux_ng_bp)
app.register_blueprint(api_smb_enum_rpcclient_bp)

# ============================================================================
# NET SCAN API ENDPOINTS
# ============================================================================
app.register_blueprint(api_net_scan_rustscan_bp)
app.register_blueprint(api_net_scan_masscan_bp)
app.register_blueprint(api_net_scan_nmap_advanced_bp)

# ============================================================================
# API SCAN ENDPOINTS
# ============================================================================
app.register_blueprint(api_api_scan_graphql_scanner_bp)
app.register_blueprint(api_api_scan_jwt_analyzer_bp)
app.register_blueprint(api_api_scan_api_schema_analyzer_bp)

# ============================================================================
# MEMORY FORENSICS ENDPOINTS
# ============================================================================
app.register_blueprint(api_memory_forensics_volatility3_bp)

# ============================================================================
# FILE CARVING ENDPOINTS
# ============================================================================
app.register_blueprint(api_file_carving_foremost_bp)

# ============================================================================
# STEGO ANALYSIS ENDPOINTS
# ============================================================================
app.register_blueprint(api_stego_analysis_steghide_bp)

# ============================================================================
# METADATA EXTRACT ENDPOINTS
# ============================================================================
app.register_blueprint(api_metadata_extract_exiftool_bp)

# ============================================================================
# CRYPTO ATTACK ENDPOINTS
# ============================================================================
app.register_blueprint(api_crypto_attack_hashpump_bp)

# ============================================================================
# WEB CRAWL ENDPOINTS
# ============================================================================
app.register_blueprint(api_web_crawl_hakrawler_bp)

# ============================================================================
# VULNERABILITY INTELLIGENCE ENDPOINTS
# ============================================================================
app.register_blueprint(api_vuln_intel_cve_monitor_bp)
app.register_blueprint(api_vuln_intel_exploit_generate_bp)
app.register_blueprint(api_vuln_intel_attack_chains_bp)
app.register_blueprint(api_vuln_intel_threat_feeds_bp)
app.register_blueprint(api_vuln_intel_zero_day_research_bp)

# ============================================================================
# AI ASSIST API ENDPOINTS
# ============================================================================
app.register_blueprint(api_ai_assist_advanced_payload_generation_bp)

# ============================================================================
# CTF API ENDPOINTS
# ============================================================================
app.register_blueprint(api_ctf_create_challenge_workflow_bp)
app.register_blueprint(api_ctf_auto_solve_challenge_bp)
app.register_blueprint(api_ctf_team_strategy_bp)
app.register_blueprint(api_ctf_suggest_tools_bp)
app.register_blueprint(api_ctf_cryptography_solver_bp)
app.register_blueprint(api_ctf_forensics_analyzer_bp)
app.register_blueprint(api_ctf_binary_analyzer_bp)

# ============================================================================
# PROCESS AUTO-SCALING & HEALTH CHECK BLUEPRINTS
# ============================================================================
app.register_blueprint(api_process_auto_scaling_bp)
app.register_blueprint(api_process_scale_pool_bp)
app.register_blueprint(api_process_health_check_bp)

# ============================================================================
# INTELLIGENT ERROR HANDLING BLUEPRINTS
# ============================================================================
app.register_blueprint(api_error_handling_statistics_bp)
app.register_blueprint(api_error_handling_test_recovery_bp)
app.register_blueprint(api_error_handling_fallback_chains_bp)
app.register_blueprint(api_error_handling_execute_with_recovery_bp)
app.register_blueprint(api_error_handling_classify_error_bp)
app.register_blueprint(api_error_handling_parameter_adjustments_bp)
app.register_blueprint(api_error_handling_alternative_tools_bp)

if __name__ == "__main__":
    BANNER = ModernVisualEngine.create_banner()
    # Display the beautiful new banner
    print(BANNER)

    parser = argparse.ArgumentParser(description="Run the HexStrike AI API Server")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--port", type=int, default=API_PORT, help=f"Port for the API server (default: {API_PORT}) i.e export HEXSTRIKE_PORT=8888")
    parser.add_argument("--host", type=str, default=API_HOST, help=f"Host for the API server (default: {API_HOST}) i.e export HEXSTRIKE_HOST=0.0.0.0")

    args = parser.parse_args()

    if args.debug:
        DEBUG_MODE = True
        logger.setLevel(logging.DEBUG)

    if args.port != API_PORT:
        API_PORT = args.port

    if args.host != API_HOST:
        API_HOST = args.host

    # Enhanced startup messages with beautiful formatting
    startup_info = f"""
{ModernVisualEngine.COLORS['MATRIX_GREEN']}{ModernVisualEngine.COLORS['BOLD']}╭─────────────────────────────────────────────────────────────────────────────╮{ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['NEON_BLUE']}🚀 Starting HexStrike AI Tools API Server{ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}├─────────────────────────────────────────────────────────────────────────────┤{ModernVisualEngine.COLORS['RESET']}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['CYBER_ORANGE']}🌐 Port:{ModernVisualEngine.COLORS['RESET']} {API_PORT}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['WARNING']}🔧 Debug Mode:{ModernVisualEngine.COLORS['RESET']} {DEBUG_MODE}
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['ELECTRIC_PURPLE']}💾 Cache Size:{ModernVisualEngine.COLORS['RESET']} {CACHE_SIZE} | TTL: {CACHE_TTL}s
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['TERMINAL_GRAY']}⏱️  Command Timeout:{ModernVisualEngine.COLORS['RESET']} {COMMAND_TIMEOUT}s
{ModernVisualEngine.COLORS['BOLD']}│{ModernVisualEngine.COLORS['RESET']} {ModernVisualEngine.COLORS['MATRIX_GREEN']}✨ Enhanced Visual Engine:{ModernVisualEngine.COLORS['RESET']} Active
{ModernVisualEngine.COLORS['MATRIX_GREEN']}{ModernVisualEngine.COLORS['BOLD']}╰─────────────────────────────────────────────────────────────────────────────╯{ModernVisualEngine.COLORS['RESET']}
"""

    for line in startup_info.strip().split('\n'):
        if line.strip():
            logger.info(line)

    app.run(host=API_HOST, port=API_PORT, debug=DEBUG_MODE)
