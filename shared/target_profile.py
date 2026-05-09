from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from shared.target_types import TargetType, TechnologyStack

@dataclass
class TargetProfile:
    """Comprehensive target analysis profile for intelligent decision making"""
    target: Any
    target_type: TargetType = TargetType.UNKNOWN
    ip_addresses: List[str] = field(default_factory=list)
    open_ports: List[int] = field(default_factory=list)
    services: Dict[int, str] = field(default_factory=dict)
    technologies: List[TechnologyStack] = field(default_factory=list)
    cms_type: Optional[str] = None
    cloud_provider: Optional[str] = None
    security_headers: Dict[str, str] = field(default_factory=dict)
    ssl_info: Dict[str, Any] = field(default_factory=dict)
    subdomains: List[str] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    attack_surface_score: float = 0.0
    risk_level: str = "unknown"
    confidence_score: float = 0.0
    # CVE / exploit intelligence fields
    cve_ids: List[str] = field(default_factory=list)
    service_versions: Dict[str, str] = field(default_factory=dict)
    known_vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    exploit_candidates: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert TargetProfile to dictionary for JSON serialization"""
        return {
            "target": self.target,
            "target_type": self.target_type.value,
            "ip_addresses": self.ip_addresses,
            "open_ports": self.open_ports,
            "services": self.services,
            "technologies": [tech.value for tech in self.technologies],
            "cms_type": self.cms_type,
            "cloud_provider": self.cloud_provider,
            "security_headers": self.security_headers,
            "ssl_info": self.ssl_info,
            "subdomains": self.subdomains,
            "endpoints": self.endpoints,
            "attack_surface_score": self.attack_surface_score,
            "risk_level": self.risk_level,
            "confidence_score": self.confidence_score,
            "cve_ids": self.cve_ids,
            "service_versions": self.service_versions,
            "known_vulnerabilities": self.known_vulnerabilities,
            "exploit_candidates": self.exploit_candidates,
        }
