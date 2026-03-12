import subprocess
from flask import Blueprint, jsonify
api_auto_tool_bp = Blueprint("auto_tool", __name__)

APT_TOOLS = {
    "aircrack-ng", "amass", "arjun", "arp-scan", "autopsy", "binutils", "binwalk", 
    "bulk-extractor", "checksec", "dirb", "dirsearch", "enum4linux", "enum4linux-ng", 
    "exiftool", "feroxbuster", "ffuf", "file", "foremost", "gdb", "gobuster", "hashcat", 
    "hashcat-utils", "hashid", "hydra", "john", "kismet", "masscan", "medusa", "nbtscan", 
    "nikto", "nmap", "ophcrack", "outguess", "paramspider", "patator",
    "radare2", "responder", "ropper", "rustscan", "scalpel", "sleuthkit",
    "smbmap", "sqlmap", "steghide", "subfinder", "tcpdump", "testdisk", "tshark",
    "wireshark", "wpscan", "xxd"
}

def is_tool_installed(tool):
    from shutil import which
    return which(tool) is not None

@api_auto_tool_bp.route("/api/tools/auto-install-missing-apt", methods=["POST"])
def auto_install_missing_tools():
    """Detect missing apt-installable tools and attempt installation."""
    missing_tools = [tool for tool in APT_TOOLS if not is_tool_installed(tool)]
    results = {}
    for tool in missing_tools:
        proc = subprocess.run(
            ["sudo", "apt-get", "install", "-y", tool],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if proc.returncode == 0:
            results[tool] = {"status": "installed", "package": tool}
        else:
            results[tool] = {
                "status": "failed",
                "package": tool,
                "error": proc.stderr.strip()
            }
      
    return jsonify({
        "success": True,
        "attempted_tools": list(missing_tools),
        "results": results
    })
