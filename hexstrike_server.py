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
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify, abort
import re
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
# API Routes

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

# ============================================================================
# CTF COMPETITION EXCELLENCE FRAMEWORK API ENDPOINTS (v8.0 ENHANCEMENT)
# ============================================================================

@app.route("/api/ctf/forensics-analyzer", methods=["POST"])
def ctf_forensics_analyzer():
    """Advanced forensics challenge analyzer with multiple investigation techniques"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        analysis_type = params.get("analysis_type", "comprehensive")
        extract_hidden = params.get("extract_hidden", True)
        check_steganography = params.get("check_steganography", True)

        if not file_path:
            return jsonify({"error": "File path is required"}), 400

        results = {
            "file_path": file_path,
            "analysis_type": analysis_type,
            "file_info": {},
            "metadata": {},
            "hidden_data": [],
            "steganography_results": [],
            "recommended_tools": [],
            "next_steps": []
        }

        # Basic file analysis
        try:
            # File command
            file_result = subprocess.run(['file', file_path], capture_output=True, text=True, timeout=30)
            if file_result.returncode == 0:
                results["file_info"]["type"] = file_result.stdout.strip()

                # Determine file category and suggest tools
                file_type = file_result.stdout.lower()
                if "image" in file_type:
                    results["recommended_tools"].extend(["exiftool", "steghide", "stegsolve", "zsteg"])
                    results["next_steps"].extend([
                        "Extract EXIF metadata",
                        "Check for steganographic content",
                        "Analyze color channels separately"
                    ])
                elif "audio" in file_type:
                    results["recommended_tools"].extend(["audacity", "sonic-visualizer", "spectrum-analyzer"])
                    results["next_steps"].extend([
                        "Analyze audio spectrum",
                        "Check for hidden data in audio channels",
                        "Look for DTMF tones or morse code"
                    ])
                elif "pdf" in file_type:
                    results["recommended_tools"].extend(["pdfinfo", "pdftotext", "binwalk"])
                    results["next_steps"].extend([
                        "Extract text and metadata",
                        "Check for embedded files",
                        "Analyze PDF structure"
                    ])
                elif "zip" in file_type or "archive" in file_type:
                    results["recommended_tools"].extend(["unzip", "7zip", "binwalk"])
                    results["next_steps"].extend([
                        "Extract archive contents",
                        "Check for password protection",
                        "Look for hidden files"
                    ])
        except Exception as e:
            results["file_info"]["error"] = str(e)

        # Metadata extraction
        try:
            exif_result = subprocess.run(['exiftool', file_path], capture_output=True, text=True, timeout=30)
            if exif_result.returncode == 0:
                results["metadata"]["exif"] = exif_result.stdout
        except Exception as e:
            results["metadata"]["exif_error"] = str(e)

        # Binwalk analysis for hidden files
        if extract_hidden:
            try:
                binwalk_result = subprocess.run(['binwalk', '-e', file_path], capture_output=True, text=True, timeout=60)
                if binwalk_result.returncode == 0:
                    results["hidden_data"].append({
                        "tool": "binwalk",
                        "output": binwalk_result.stdout
                    })
            except Exception as e:
                results["hidden_data"].append({
                    "tool": "binwalk",
                    "error": str(e)
                })

        # Steganography checks
        if check_steganography:
            # Check for common steganography tools
            steg_tools = ["steghide", "zsteg", "outguess"]
            for tool in steg_tools:
                try:
                    steg_result = None
                    if tool == "steghide":
                        steg_result = subprocess.run([tool, 'info', file_path], capture_output=True, text=True, timeout=30)
                    elif tool == "zsteg":
                        steg_result = subprocess.run([tool, '-a', file_path], capture_output=True, text=True, timeout=30)
                    elif tool == "outguess":
                        steg_result = subprocess.run([tool, '-r', file_path, '/tmp/outguess_output'], capture_output=True, text=True, timeout=30)

                    if steg_result and steg_result.returncode == 0 and steg_result.stdout.strip():
                        results["steganography_results"].append({
                            "tool": tool,
                            "output": steg_result.stdout
                        })
                except Exception as e:
                    results["steganography_results"].append({
                        "tool": tool,
                        "error": str(e)
                    })

        # Strings analysis
        try:
            strings_result = subprocess.run(['strings', file_path], capture_output=True, text=True, timeout=30)
            if strings_result.returncode == 0:
                # Look for interesting strings (flags, URLs, etc.)
                interesting_strings = []
                for line in strings_result.stdout.split('\n'):
                    if any(keyword in line.lower() for keyword in ['flag', 'password', 'key', 'secret', 'http', 'ftp']):
                        interesting_strings.append(line.strip())

                if interesting_strings:
                    results["hidden_data"].append({
                        "tool": "strings",
                        "interesting_strings": interesting_strings[:20]  # Limit to first 20
                    })
        except Exception as e:
            results["hidden_data"].append({
                "tool": "strings",
                "error": str(e)
            })

        logger.info(f"🔍 CTF forensics analysis completed | File: {file_path} | Tools used: {len(results['recommended_tools'])}")
        return jsonify({
            "success": True,
            "analysis": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in CTF forensics analyzer: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/ctf/binary-analyzer", methods=["POST"])
def ctf_binary_analyzer():
    """Advanced binary analysis for reverse engineering and pwn challenges"""
    try:
        params = request.json
        binary_path = params.get("binary_path", "")
        analysis_depth = params.get("analysis_depth", "comprehensive")  # basic, comprehensive, deep
        check_protections = params.get("check_protections", True)
        find_gadgets = params.get("find_gadgets", True)

        if not binary_path:
            return jsonify({"error": "Binary path is required"}), 400

        results = {
            "binary_path": binary_path,
            "analysis_depth": analysis_depth,
            "file_info": {},
            "security_protections": {},
            "interesting_functions": [],
            "strings_analysis": {},
            "gadgets": [],
            "recommended_tools": [],
            "exploitation_hints": []
        }

        # Basic file information
        try:
            file_result = subprocess.run(['file', binary_path], capture_output=True, text=True, timeout=30)
            if file_result.returncode == 0:
                results["file_info"]["type"] = file_result.stdout.strip()

                # Determine architecture and suggest tools
                file_output = file_result.stdout.lower()
                if "x86-64" in file_output or "x86_64" in file_output:
                    results["file_info"]["architecture"] = "x86_64"
                elif "i386" in file_output or "80386" in file_output:
                    results["file_info"]["architecture"] = "i386"
                elif "arm" in file_output:
                    results["file_info"]["architecture"] = "ARM"

                results["recommended_tools"].extend(["gdb-peda", "radare2", "ghidra"])
        except Exception as e:
            results["file_info"]["error"] = str(e)

        # Security protections check
        if check_protections:
            try:
                checksec_result = subprocess.run(['checksec', '--file', binary_path], capture_output=True, text=True, timeout=30)
                if checksec_result.returncode == 0:
                    results["security_protections"]["checksec"] = checksec_result.stdout

                    # Parse protections and provide exploitation hints
                    output = checksec_result.stdout.lower()
                    if "no canary found" in output:
                        results["exploitation_hints"].append("Stack canary disabled - buffer overflow exploitation possible")
                    if "nx disabled" in output:
                        results["exploitation_hints"].append("NX disabled - shellcode execution on stack possible")
                    if "no pie" in output:
                        results["exploitation_hints"].append("PIE disabled - fixed addresses, ROP/ret2libc easier")
                    if "no relro" in output:
                        results["exploitation_hints"].append("RELRO disabled - GOT overwrite attacks possible")
            except Exception as e:
                results["security_protections"]["error"] = str(e)

        # Strings analysis
        try:
            strings_result = subprocess.run(['strings', binary_path], capture_output=True, text=True, timeout=30)
            if strings_result.returncode == 0:
                strings_output = strings_result.stdout.split('\n')

                # Categorize interesting strings
                interesting_categories = {
                    "functions": [],
                    "format_strings": [],
                    "file_paths": [],
                    "potential_flags": [],
                    "system_calls": []
                }

                for string in strings_output:
                    string = string.strip()
                    if not string:
                        continue

                    # Look for function names
                    if any(func in string for func in ['printf', 'scanf', 'gets', 'strcpy', 'system', 'execve']):
                        interesting_categories["functions"].append(string)

                    # Look for format strings
                    if '%' in string and any(fmt in string for fmt in ['%s', '%d', '%x', '%n']):
                        interesting_categories["format_strings"].append(string)

                    # Look for file paths
                    if string.startswith('/') or '\\' in string:
                        interesting_categories["file_paths"].append(string)

                    # Look for potential flags
                    if any(keyword in string.lower() for keyword in ['flag', 'ctf', 'key', 'password']):
                        interesting_categories["potential_flags"].append(string)

                    # Look for system calls
                    if string in ['sh', 'bash', '/bin/sh', '/bin/bash', 'cmd.exe']:
                        interesting_categories["system_calls"].append(string)

                results["strings_analysis"] = interesting_categories

                # Add exploitation hints based on strings
                if interesting_categories["functions"]:
                    dangerous_funcs = ['gets', 'strcpy', 'sprintf', 'scanf']
                    found_dangerous = [f for f in dangerous_funcs if any(f in s for s in interesting_categories["functions"])]
                    if found_dangerous:
                        results["exploitation_hints"].append(f"Dangerous functions found: {', '.join(found_dangerous)} - potential buffer overflow")

                if interesting_categories["format_strings"]:
                    if any('%n' in s for s in interesting_categories["format_strings"]):
                        results["exploitation_hints"].append("Format string with %n found - potential format string vulnerability")

        except Exception as e:
            results["strings_analysis"] = {"error": str(e)}

        # ROP gadgets search
        if find_gadgets and analysis_depth in ["comprehensive", "deep"]:
            try:
                ropgadget_result = subprocess.run(['ROPgadget', '--binary', binary_path, '--only', 'pop|ret'], capture_output=True, text=True, timeout=60)
                if ropgadget_result.returncode == 0:
                    gadget_lines = ropgadget_result.stdout.split('\n')
                    useful_gadgets = []

                    for line in gadget_lines:
                        if 'pop' in line and 'ret' in line:
                            useful_gadgets.append(line.strip())

                    results["gadgets"] = useful_gadgets[:20]  # Limit to first 20 gadgets

                    if useful_gadgets:
                        results["exploitation_hints"].append(f"Found {len(useful_gadgets)} ROP gadgets - ROP chain exploitation possible")
                        results["recommended_tools"].append("ropper")

            except Exception as e:
                results["gadgets"] = [f"Error finding gadgets: {str(e)}"]

        # Function analysis with objdump
        if analysis_depth in ["comprehensive", "deep"]:
            try:
                objdump_result = subprocess.run(['objdump', '-t', binary_path], capture_output=True, text=True, timeout=30)
                if objdump_result.returncode == 0:
                    functions = []
                    for line in objdump_result.stdout.split('\n'):
                        if 'F .text' in line:  # Function in text section
                            parts = line.split()
                            if len(parts) >= 6:
                                func_name = parts[-1]
                                functions.append(func_name)

                    results["interesting_functions"] = functions[:50]  # Limit to first 50 functions
            except Exception as e:
                results["interesting_functions"] = [f"Error analyzing functions: {str(e)}"]

        # Add tool recommendations based on findings
        if results["exploitation_hints"]:
            results["recommended_tools"].extend(["pwntools", "gdb-peda", "one-gadget"])

        if "format string" in str(results["exploitation_hints"]).lower():
            results["recommended_tools"].append("format-string-exploiter")

        logger.info(f"🔬 CTF binary analysis completed | Binary: {binary_path} | Hints: {len(results['exploitation_hints'])}")
        return jsonify({
            "success": True,
            "analysis": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in CTF binary analyzer: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# ADVANCED PROCESS MANAGEMENT API ENDPOINTS (v10.0 ENHANCEMENT)
# ============================================================================

@app.route("/api/process/execute-async", methods=["POST"])
def execute_command_async():
    """Execute command asynchronously using enhanced process management"""
    try:
        params = request.json
        command = params.get("command", "")
        context = params.get("context", {})

        if not command:
            return jsonify({"error": "Command parameter is required"}), 400

        # Execute command asynchronously
        task_id = enhanced_process_manager.execute_command_async(command, context)

        logger.info(f"🚀 Async command execution started | Task ID: {task_id}")
        return jsonify({
            "success": True,
            "task_id": task_id,
            "command": command,
            "status": "submitted",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in async command execution: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/get-task-result/<task_id>", methods=["GET"])
def get_async_task_result(task_id):
    """Get result of asynchronous task"""
    try:
        result = enhanced_process_manager.get_task_result(task_id)

        if result["status"] == "not_found":
            return jsonify({"error": "Task not found"}), 404

        logger.info(f"📋 Task result retrieved | Task ID: {task_id} | Status: {result['status']}")
        return jsonify({
            "success": True,
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error getting task result: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/pool-stats", methods=["GET"])
def get_process_pool_stats():
    """Get process pool statistics and performance metrics"""
    try:
        stats = enhanced_process_manager.get_comprehensive_stats()

        logger.info(f"📊 Process pool stats retrieved | Active workers: {stats['process_pool']['active_workers']}")
        return jsonify({
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error getting pool stats: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/cache-stats", methods=["GET"])
def get_cache_stats():
    """Get advanced cache statistics"""
    try:
        cache_stats = enhanced_process_manager.cache.get_stats()

        logger.info(f"💾 Cache stats retrieved | Hit rate: {cache_stats['hit_rate']:.1f}%")
        return jsonify({
            "success": True,
            "cache_stats": cache_stats,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error getting cache stats: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/clear-cache", methods=["POST"])
def clear_process_cache():
    """Clear the advanced cache"""
    try:
        enhanced_process_manager.cache.clear()

        logger.info("🧹 Process cache cleared")
        return jsonify({
            "success": True,
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error clearing cache: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/resource-usage", methods=["GET"])
def get_resource_usage():
    """Get current system resource usage and trends"""
    try:
        current_usage = enhanced_process_manager.resource_monitor.get_current_usage()
        usage_trends = enhanced_process_manager.resource_monitor.get_usage_trends()

        logger.info(f"📈 Resource usage retrieved | CPU: {current_usage['cpu_percent']:.1f}% | Memory: {current_usage['memory_percent']:.1f}%")
        return jsonify({
            "success": True,
            "current_usage": current_usage,
            "usage_trends": usage_trends,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error getting resource usage: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/performance-dashboard", methods=["GET"])
def get_performance_dashboard():
    """Get performance dashboard data"""
    try:
        dashboard_data = enhanced_process_manager.performance_dashboard.get_summary()
        pool_stats = enhanced_process_manager.process_pool.get_pool_stats()
        resource_usage = enhanced_process_manager.resource_monitor.get_current_usage()

        # Create comprehensive dashboard
        dashboard = {
            "performance_summary": dashboard_data,
            "process_pool": pool_stats,
            "resource_usage": resource_usage,
            "cache_stats": enhanced_process_manager.cache.get_stats(),
            "auto_scaling_status": enhanced_process_manager.auto_scaling_enabled,
            "system_health": {
                "cpu_status": "healthy" if resource_usage["cpu_percent"] < 80 else "warning" if resource_usage["cpu_percent"] < 95 else "critical",
                "memory_status": "healthy" if resource_usage["memory_percent"] < 85 else "warning" if resource_usage["memory_percent"] < 95 else "critical",
                "disk_status": "healthy" if resource_usage["disk_percent"] < 90 else "warning" if resource_usage["disk_percent"] < 98 else "critical"
            }
        }

        logger.info(f"📊 Performance dashboard retrieved | Success rate: {dashboard_data.get('success_rate', 0):.1f}%")
        return jsonify({
            "success": True,
            "dashboard": dashboard,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error getting performance dashboard: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/terminate-gracefully/<int:pid>", methods=["POST"])
def terminate_process_gracefully(pid):
    """Terminate process with graceful degradation"""
    try:
        params = request.json or {}
        timeout = params.get("timeout", 30)

        success = enhanced_process_manager.terminate_process_gracefully(pid, timeout)

        if success:
            logger.info(f"✅ Process {pid} terminated gracefully")
            return jsonify({
                "success": True,
                "message": f"Process {pid} terminated successfully",
                "pid": pid,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to terminate process {pid}",
                "pid": pid,
                "timestamp": datetime.now().isoformat()
            }), 400

    except Exception as e:
        logger.error(f"💥 Error terminating process {pid}: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/auto-scaling", methods=["POST"])
def configure_auto_scaling():
    """Configure auto-scaling settings"""
    try:
        params = request.json
        enabled = params.get("enabled", True)
        thresholds = params.get("thresholds", {})

        # Update auto-scaling configuration
        enhanced_process_manager.auto_scaling_enabled = enabled

        if thresholds:
            enhanced_process_manager.resource_thresholds.update(thresholds)

        logger.info(f"⚙️ Auto-scaling configured | Enabled: {enabled}")
        return jsonify({
            "success": True,
            "auto_scaling_enabled": enabled,
            "resource_thresholds": enhanced_process_manager.resource_thresholds,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error configuring auto-scaling: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/scale-pool", methods=["POST"])
def manual_scale_pool():
    """Manually scale the process pool"""
    try:
        params = request.json
        action = params.get("action", "")  # "up" or "down"
        count = params.get("count", 1)

        if action not in ["up", "down"]:
            return jsonify({"error": "Action must be 'up' or 'down'"}), 400

        current_stats = enhanced_process_manager.process_pool.get_pool_stats()
        current_workers = current_stats["active_workers"]

        if action == "up":
            max_workers = enhanced_process_manager.process_pool.max_workers
            if current_workers + count <= max_workers:
                enhanced_process_manager.process_pool._scale_up(count)
                new_workers = current_workers + count
                message = f"Scaled up by {count} workers"
            else:
                return jsonify({"error": f"Cannot scale up: would exceed max workers ({max_workers})"}), 400
        else:  # down
            min_workers = enhanced_process_manager.process_pool.min_workers
            if current_workers - count >= min_workers:
                enhanced_process_manager.process_pool._scale_down(count)
                new_workers = current_workers - count
                message = f"Scaled down by {count} workers"
            else:
                return jsonify({"error": f"Cannot scale down: would go below min workers ({min_workers})"}), 400

        logger.info(f"📏 Manual scaling | {message} | Workers: {current_workers} → {new_workers}")
        return jsonify({
            "success": True,
            "message": message,
            "previous_workers": current_workers,
            "current_workers": new_workers,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error scaling pool: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/process/health-check", methods=["GET"])
def process_health_check():
    """Comprehensive health check of the process management system"""
    try:
        # Get all system stats
        comprehensive_stats = enhanced_process_manager.get_comprehensive_stats()

        # Determine overall health
        resource_usage = comprehensive_stats["resource_usage"]
        pool_stats = comprehensive_stats["process_pool"]
        cache_stats = comprehensive_stats["cache"]

        health_score = 100
        issues = []

        # CPU health
        if resource_usage["cpu_percent"] > 95:
            health_score -= 30
            issues.append("Critical CPU usage")
        elif resource_usage["cpu_percent"] > 80:
            health_score -= 15
            issues.append("High CPU usage")

        # Memory health
        if resource_usage["memory_percent"] > 95:
            health_score -= 25
            issues.append("Critical memory usage")
        elif resource_usage["memory_percent"] > 85:
            health_score -= 10
            issues.append("High memory usage")

        # Disk health
        if resource_usage["disk_percent"] > 98:
            health_score -= 20
            issues.append("Critical disk usage")
        elif resource_usage["disk_percent"] > 90:
            health_score -= 5
            issues.append("High disk usage")

        # Process pool health
        if pool_stats["queue_size"] > 50:
            health_score -= 15
            issues.append("High task queue backlog")

        # Cache health
        if cache_stats["hit_rate"] < 30:
            health_score -= 10
            issues.append("Low cache hit rate")

        health_score = max(0, health_score)

        # Determine status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        elif health_score >= 25:
            status = "poor"
        else:
            status = "critical"

        health_report = {
            "overall_status": status,
            "health_score": health_score,
            "issues": issues,
            "system_stats": comprehensive_stats,
            "recommendations": []
        }

        # Add recommendations based on issues
        if "High CPU usage" in issues:
            health_report["recommendations"].append("Consider reducing concurrent processes or upgrading CPU")
        if "High memory usage" in issues:
            health_report["recommendations"].append("Clear caches or increase available memory")
        if "High task queue backlog" in issues:
            health_report["recommendations"].append("Scale up process pool or optimize task processing")
        if "Low cache hit rate" in issues:
            health_report["recommendations"].append("Review cache TTL settings or increase cache size")

        logger.info(f"🏥 Health check completed | Status: {status} | Score: {health_score}/100")
        return jsonify({
            "success": True,
            "health_report": health_report,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in health check: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# BANNER AND STARTUP CONFIGURATION
# ============================================================================

# ============================================================================
# INTELLIGENT ERROR HANDLING API ENDPOINTS
# ============================================================================

@app.route("/api/error-handling/statistics", methods=["GET"])
def get_error_statistics():
    """Get error handling statistics"""
    try:
        stats = error_handler.get_error_statistics()
        return jsonify({
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting error statistics: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/error-handling/test-recovery", methods=["POST"])
def test_error_recovery():
    """Test error recovery system with simulated failures"""
    try:
        data = request.get_json()
        tool_name = data.get("tool_name", "nmap")
        error_type = data.get("error_type", "timeout")
        target = data.get("target", "example.com")

        # Simulate an error for testing
        if error_type == "timeout":
            exception = TimeoutError("Simulated timeout error")
        elif error_type == "permission_denied":
            exception = PermissionError("Simulated permission error")
        elif error_type == "network_unreachable":
            exception = ConnectionError("Simulated network error")
        else:
            exception = Exception(f"Simulated {error_type} error")

        context = {
            "target": target,
            "parameters": data.get("parameters", {}),
            "attempt_count": 1
        }

        # Get recovery strategy
        recovery_strategy = error_handler.handle_tool_failure(tool_name, exception, context)

        return jsonify({
            "success": True,
            "recovery_strategy": {
                "action": recovery_strategy.action.value,
                "parameters": recovery_strategy.parameters,
                "max_attempts": recovery_strategy.max_attempts,
                "success_probability": recovery_strategy.success_probability,
                "estimated_time": recovery_strategy.estimated_time
            },
            "error_classification": error_handler.classify_error(str(exception), exception).value,
            "alternative_tools": error_handler.tool_alternatives.get(tool_name, []),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error testing recovery system: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/error-handling/fallback-chains", methods=["GET"])
def get_fallback_chains():
    """Get available fallback tool chains"""
    try:
        operation = request.args.get("operation", "")
        failed_tools = request.args.getlist("failed_tools")

        if operation:
            fallback_chain = degradation_manager.create_fallback_chain(operation, failed_tools)
            return jsonify({
                "success": True,
                "operation": operation,
                "fallback_chain": fallback_chain,
                "is_critical": degradation_manager.is_critical_operation(operation),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": True,
                "available_operations": list(degradation_manager.fallback_chains.keys()),
                "critical_operations": list(degradation_manager.critical_operations),
                "timestamp": datetime.now().isoformat()
            })

    except Exception as e:
        logger.error(f"Error getting fallback chains: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/error-handling/execute-with-recovery", methods=["POST"])
def execute_with_recovery_endpoint():
    """Execute a command with intelligent error handling and recovery"""
    try:
        data = request.get_json()
        tool_name = data.get("tool_name", "")
        command = data.get("command", "")
        parameters = data.get("parameters", {})
        max_attempts = data.get("max_attempts", 3)
        use_cache = data.get("use_cache", True)

        if not tool_name or not command:
            return jsonify({"error": "tool_name and command are required"}), 400

        # Execute command with recovery
        result = execute_command_with_recovery(
            tool_name=tool_name,
            command=command,
            parameters=parameters,
            use_cache=use_cache,
            max_attempts=max_attempts
        )

        return jsonify({
            "success": result.get("success", False),
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error executing command with recovery: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/error-handling/classify-error", methods=["POST"])
def classify_error_endpoint():
    """Classify an error message"""
    try:
        data = request.get_json()
        error_message = data.get("error_message", "")

        if not error_message:
            return jsonify({"error": "error_message is required"}), 400

        error_type = error_handler.classify_error(error_message)
        recovery_strategies = error_handler.recovery_strategies.get(error_type, [])

        return jsonify({
            "success": True,
            "error_type": error_type.value,
            "recovery_strategies": [
                {
                    "action": strategy.action.value,
                    "parameters": strategy.parameters,
                    "success_probability": strategy.success_probability,
                    "estimated_time": strategy.estimated_time
                }
                for strategy in recovery_strategies
            ],
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error classifying error: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/error-handling/parameter-adjustments", methods=["POST"])
def get_parameter_adjustments():
    """Get parameter adjustments for a tool and error type"""
    try:
        data = request.get_json()
        tool_name = data.get("tool_name", "")
        error_type_str = data.get("error_type", "")
        original_params = data.get("original_params", {})

        if not tool_name or not error_type_str:
            return jsonify({"error": "tool_name and error_type are required"}), 400

        # Convert string to ErrorType enum
        try:
            error_type = ErrorType(error_type_str)
        except ValueError:
            return jsonify({"error": f"Invalid error_type: {error_type_str}"}), 400

        adjusted_params = error_handler.auto_adjust_parameters(tool_name, error_type, original_params)

        return jsonify({
            "success": True,
            "tool_name": tool_name,
            "error_type": error_type.value,
            "original_params": original_params,
            "adjusted_params": adjusted_params,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting parameter adjustments: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/error-handling/alternative-tools", methods=["GET"])
def get_alternative_tools():
    """Get alternative tools for a given tool"""
    try:
        tool_name = request.args.get("tool_name", "")

        if not tool_name:
            return jsonify({"error": "tool_name parameter is required"}), 400

        alternatives = error_handler.tool_alternatives.get(tool_name, [])

        return jsonify({
            "success": True,
            "tool_name": tool_name,
            "alternatives": alternatives,
            "has_alternatives": len(alternatives) > 0,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting alternative tools: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Create the banner after all classes are defined

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
