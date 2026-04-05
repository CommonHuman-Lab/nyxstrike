import re
import socket
import urllib.parse
from typing import Any, Dict, List, Optional

from shared.attack_chain import AttackChain, AttackStep
from shared.target_profile import TargetProfile
from shared.target_types import TargetType, TechnologyStack
from server_core.parameter_optimizer import ParameterOptimizer
from server_core.tool_stats_store import ToolStatsStore

from .decision_engine_constants import (
    TIME_ESTIMATES,
    initialize_attack_patterns,
    initialize_technology_signatures,
    initialize_tool_effectiveness,
)
from .decision_engine_legacy_optimizers import LegacyParameterOptimizers

parameter_optimizer = ParameterOptimizer()
_tool_stats = ToolStatsStore()


class IntelligentDecisionEngine(LegacyParameterOptimizers):
    """AI-powered tool selection and parameter optimization engine."""

    def __init__(self):
        self.tool_effectiveness = self._initialize_tool_effectiveness()
        self.technology_signatures = self._initialize_technology_signatures()
        self.attack_patterns = self._initialize_attack_patterns()
        self._use_advanced_optimizer = True

    def _initialize_tool_effectiveness(self) -> Dict[str, Dict[str, float]]:
        """Initialize tool effectiveness ratings for different target types."""
        return initialize_tool_effectiveness()

    def _initialize_technology_signatures(self) -> Dict[str, Dict[str, Any]]:
        """Initialize technology detection signatures."""
        return initialize_technology_signatures()

    def _initialize_attack_patterns(self) -> Dict[str, List[Dict[str, Any]]]:
        """Initialize common attack patterns for different scenarios."""
        return initialize_attack_patterns()

    def analyze_target(self, target: str) -> TargetProfile:
        """Analyze target and create comprehensive profile."""
        profile = TargetProfile(target=target)
        profile.target_type = self._determine_target_type(target)

        if profile.target_type in [TargetType.WEB_APPLICATION, TargetType.API_ENDPOINT]:
            profile.ip_addresses = self._resolve_domain(target)

        if profile.target_type == TargetType.WEB_APPLICATION:
            profile.technologies = self._detect_technologies(target)
            profile.cms_type = self._detect_cms(target)

        profile.attack_surface_score = self._calculate_attack_surface(profile)
        profile.risk_level = self._determine_risk_level(profile)
        profile.confidence_score = self._calculate_confidence(profile)
        return profile

    def _determine_target_type(self, target: str) -> TargetType:
        """Determine the type of target for appropriate tool selection."""
        if target.startswith(("http://", "https://")):
            parsed = urllib.parse.urlparse(target)
            if "/api/" in parsed.path or parsed.path.endswith("/api"):
                return TargetType.API_ENDPOINT
            return TargetType.WEB_APPLICATION

        if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", target):
            return TargetType.NETWORK_HOST

        if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target):
            return TargetType.WEB_APPLICATION

        if target.endswith((".exe", ".bin", ".elf", ".so", ".dll")):
            return TargetType.BINARY_FILE

        if any(cloud in target.lower() for cloud in ["amazonaws.com", "azure", "googleapis.com"]):
            return TargetType.CLOUD_SERVICE

        return TargetType.UNKNOWN

    def _resolve_domain(self, target: str) -> List[str]:
        """Resolve domain to IP addresses."""
        try:
            if target.startswith(("http://", "https://")):
                hostname = urllib.parse.urlparse(target).hostname
            else:
                hostname = target

            if hostname:
                return [socket.gethostbyname(hostname)]
        except Exception:
            pass
        return []

    def _detect_technologies(self, target: str) -> List[TechnologyStack]:
        """Detect technologies using basic heuristics."""
        technologies = []

        if "wordpress" in target.lower() or "wp-" in target.lower():
            technologies.append(TechnologyStack.WORDPRESS)
        if any(ext in target.lower() for ext in [".php", "php"]):
            technologies.append(TechnologyStack.PHP)
        if any(ext in target.lower() for ext in [".asp", ".aspx"]):
            technologies.append(TechnologyStack.DOTNET)

        return technologies if technologies else [TechnologyStack.UNKNOWN]

    def _detect_cms(self, target: str) -> Optional[str]:
        """Detect CMS type."""
        target_lower = target.lower()
        if "wordpress" in target_lower or "wp-" in target_lower:
            return "WordPress"
        if "drupal" in target_lower:
            return "Drupal"
        if "joomla" in target_lower:
            return "Joomla"
        return None

    def _calculate_attack_surface(self, profile: TargetProfile) -> float:
        """Calculate attack surface score based on profile."""
        type_scores = {
            TargetType.WEB_APPLICATION: 7.0,
            TargetType.API_ENDPOINT: 6.0,
            TargetType.NETWORK_HOST: 8.0,
            TargetType.CLOUD_SERVICE: 5.0,
            TargetType.BINARY_FILE: 4.0,
        }

        score = type_scores.get(profile.target_type, 3.0)
        score += len(profile.technologies) * 0.5
        score += len(profile.open_ports) * 0.3
        score += len(profile.subdomains) * 0.2
        if profile.cms_type:
            score += 1.5
        return min(score, 10.0)

    def _determine_risk_level(self, profile: TargetProfile) -> str:
        """Determine risk level based on attack surface."""
        if profile.attack_surface_score >= 8.0:
            return "critical"
        if profile.attack_surface_score >= 6.0:
            return "high"
        if profile.attack_surface_score >= 4.0:
            return "medium"
        if profile.attack_surface_score >= 2.0:
            return "low"
        return "minimal"

    def _calculate_confidence(self, profile: TargetProfile) -> float:
        """Calculate confidence score in the analysis."""
        confidence = 0.5
        if profile.ip_addresses:
            confidence += 0.1
        if profile.technologies and profile.technologies[0] != TechnologyStack.UNKNOWN:
            confidence += 0.2
        if profile.cms_type:
            confidence += 0.1
        if profile.target_type != TargetType.UNKNOWN:
            confidence += 0.1
        return min(confidence, 1.0)

    def _effective_score(self, tool: str, target_type_value: str) -> float:
        """Return best available effectiveness score for a tool."""
        baseline = self.tool_effectiveness.get(target_type_value, {}).get(tool, 0.5)
        return _tool_stats.blended_effectiveness(tool, baseline)

    def select_optimal_tools(self, profile: TargetProfile, objective: str = "comprehensive") -> List[str]:
        """Select optimal tools based on target profile and objective."""
        target_type = profile.target_type.value
        effectiveness_map = self.tool_effectiveness.get(target_type, {})
        base_tools = list(effectiveness_map.keys())

        if objective == "quick":
            sorted_tools = sorted(base_tools, key=lambda t: self._effective_score(t, target_type), reverse=True)
            selected_tools = sorted_tools[:3]
        elif objective == "comprehensive":
            selected_tools = [tool for tool in base_tools if self._effective_score(tool, target_type) > 0.7]
        elif objective == "stealth":
            stealth_tools = ["amass", "subfinder", "httpx", "nuclei"]
            selected_tools = [tool for tool in base_tools if tool in stealth_tools]
        else:
            selected_tools = base_tools

        for tech in profile.technologies:
            if tech == TechnologyStack.WORDPRESS and "wpscan" not in selected_tools:
                selected_tools.append("wpscan")
            elif tech == TechnologyStack.PHP and "nikto" not in selected_tools:
                selected_tools.append("nikto")

        return selected_tools

    def optimize_parameters(
        self,
        tool: str,
        profile: TargetProfile,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Enhanced parameter optimization with advanced intelligence."""
        if context is None:
            context = {}

        if hasattr(self, "_use_advanced_optimizer") and self._use_advanced_optimizer:
            return parameter_optimizer.optimize_parameters_advanced(tool, profile, context)

        if tool == "nmap":
            return self._optimize_nmap_params(profile, context)
        if tool == "gobuster":
            return self._optimize_gobuster_params(profile, context)
        if tool == "nuclei":
            return self._optimize_nuclei_params(profile, context)
        if tool == "sqlmap":
            return self._optimize_sqlmap_params(profile, context)
        if tool == "ffuf":
            return self._optimize_ffuf_params(profile, context)
        if tool == "hydra":
            return self._optimize_hydra_params(profile, context)
        if tool == "rustscan":
            return self._optimize_rustscan_params(profile, context)
        if tool == "masscan":
            return self._optimize_masscan_params(profile, context)
        if tool == "nmap_advanced":
            return self._optimize_nmap_advanced_params(profile, context)
        if tool == "enum4linux-ng":
            return self._optimize_enum4linux_ng_params(profile, context)
        if tool == "autorecon":
            return self._optimize_autorecon_params(profile, context)
        if tool == "ghidra":
            return self._optimize_ghidra_params(profile, context)
        if tool == "pwntools":
            return self._optimize_pwntools_params(profile, context)
        if tool == "ropper":
            return self._optimize_ropper_params(profile, context)
        if tool == "angr":
            return self._optimize_angr_params(profile, context)
        if tool == "prowler":
            return self._optimize_prowler_params(profile, context)
        if tool == "scout-suite":
            return self._optimize_scout_suite_params(profile, context)
        if tool == "kube-hunter":
            return self._optimize_kube_hunter_params(profile, context)
        if tool == "trivy":
            return self._optimize_trivy_params(profile, context)
        if tool == "checkov":
            return self._optimize_checkov_params(profile, context)

        return parameter_optimizer.optimize_parameters_advanced(tool, profile, context)

    def enable_advanced_optimization(self):
        """Enable advanced parameter optimization."""
        self._use_advanced_optimizer = True

    def disable_advanced_optimization(self):
        """Disable advanced parameter optimization and use legacy mode."""
        self._use_advanced_optimizer = False

    def create_attack_chain(self, profile: TargetProfile, objective: str = "comprehensive") -> AttackChain:
        """Create an intelligent attack chain based on target profile."""
        chain = AttackChain(profile)

        objective_overrides = {
            "api_security": "api_testing",
            "internal_network_ad": "internal_network_ad_assessment",
        }
        override_pattern = objective_overrides.get(objective)
        if override_pattern:
            pattern = self.attack_patterns[override_pattern]
        else:
            pattern = self._select_attack_pattern(profile, objective)

        for step_config in pattern:
            tool = step_config["tool"]
            optimized_params = self.optimize_parameters(tool, profile)
            effectiveness = self._effective_score(tool, profile.target_type.value)
            success_prob = effectiveness * profile.confidence_score
            exec_time = TIME_ESTIMATES.get(tool, 180)

            chain.add_step(
                AttackStep(
                    tool=tool,
                    parameters=optimized_params,
                    expected_outcome=f"Discover vulnerabilities using {tool}",
                    success_probability=success_prob,
                    execution_time_estimate=exec_time,
                )
            )

        chain.calculate_success_probability()
        chain.risk_level = profile.risk_level
        return chain

    def _select_attack_pattern(self, profile: TargetProfile, objective: str) -> List[Dict[str, Any]]:
        if profile.target_type == TargetType.WEB_APPLICATION:
            if objective == "quick":
                return self.attack_patterns["vulnerability_assessment"][:2]
            return self.attack_patterns["web_reconnaissance"] + self.attack_patterns["vulnerability_assessment"]

        if profile.target_type == TargetType.API_ENDPOINT:
            return self.attack_patterns["api_testing"]

        if profile.target_type == TargetType.NETWORK_HOST:
            if objective == "comprehensive":
                return self.attack_patterns["comprehensive_network_pentest"]
            return self.attack_patterns["network_discovery"]

        if profile.target_type == TargetType.BINARY_FILE:
            if objective == "ctf":
                return self.attack_patterns["ctf_pwn_challenge"]
            return self.attack_patterns["binary_exploitation"]

        if profile.target_type == TargetType.CLOUD_SERVICE:
            cloud_objectives = {
                "aws": "aws_security_assessment",
                "kubernetes": "kubernetes_security_assessment",
                "containers": "container_security_assessment",
                "iac": "iac_security_assessment",
            }
            return self.attack_patterns[cloud_objectives.get(objective, "multi_cloud_assessment")]

        bug_bounty_objectives = {
            "bug_bounty_recon": "bug_bounty_reconnaissance",
            "bug_bounty_hunting": "bug_bounty_vulnerability_hunting",
            "bug_bounty_high_impact": "bug_bounty_high_impact",
        }
        return self.attack_patterns[bug_bounty_objectives.get(objective, "web_reconnaissance")]
