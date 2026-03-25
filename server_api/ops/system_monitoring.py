from flask import Blueprint, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict
import logging
import subprocess
import threading
import time
import traceback

import server_core.config_core as config_core
from server_core.command_executor import execute_command
from server_core.modern_visual_engine import ModernVisualEngine
from server_core.singletons import cache, telemetry

logger = logging.getLogger(__name__)

api_system_monitoring_bp = Blueprint("api_system_monitoring", __name__)

# ============================================================================
# TOOL AVAILABILITY CACHE — populated once at startup, refreshed every hour
# ============================================================================
# List of tools considered always installed (built-in, code-provided or simulated)
BUILT_IN_TOOLS = ["jwt-analyzer", "api-schema-analyzer", "graphql-scanner", "http-framework"]

REQUIRE_DPKG_CHECK = ["hashcat-utils", "sleuthkit", "impacket-scripts"]

REQUIRE_PIP_CHECK = ["pwntools", "one-gadget"]

REQUIRE_GEM_CHECK = ["zsteg"]

REQUIRE_CARGO_CHECK = ["pwninit", "x8"]

BINARY_NAME_OVERRIDES = {
    "scout-suite": "scout",
    "volatility": "vol"
}

_HEALTH_TOOL_CATEGORIES = {
    "essential": ["nmap", "gobuster", "dirb", "nikto", "sqlmap", "hydra", "john", "hashcat"],
    "network_recon": ["rustscan", "masscan", "autorecon", "nbtscan", "arp-scan", "responder",
                "nxc", "enum4linux-ng", "rpcclient", "enum4linux", "smbmap", "evil-winrm"],
    "web_recon": ["ffuf", "feroxbuster", "dirsearch", "dotdotpwn", "xsser", "wfuzz",
                     "arjun", "paramspider", "x8", "jaeles", "dalfox",
                     "httpx", "wafw00f", "burpsuite", "katana", "hakrawler", "wpscan"],
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
    "osint": ["amass", "subfinder", "fierce", "dnsenum", "theharvester", "sherlock",
              "social-analyzer", "recon-ng", "maltego", "spiderfoot",
              "have-i-been-pwned", "whois", "bbot", "gau", "waybackurls"],
    "exploitation": ["msfconsole", "msfvenom", "searchsploit"],
    "api": ["api-schema-analyzer", "curl", "http-framework", "anew", "qsreplace", "uro"],
    "wifi_pentest": ["kismet", "wireshark", "tshark", "tcpdump",
                 "airbase-ng", "airdecap-ng", "hcxdumptool", "hcxpcapngtool",
                 "mdk4", "eaphammer", "wifite", "bettercap", "airmon-ng", "airodump-ng", "aireplay-ng", "aircrack-ng"],
    "database": ["mysql", "sqlite3"],
    "active_directory": [
        "impacket-scripts"
    ],
    "vulnerability_intelligence": ["vulnx"]

    #Not in use: httpie, postman, insomnia, "shodan-cli", "censys-cli", 
    
    #"active_directory": [
    #    "impacket-scripts", "bloodhound-ce-python", "ldapdomaindump",
    #    "certipy-ad", "mitm6", "adidnsdump", "pywerview"
    #]
}

_tool_availability_cache: Dict[str, bool] = {}
_tool_availability_lock = threading.Lock()
_tool_availability_last_refresh: float = 0.0


