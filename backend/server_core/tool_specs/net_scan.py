import glob
import os
import re
import shlex
import socket
import stat
import sys

from backend.server_core import config_core
from backend.server_core.tool_spec import ParamSpec, ToolSpec, ToolValidationError


def _arp_scan_command(p: dict) -> str:
    if not p["target"] and not p["local_network"]:
        raise ToolValidationError("Target parameter or local_network flag is required")

    argv = ["arp-scan", "-t", str(p["timeout"]), "-r", str(p["retry"])]
    if p["interface"]:
        argv.append("-I")
        argv.append(p["interface"])
    if p["local_network"]:
        argv.append("-l")
    else:
        argv.append(p["target"])
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _masscan_command(p: dict) -> str:
    target = p["target"].strip()
    # Leave numeric addresses, CIDRs, ranges and target lists for Masscan to parse.
    if target and not re.fullmatch(r"[0-9.\-]+", target) and not any(
        char in target for char in "/:, \t\n"
    ):
        try:
            target = socket.gethostbyname(target)
        except (OSError, UnicodeError) as exc:
            raise ToolValidationError("Could not resolve the Masscan target to an IPv4 address") from exc
    argv = ["masscan", target, f"-p{p['ports']}", f"--rate={p['rate']}"]
    if p["interface"]:
        argv.append("-e")
        argv.append(p["interface"])
    if p["router_mac"]:
        argv.append("--router-mac")
        argv.append(p["router_mac"])
    if p["source_ip"]:
        argv.append("--source-ip")
        argv.append(p["source_ip"])
    if p["banners"]:
        argv.append("--banners")
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _rustscan_command(p: dict) -> str:
    argv = [
        "rustscan", "-a", p["target"],
        "--ulimit", str(p["ulimit"]), "-b", str(p["batch_size"]), "-t", str(p["timeout"]),
    ]
    if p["ports"]:
        argv.append("-p")
        argv.append(p["ports"])
    if p["scripts"]:
        argv.append("--")
        argv.append("-sC")
        argv.append("-sV")
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


def _nmap_binary() -> str:
    override = config_core.get("BINARY_PATH_OVERRIDES", {}).get("nmap", "")
    if not override:
        return "nmap"
    return os.path.expanduser(override.replace("{HOME}", os.path.expanduser("~")))


def _nmap_prefix(scan_type: str, additional_args: str) -> list:
    argv = [_nmap_binary()]
    # A custom executable or wrapper remains responsible for its own privileges.
    if config_core.get("BINARY_PATH_OVERRIDES", {}).get("nmap"):
        return argv
    options = shlex.split(scan_type) + shlex.split(additional_args)
    syn_scan = any(re.fullmatch(r"-s[ACFIMNORSTUVWXYZ]+", option)
                   and "S" in option[2:] for option in options)
    if sys.platform != "darwin" or os.geteuid() == 0 or not syn_scan:
        return argv
    if "--send-ip" in options or "--unprivileged" in options:
        raise ToolValidationError("macOS SYN scans without root require BPF access and --send-eth")
    for device in glob.glob("/dev/bpf[0-9]*"):
        try:
            accessible = stat.S_ISCHR(os.stat(device).st_mode) and os.access(device, os.R_OK | os.W_OK)
        except OSError:
            continue
        if accessible:
            # BPF permits Ethernet I/O without running Nmap or its scripts as root.
            return argv + ["--privileged", "--send-eth"]
    raise ToolValidationError(
        "macOS SYN scans need packet-device access. Run ./nyxstrike.sh -a -t, "
        "then sign out and back in and restart NyxStrike to activate group membership. "
        "VPN and other non-Ethernet interfaces may still require root."
    )


def _nmap_command(p: dict) -> str:
    argv = _nmap_prefix(p["scan_type"], p["additional_args"]) + shlex.split(p["scan_type"])
    if p["ports"]:
        argv.append("-p")
        argv.append(p["ports"])
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    argv.append(p["target"])
    return shlex.join(argv)


def _nmap_advanced_command(p: dict) -> str:
    argv = _nmap_prefix(p["scan_type"], p["additional_args"]) + shlex.split(p["scan_type"]) + [p["target"]]
    if p["ports"]:
        argv.append("-p")
        argv.append(p["ports"])
    if p["stealth"]:
        argv.append("-T2")
        argv.append("-f")
        argv.append("--mtu")
        argv.append("24")
    else:
        argv.append(f"-{p['timing']}")
    if p["os_detection"]:
        argv.append("-O")
    if p["version_detection"]:
        argv.append("-sV")
    if p["aggressive"]:
        argv.append("-A")
    if p["nse_scripts"]:
        argv.append(f"--script={p['nse_scripts']}")
    elif not p["aggressive"]:
        argv.append("-sC")
    if p["additional_args"]:
        argv.extend(shlex.split(p["additional_args"]))
    return shlex.join(argv)


