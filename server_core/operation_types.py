"""Operation type helpers for tool execution and recovery."""

from typing import Dict

OPERATION_MAPPING: Dict[str, str] = {
  "nmap": "network_discovery",
  "rustscan": "network_discovery",
  "masscan": "network_discovery",
  "gobuster": "web_discovery",
  "feroxbuster": "web_discovery",
  "dirsearch": "web_discovery",
  "ffuf": "web_discovery",
  "nuclei": "vulnerability_scanning",
  "jaeles": "vulnerability_scanning",
  "nikto": "vulnerability_scanning",
  "subfinder": "subdomain_enumeration",
  "amass": "subdomain_enumeration",
  "assetfinder": "subdomain_enumeration",
  "shuffledns": "subdomain_enumeration",
  "massdns": "subdomain_enumeration",
  "arjun": "parameter_discovery",
  "paramspider": "parameter_discovery",
  "x8": "parameter_discovery",
}


def determine_operation_type(tool_name: str) -> str:
  """Determine operation type based on tool name."""
  return OPERATION_MAPPING.get(tool_name, "unknown_operation")