def _refresh_tool_availability() -> None:
    """Probe all tools with `which` in parallel and update the module-level cache."""
    global _tool_availability_last_refresh
    all_tools_flat = list({
        tool
        for tools in _HEALTH_TOOL_CATEGORIES.values()
        for tool in tools
    })

    def probe(tool: str) -> tuple:
        if tool in BINARY_NAME_OVERRIDES:
            tool_to_check = BINARY_NAME_OVERRIDES[tool]
        else:
            tool_to_check = tool
        if tool_to_check in BUILT_IN_TOOLS:
            # Always report built-ins as available without probing
            return tool, True
        try:
            if tool_to_check in REQUIRE_DPKG_CHECK:
                # For tools that require dpkg, check if the package is installed
                result = subprocess.run(
                    ["dpkg", "-s", tool_to_check],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return tool, result.returncode == 0
            elif tool_to_check in REQUIRE_PIP_CHECK:
                # For tools that require pip, check if the package is installed
                result = subprocess.run(
                    ["pip3", "list", "|", "grep", tool_to_check],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return tool, result.returncode == 0
            elif tool_to_check in REQUIRE_GEM_CHECK:
                # For tools that require gem, check if the package is installed
                result = subprocess.run(
                    ["gem", "list", "|", "grep", tool_to_check],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return tool, result.returncode == 0
            elif tool_to_check in REQUIRE_CARGO_CHECK:
                # For tools that require cargo, check if the package is installed
                result = subprocess.run(
                    ["cargo", "install", "--list", "|", "grep", tool_to_check],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return tool, result.returncode == 0
            else:
                result = subprocess.run(
                    ["which", tool_to_check],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return tool, result.returncode == 0
        except Exception:
            return tool, False

    with ThreadPoolExecutor(max_workers=20) as pool:
        results = dict(pool.map(probe, all_tools_flat))

    with _tool_availability_lock:
        _tool_availability_cache.update(results)
        _tool_availability_last_refresh = time.time()

    installed = sorted(t for t, ok in results.items() if ok)
    missing = sorted(t for t, ok in results.items() if not ok)
    GREEN = ModernVisualEngine.COLORS['MATRIX_GREEN']
    RED = ModernVisualEngine.COLORS['HACKER_RED']
    RESET = ModernVisualEngine.COLORS['RESET']
    lines = ["Tool availability refreshed: %d/%d available" % (len(installed), len(results))]
    for tool in installed:
        lines.append("%s  %-30s installed%s" % (GREEN, tool, RESET))
    for tool in missing:
        lines.append("%s  %-30s NOT INSTALLED%s" % (RED, tool, RESET))
    logger.info("\n".join(lines))


def _get_tool_availability() -> Dict[str, bool]:
    """Return cached tool availability, refreshing in a background thread if stale."""
    now = time.time()
    with _tool_availability_lock:
        stale = (now - _tool_availability_last_refresh) > config_core.get("TOOL_AVAILABILITY_TTL", 3600)
        empty = not _tool_availability_cache

    if empty:
        _refresh_tool_availability()
    elif stale:
        threading.Thread(target=_refresh_tool_availability, daemon=True).start()

    with _tool_availability_lock:
        # Always set any built-in tool as available in returned status
        output_status = dict(_tool_availability_cache)
        for tool in BUILT_IN_TOOLS:
            output_status[tool] = True
        return output_status


@api_system_monitoring_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint with comprehensive tool detection"""
    tools_status = _get_tool_availability()

    essential_tools = _HEALTH_TOOL_CATEGORIES["essential"]
    all_essential_tools_available = all(tools_status.get(t, False) for t in essential_tools)

    category_stats = {
        cat: {
            "total": len(tools),
            "available": sum(1 for t in tools if tools_status.get(t, False)),
        }
        for cat, tools in _HEALTH_TOOL_CATEGORIES.items()
    }

    all_tools_count = len(tools_status)

    return jsonify({
        "status": "healthy",
        "message": "HexStrike AI Tools API Server is operational",
        "version": config_core.get("VERSION", "unknown"),
        "tools_status": tools_status,
        "all_essential_tools_available": all_essential_tools_available,
        "total_tools_available": sum(1 for available in tools_status.values() if available),
        "total_tools_count": all_tools_count,
        "category_stats": category_stats,
        "cache_stats": cache.get_stats(),
        "telemetry": telemetry.get_stats(),
        "uptime": time.time() - telemetry.stats["start_time"],
        "tool_availability_age_seconds": round(time.time() - _tool_availability_last_refresh, 1),
    })


@api_system_monitoring_bp.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "success": True,
        "message": "Pong! HexStrike AI Tools API Server is responsive",
        "timestamp": datetime.now().isoformat()
    })


@api_system_monitoring_bp.route("/api/command", methods=["POST"])
def generic_command():
    """Execute any command provided in the request with enhanced logging"""
    try:
        params = request.json
        command = params.get("command", "")
        use_cache = params.get("use_cache", True)

        if not command:
            logger.warning("Command endpoint called without command parameter")
            return jsonify({
                "error": "Command parameter is required"
            }), 400

        result = execute_command(command, use_cache=use_cache)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in command endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500


@api_system_monitoring_bp.route("/api/cache/stats", methods=["GET"])
def cache_stats():
    """Get cache statistics"""
    return jsonify(cache.get_stats())


@api_system_monitoring_bp.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """Clear the cache"""
    cache.clear()
    logger.info("Cache cleared")
    return jsonify({"success": True, "message": "Cache cleared"})


@api_system_monitoring_bp.route("/api/telemetry", methods=["GET"])
def get_telemetry():
    """Get system telemetry"""
    return jsonify(telemetry.get_stats())