SPECS = [
    ToolSpec(
        name="arp-scan",
        mcp_tool_name="arp_scan_discovery",
        endpoint="/api/tools/arp-scan",
        category="net_scan",
        description="Execute arp-scan for network discovery.",
        params=[
            ParamSpec("target", str, default="", help_text="The target IP range (if not using local_network)"),
            ParamSpec("interface", str, default="", help_text="Network interface to use"),
            ParamSpec("local_network", bool, default=False, help_text="Scan local network"),
            ParamSpec("timeout", int, default=500, help_text="Timeout in milliseconds"),
            ParamSpec("retry", int, default=3, help_text="Number of retries"),
            ParamSpec("additional_args", str, default="", help_text="Additional arp-scan arguments"),
        ],
        build_command=_arp_scan_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="masscan",
        mcp_tool_name="masscan_high_speed",
        endpoint="/api/tools/masscan",
        category="net_scan",
        description="Execute Masscan for high-speed Internet-scale port scanning.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address or CIDR range"),
            ParamSpec("ports", str, default="1-65535", help_text="Port range to scan"),
            ParamSpec("rate", int, default=1000, help_text="Packets per second rate"),
            ParamSpec("interface", str, default="", help_text="Network interface to use"),
            ParamSpec("router_mac", str, default="", help_text="Router MAC address"),
            ParamSpec("source_ip", str, default="", help_text="Source IP address"),
            ParamSpec("banners", bool, default=False, help_text="Enable banner grabbing"),
            ParamSpec("additional_args", str, default="", help_text="Additional Masscan arguments"),
        ],
        build_command=_masscan_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="rustscan",
        mcp_tool_name="rustscan_fast_scan",
        endpoint="/api/tools/rustscan",
        category="net_scan",
        description="Execute Rustscan for ultra-fast port scanning.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address or hostname"),
            ParamSpec("ports", str, default="", help_text="Specific ports to scan (e.g., \"22,80,443\")"),
            ParamSpec("ulimit", int, default=5000, help_text="File descriptor limit"),
            ParamSpec("batch_size", int, default=4500, help_text="Batch size for scanning"),
            ParamSpec("timeout", int, default=1500, help_text="Timeout in milliseconds"),
            ParamSpec("scripts", bool, default=False, help_text="Run Nmap scripts on discovered ports"),
            ParamSpec("additional_args", str, default="", help_text="Additional Rustscan arguments"),
        ],
        build_command=_rustscan_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="nmap",
        mcp_tool_name="nmap_scan",
        endpoint="/api/tools/nmap",
        category="net_scan",
        description="Execute an Nmap scan against a target.",
        params=[
            ParamSpec("target", str, required=True, help_text="The IP address or hostname to scan"),
            ParamSpec("scan_type", str, default="-sCV", help_text="Scan type (e.g., -sV for version detection, -sC for scripts)"),
            ParamSpec("ports", str, default="", help_text="Comma-separated list of ports or port ranges"),
            ParamSpec("additional_args", str, default="-T4 -Pn", help_text="Additional Nmap arguments"),
        ],
        build_command=_nmap_command,
        use_recovery=True,
    ),
    ToolSpec(
        name="nmap-advanced",
        mcp_tool_name="nmap_advanced_scan",
        endpoint="/api/tools/nmap-advanced",
        category="net_scan",
        description="Execute advanced Nmap scans with custom NSE scripts and optimized timing.",
        params=[
            ParamSpec("target", str, required=True, help_text="The target IP address or hostname"),
            ParamSpec("scan_type", str, default="-sS", help_text="Nmap scan type (e.g., -sS, -sT, -sU)"),
            ParamSpec("ports", str, default="", help_text="Specific ports to scan"),
            ParamSpec("timing", str, default="T4", help_text="Timing template (T0-T5)"),
            ParamSpec("nse_scripts", str, default="", help_text="Custom NSE scripts to run"),
            ParamSpec("os_detection", bool, default=False, help_text="Enable OS detection"),
            ParamSpec("version_detection", bool, default=False, help_text="Enable version detection"),
            ParamSpec("aggressive", bool, default=False, help_text="Enable aggressive scanning"),
            ParamSpec("stealth", bool, default=False, help_text="Enable stealth mode"),
            ParamSpec("additional_args", str, default="", help_text="Additional Nmap arguments"),
        ],
        build_command=_nmap_advanced_command,
        use_recovery=True,
    ),
]
