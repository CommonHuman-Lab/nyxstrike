from dataclasses import dataclass
from typing import Dict, List, Set

from shared.target_types import TargetType, TechnologyStack


@dataclass(frozen=True)
class ToolSpec:
    name: str
    capabilities: Set[str]
    target_types: Set[str]
    objectives: Set[str]
    tech_affinities: Set[str]
    noise_score: float


def _all_targets() -> Set[str]:
    return {
        TargetType.WEB_APPLICATION.value,
        TargetType.API_ENDPOINT.value,
        TargetType.NETWORK_HOST.value,
        TargetType.CLOUD_SERVICE.value,
        TargetType.BINARY_FILE.value,
        TargetType.UNKNOWN.value,
    }


def build_tool_catalog() -> Dict[str, ToolSpec]:
    all_targets = _all_targets()

    return {
        "nmap": ToolSpec(
            name="nmap",
            capabilities={"surface", "network_scan", "service_enumeration"},
            target_types=all_targets,
            objectives={"quick", "comprehensive", "stealth", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.35,
        ),
        "nmap_advanced": ToolSpec(
            name="nmap_advanced",
            capabilities={"surface", "network_scan", "service_enumeration"},
            target_types={TargetType.NETWORK_HOST.value, TargetType.WEB_APPLICATION.value},
            objectives={"comprehensive", "internal_network_ad", "intelligence"},
            tech_affinities=set(),
            noise_score=0.55,
        ),
        "rustscan": ToolSpec(
            name="rustscan",
            capabilities={"surface", "network_scan"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"quick", "comprehensive", "reconnaissance", "internal_network_ad"},
            tech_affinities=set(),
            noise_score=0.4,
        ),
        "masscan": ToolSpec(
            name="masscan",
            capabilities={"network_scan"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"comprehensive", "reconnaissance"},
            tech_affinities=set(),
            noise_score=0.75,
        ),
        "arp-scan": ToolSpec(
            name="arp-scan",
            capabilities={"network_scan", "surface"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"quick", "comprehensive", "reconnaissance", "internal_network_ad", "intelligence"},
            tech_affinities=set(),
            noise_score=0.2,
        ),
        "httpx": ToolSpec(
            name="httpx",
            capabilities={"surface", "web_fingerprint", "api_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "stealth", "reconnaissance", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.15,
        ),
        "hurl": ToolSpec(
            name="hurl",
            capabilities={"api_assessment", "manual_validation"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "stealth", "reconnaissance", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "katana": ToolSpec(
            name="katana",
            capabilities={"content_discovery", "endpoint_discovery", "api_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"comprehensive", "reconnaissance", "api_security", "intelligence"},
            tech_affinities={TechnologyStack.REACT.value, TechnologyStack.ANGULAR.value, TechnologyStack.VUE.value},
            noise_score=0.3,
        ),
        "hakrawler": ToolSpec(
            name="hakrawler",
            capabilities={"content_discovery", "endpoint_discovery", "api_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "reconnaissance", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.28,
        ),
        "gospider": ToolSpec(
            name="gospider",
            capabilities={"content_discovery", "endpoint_discovery", "api_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "reconnaissance", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.30,
        ),
        "gau": ToolSpec(
            name="gau",
            capabilities={"historical_discovery", "endpoint_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "waybackurls": ToolSpec(
            name="waybackurls",
            capabilities={"historical_discovery", "endpoint_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "waymore": ToolSpec(
            name="waymore",
            capabilities={"historical_discovery", "endpoint_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "dirsearch": ToolSpec(
            name="dirsearch",
            capabilities={"content_discovery"},
            target_types={TargetType.WEB_APPLICATION.value},
            objectives={"comprehensive", "reconnaissance", "intelligence"},
            tech_affinities={TechnologyStack.PHP.value, TechnologyStack.DOTNET.value, TechnologyStack.JAVA.value},
            noise_score=0.35,
        ),
        "gobuster": ToolSpec(
            name="gobuster",
            capabilities={"content_discovery"},
            target_types={TargetType.WEB_APPLICATION.value},
            objectives={"quick", "comprehensive", "reconnaissance", "intelligence"},
            tech_affinities={TechnologyStack.PHP.value, TechnologyStack.DOTNET.value, TechnologyStack.JAVA.value},
            noise_score=0.45,
        ),
        "feroxbuster": ToolSpec(
            name="feroxbuster",
            capabilities={"content_discovery", "endpoint_discovery"},
            target_types={TargetType.WEB_APPLICATION.value},
            objectives={"comprehensive", "reconnaissance", "intelligence"},
            tech_affinities={TechnologyStack.PHP.value, TechnologyStack.DOTNET.value, TechnologyStack.JAVA.value},
            noise_score=0.38,
        ),
        "dirb": ToolSpec(
            name="dirb",
            capabilities={"content_discovery"},
            target_types={TargetType.WEB_APPLICATION.value},
            objectives={"quick", "comprehensive", "reconnaissance"},
            tech_affinities=set(),
            noise_score=0.48,
        ),
        "nuclei": ToolSpec(
            name="nuclei",
            capabilities={"vuln_scan", "web_vulnerability", "api_assessment"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value, TargetType.NETWORK_HOST.value},
            objectives={"quick", "comprehensive", "stealth", "vulnerability_hunting", "api_security", "intelligence"},
            tech_affinities={
                TechnologyStack.WORDPRESS.value,
                TechnologyStack.DRUPAL.value,
                TechnologyStack.JOOMLA.value,
                TechnologyStack.APACHE.value,
                TechnologyStack.NGINX.value,
            },
            noise_score=0.25,
        ),
        "nikto": ToolSpec(
            name="nikto",
            capabilities={"web_vulnerability"},
            target_types={TargetType.WEB_APPLICATION.value},
            objectives={"comprehensive", "vulnerability_hunting", "intelligence"},
            tech_affinities={TechnologyStack.PHP.value, TechnologyStack.APACHE.value},
            noise_score=0.65,
        ),
        "jaeles": ToolSpec(
            name="jaeles",
            capabilities={"web_vulnerability"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"comprehensive", "vulnerability_hunting", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.45,
        ),
        "wafw00f": ToolSpec(
            name="wafw00f",
            capabilities={"web_fingerprint"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "stealth", "reconnaissance", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.12,
        ),
        "testssl": ToolSpec(
            name="testssl",
            capabilities={"tls_assessment", "web_fingerprint"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "stealth", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.2,
        ),
        "wfuzz": ToolSpec(
            name="wfuzz",
            capabilities={"content_discovery", "param_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"comprehensive", "vulnerability_hunting", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.45,
        ),
        "burpsuite": ToolSpec(
            name="burpsuite",
            capabilities={"web_vulnerability", "api_assessment", "manual_validation"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"comprehensive", "vulnerability_hunting", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.42,
        ),
        "zaproxy": ToolSpec(
            name="zaproxy",
            capabilities={"web_vulnerability", "api_assessment"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"comprehensive", "vulnerability_hunting", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.46,
        ),
        "graphql-scanner": ToolSpec(
            name="graphql-scanner",
            capabilities={"api_discovery", "api_assessment"},
            target_types={TargetType.API_ENDPOINT.value},
            objectives={"comprehensive", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.24,
        ),
        "jwt-analyzer": ToolSpec(
            name="jwt-analyzer",
            capabilities={"api_assessment", "auth_assessment"},
            target_types={TargetType.API_ENDPOINT.value, TargetType.WEB_APPLICATION.value},
            objectives={"comprehensive", "api_security", "vulnerability_hunting", "intelligence"},
            tech_affinities=set(),
            noise_score=0.18,
        ),
        "api-schema-analyzer": ToolSpec(
            name="api-schema-analyzer",
            capabilities={"api_discovery", "api_assessment"},
            target_types={TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.14,
        ),
        "qsreplace": ToolSpec(
            name="qsreplace",
            capabilities={"param_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.08,
        ),
        "uro": ToolSpec(
            name="uro",
            capabilities={"historical_discovery", "endpoint_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.06,
        ),
        "anew": ToolSpec(
            name="anew",
            capabilities={"historical_discovery", "endpoint_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.05,
        ),
        "dalfox": ToolSpec(
            name="dalfox",
            capabilities={"xss_testing", "web_vulnerability"},
            target_types={TargetType.WEB_APPLICATION.value},
            objectives={"comprehensive", "vulnerability_hunting", "intelligence"},
            tech_affinities={TechnologyStack.REACT.value, TechnologyStack.ANGULAR.value, TechnologyStack.VUE.value},
            noise_score=0.5,
        ),
        "sqlmap": ToolSpec(
            name="sqlmap",
            capabilities={"sqli_testing", "web_vulnerability", "api_assessment"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"comprehensive", "vulnerability_hunting", "api_security", "intelligence"},
            tech_affinities={TechnologyStack.PHP.value, TechnologyStack.DOTNET.value},
            noise_score=0.7,
        ),
        "ffuf": ToolSpec(
            name="ffuf",
            capabilities={"content_discovery", "param_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "api_security", "vulnerability_hunting", "intelligence"},
            tech_affinities=set(),
            noise_score=0.4,
        ),
        "arjun": ToolSpec(
            name="arjun",
            capabilities={"param_discovery", "api_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.25,
        ),
        "paramspider": ToolSpec(
            name="paramspider",
            capabilities={"param_discovery", "historical_discovery"},
            target_types={TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "comprehensive", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.2,
        ),
        "x8": ToolSpec(
            name="x8",
            capabilities={"param_discovery", "api_assessment"},
            target_types={TargetType.API_ENDPOINT.value, TargetType.WEB_APPLICATION.value},
            objectives={"comprehensive", "api_security", "intelligence"},
            tech_affinities=set(),
            noise_score=0.35,
        ),
        "wpscan": ToolSpec(
            name="wpscan",
            capabilities={"cms_assessment", "web_vulnerability"},
            target_types={TargetType.WEB_APPLICATION.value},
            objectives={"quick", "comprehensive", "vulnerability_hunting", "intelligence"},
            tech_affinities={TechnologyStack.WORDPRESS.value},
            noise_score=0.3,
        ),
        "enum4linux-ng": ToolSpec(
            name="enum4linux-ng",
            capabilities={"smb_enum", "ad_enum"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"comprehensive", "internal_network_ad", "intelligence"},
            tech_affinities=set(),
            noise_score=0.5,
        ),
        "enum4linux": ToolSpec(
            name="enum4linux",
            capabilities={"smb_enum", "ad_enum"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"comprehensive", "internal_network_ad", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.55,
        ),
        "nbtscan": ToolSpec(
            name="nbtscan",
            capabilities={"smb_enum", "network_scan"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"quick", "comprehensive", "internal_network_ad", "reconnaissance", "intelligence"},
            tech_affinities=set(),
            noise_score=0.22,
        ),
        "smbmap": ToolSpec(
            name="smbmap",
            capabilities={"smb_enum"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"comprehensive", "internal_network_ad", "intelligence"},
            tech_affinities=set(),
            noise_score=0.4,
        ),
        "rpcclient": ToolSpec(
            name="rpcclient",
            capabilities={"ad_enum"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"comprehensive", "internal_network_ad", "intelligence"},
            tech_affinities=set(),
            noise_score=0.35,
        ),
        "netexec": ToolSpec(
            name="netexec",
            capabilities={"ad_enum", "auth_assessment"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"comprehensive", "internal_network_ad", "intelligence"},
            tech_affinities=set(),
            noise_score=0.45,
        ),
        "responder": ToolSpec(
            name="responder",
            capabilities={"credential_capture", "ad_enum"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"internal_network_ad"},
            tech_affinities=set(),
            noise_score=0.9,
        ),
        "amass": ToolSpec(
            name="amass",
            capabilities={"surface", "historical_discovery"},
            target_types={TargetType.NETWORK_HOST.value, TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"stealth", "reconnaissance", "comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.25,
        ),
        "subfinder": ToolSpec(
            name="subfinder",
            capabilities={"surface", "historical_discovery"},
            target_types={TargetType.NETWORK_HOST.value, TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "stealth", "reconnaissance", "comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.14,
        ),
        "assetfinder": ToolSpec(
            name="assetfinder",
            capabilities={"surface", "historical_discovery"},
            target_types={TargetType.NETWORK_HOST.value, TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "stealth", "reconnaissance", "comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.16,
        ),
        "shuffledns": ToolSpec(
            name="shuffledns",
            capabilities={"surface", "historical_discovery"},
            target_types={TargetType.NETWORK_HOST.value, TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "stealth", "reconnaissance", "comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.22,
        ),
        "massdns": ToolSpec(
            name="massdns",
            capabilities={"surface", "historical_discovery"},
            target_types={TargetType.NETWORK_HOST.value, TargetType.WEB_APPLICATION.value, TargetType.API_ENDPOINT.value},
            objectives={"quick", "stealth", "reconnaissance", "comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.20,
        ),
        "autorecon": ToolSpec(
            name="autorecon",
            capabilities={"network_scan", "service_enumeration"},
            target_types={TargetType.NETWORK_HOST.value},
            objectives={"comprehensive", "internal_network_ad", "intelligence"},
            tech_affinities=set(),
            noise_score=0.5,
        ),
        "kube-hunter": ToolSpec(
            name="kube-hunter",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.35,
        ),
        "checkov": ToolSpec(
            name="checkov",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.2,
        ),
        "trivy": ToolSpec(
            name="trivy",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.25,
        ),
        "scout-suite": ToolSpec(
            name="scout-suite",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.2,
        ),
        "cloudmapper": ToolSpec(
            name="cloudmapper",
            capabilities={"cloud_assessment", "surface"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.25,
        ),
        "pacu": ToolSpec(
            name="pacu",
            capabilities={"cloud_assessment", "auth_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.35,
        ),
        "clair": ToolSpec(
            name="clair",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.22,
        ),
        "kube-bench": ToolSpec(
            name="kube-bench",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.15,
        ),
        "docker-bench-security": ToolSpec(
            name="docker-bench-security",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.2,
        ),
        "falco": ToolSpec(
            name="falco",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.3,
        ),
        "terrascan": ToolSpec(
            name="terrascan",
            capabilities={"cloud_assessment"},
            target_types={TargetType.CLOUD_SERVICE.value},
            objectives={"comprehensive", "intelligence"},
            tech_affinities=set(),
            noise_score=0.18,
        ),
        "ghidra": ToolSpec(
            name="ghidra",
            capabilities={"binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "ropper": ToolSpec(
            name="ropper",
            capabilities={"binary_exploitation"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "pwntools": ToolSpec(
            name="pwntools",
            capabilities={"binary_exploitation"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "radare2": ToolSpec(
            name="radare2",
            capabilities={"binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"quick", "comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.08,
        ),
        "gdb": ToolSpec(
            name="gdb",
            capabilities={"binary_analysis", "binary_exploitation"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "gdb-peda": ToolSpec(
            name="gdb-peda",
            capabilities={"binary_analysis", "binary_exploitation"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.1,
        ),
        "ropgadget": ToolSpec(
            name="ropgadget",
            capabilities={"binary_exploitation"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.09,
        ),
        "one-gadget": ToolSpec(
            name="one-gadget",
            capabilities={"binary_exploitation"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.06,
        ),
        "libc-database": ToolSpec(
            name="libc-database",
            capabilities={"binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.08,
        ),
        "strings": ToolSpec(
            name="strings",
            capabilities={"binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"quick", "comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.05,
        ),
        "objdump": ToolSpec(
            name="objdump",
            capabilities={"binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"quick", "comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.06,
        ),
        "binwalk": ToolSpec(
            name="binwalk",
            capabilities={"binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"quick", "comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.08,
        ),
        "pwninit": ToolSpec(
            name="pwninit",
            capabilities={"binary_exploitation", "binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"quick", "comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.07,
        ),
        "checksec": ToolSpec(
            name="checksec",
            capabilities={"binary_analysis"},
            target_types={TargetType.BINARY_FILE.value},
            objectives={"quick", "comprehensive", "intelligence", "ctf"},
            tech_affinities=set(),
            noise_score=0.05,
        ),
    }


def validate_tool_catalog(catalog: Dict[str, ToolSpec]) -> List[str]:
    """Validate tool catalog entries and return a list of problems."""
    issues: List[str] = []
    known_targets = {target.value for target in TargetType}

    for key, spec in catalog.items():
        if spec.name != key:
            issues.append(f"{key}: spec.name must match catalog key")

        if not spec.capabilities:
            issues.append(f"{key}: capabilities cannot be empty")

        if not spec.target_types:
            issues.append(f"{key}: target_types cannot be empty")
        else:
            invalid_targets = sorted(list(spec.target_types - known_targets))
            if invalid_targets:
                issues.append(f"{key}: unknown target_types {invalid_targets}")

        if not spec.objectives:
            issues.append(f"{key}: objectives cannot be empty")

        if spec.noise_score < 0.0 or spec.noise_score > 1.0:
            issues.append(f"{key}: noise_score must be between 0.0 and 1.0")

    return issues


OBJECTIVE_CONFIG: Dict[str, Dict[str, float]] = {
    "quick": {"max_tools": 4, "noise_weight": 0.30, "cost_weight": 0.22, "min_score": 0.57},
    "comprehensive": {"max_tools": 8, "noise_weight": 0.10, "cost_weight": 0.08, "min_score": 0.50},
    "stealth": {"max_tools": 5, "noise_weight": 0.45, "cost_weight": 0.18, "min_score": 0.53},
    "reconnaissance": {"max_tools": 6, "noise_weight": 0.18, "cost_weight": 0.10, "min_score": 0.52},
    "vulnerability_hunting": {"max_tools": 6, "noise_weight": 0.20, "cost_weight": 0.10, "min_score": 0.54},
    "api_security": {"max_tools": 7, "noise_weight": 0.15, "cost_weight": 0.10, "min_score": 0.53},
    "internal_network_ad": {"max_tools": 8, "noise_weight": 0.14, "cost_weight": 0.08, "min_score": 0.51},
    "intelligence": {"max_tools": 8, "noise_weight": 0.12, "cost_weight": 0.08, "min_score": 0.51},
}


DEFAULT_OBJECTIVE = "comprehensive"


def objective_alias(objective: str) -> str:
    normalized = (objective or "").strip().lower()
    aliases = {
        "intelligence": "intelligence",
        "comprehensive": "comprehensive",
        "quick": "quick",
        "stealth": "stealth",
        "recon": "reconnaissance",
        "reconnaissance": "reconnaissance",
        "vulnerability": "vulnerability_hunting",
        "vulnerability_hunting": "vulnerability_hunting",
        "api_security": "api_security",
        "api": "api_security",
        "internal_network_ad": "internal_network_ad",
        "ad": "internal_network_ad",
    }
    return aliases.get(normalized, DEFAULT_OBJECTIVE)


def required_capabilities(target_type: str, objective: str) -> Set[str]:
    obj = objective_alias(objective)

    if obj == "api_security":
        return {"surface", "api_discovery", "param_discovery", "api_assessment"}
    if obj == "internal_network_ad":
        return {"network_scan", "smb_enum", "ad_enum"}
    if obj == "reconnaissance":
        if target_type == TargetType.NETWORK_HOST.value:
            return {"network_scan", "service_enumeration"}
        return {"surface", "content_discovery", "historical_discovery"}
    if obj == "vulnerability_hunting":
        if target_type == TargetType.API_ENDPOINT.value:
            return {"api_assessment", "param_discovery"}
        return {"web_vulnerability"}
    if obj == "quick":
        if target_type == TargetType.NETWORK_HOST.value:
            return {"network_scan"}
        if target_type == TargetType.API_ENDPOINT.value:
            return {"surface", "param_discovery"}
        if target_type == TargetType.BINARY_FILE.value:
            return {"binary_analysis"}
        if target_type == TargetType.CLOUD_SERVICE.value:
            return {"cloud_assessment"}
        return {"surface", "web_vulnerability"}
    if obj in {"comprehensive", "intelligence"}:
        if target_type == TargetType.NETWORK_HOST.value:
            return {"network_scan", "service_enumeration", "smb_enum"}
        if target_type == TargetType.API_ENDPOINT.value:
            return {"surface", "api_discovery", "param_discovery", "api_assessment"}
        if target_type == TargetType.BINARY_FILE.value:
            return {"binary_analysis", "binary_exploitation"}
        if target_type == TargetType.CLOUD_SERVICE.value:
            return {"cloud_assessment"}
        return {"surface", "content_discovery", "web_vulnerability"}
    if obj == "stealth":
        if target_type == TargetType.NETWORK_HOST.value:
            return {"network_scan"}
        if target_type == TargetType.API_ENDPOINT.value:
            return {"surface", "param_discovery"}
        return {"surface", "web_vulnerability"}

    return set()


def objective_settings(objective: str) -> Dict[str, float]:
    return OBJECTIVE_CONFIG.get(objective_alias(objective), OBJECTIVE_CONFIG[DEFAULT_OBJECTIVE]).copy()


def tech_values_from_profile(technologies: List[TechnologyStack]) -> Set[str]:
    return {tech.value for tech in technologies if tech != TechnologyStack.UNKNOWN}
