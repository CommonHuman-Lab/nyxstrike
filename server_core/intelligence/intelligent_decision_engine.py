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
from .tool_catalog import build_tool_catalog
from .tool_scoring import explain_selection_reason, rank_tools_precision_first

parameter_optimizer = ParameterOptimizer()
_tool_stats = ToolStatsStore()

CLOUD_DOMAIN_HINTS = (
    "amazonaws.com",
    "aws.amazon.com",
    "cloudfront.net",
    "azure.com",
    "azurewebsites.net",
    "windows.net",
    "googleapis.com",
    "gcp.",
)


class IntelligentDecisionEngine(LegacyParameterOptimizers):
    """AI-powered tool selection and parameter optimization engine."""

    def __init__(self):
        self.tool_effectiveness = self._initialize_tool_effectiveness()
        self.technology_signatures = self._initialize_technology_signatures()
        self.attack_patterns = self._initialize_attack_patterns()
        self.tool_catalog = build_tool_catalog()
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

        if profile.target_type == TargetType.CLOUD_SERVICE:
            profile.cloud_provider = self._detect_cloud_provider(target)

        profile.attack_surface_score = self._calculate_attack_surface(profile)
        profile.risk_level = self._determine_risk_level(profile)
        profile.confidence_score = self._calculate_confidence(profile)
        return profile

    def _determine_target_type(self, target: str) -> TargetType:
        """Determine the type of target for appropriate tool selection."""
        target_lower = target.lower()
        parsed = urllib.parse.urlparse(target) if target.startswith(("http://", "https://")) else None

        domain_hint = target_lower
        if parsed and parsed.hostname:
            domain_hint = parsed.hostname.lower()

        if any(cloud in domain_hint for cloud in CLOUD_DOMAIN_HINTS):
            return TargetType.CLOUD_SERVICE

        if target_lower.endswith((".exe", ".bin", ".elf", ".so", ".dll")):
            return TargetType.BINARY_FILE

        if parsed:
            if "/api/" in parsed.path or parsed.path.endswith("/api"):
                return TargetType.API_ENDPOINT
            return TargetType.WEB_APPLICATION

        if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", target):
            return TargetType.NETWORK_HOST

        if re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target):
            return TargetType.WEB_APPLICATION

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

    def _detect_cloud_provider(self, target: str) -> Optional[str]:
        """Detect cloud provider from target string."""
        target_lower = target.lower()
        if any(hint in target_lower for hint in ("amazonaws.com", "aws.amazon.com", "cloudfront.net", "aws")):
            return "aws"
        if any(hint in target_lower for hint in ("azure.com", "azurewebsites.net", "windows.net", "azure")):
            return "azure"
        if any(hint in target_lower for hint in ("googleapis.com", "gcp", "google")):
            return "gcp"
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

    def _build_context_key(self, profile: TargetProfile, objective: str) -> str:
        """Build context key for contextual effectiveness scoring."""
        primary_tech = "none"
        for tech in profile.technologies:
            if tech != TechnologyStack.UNKNOWN:
                primary_tech = tech.value
                break

        objective_norm = (objective or "comprehensive").strip().lower()
        return f"{profile.target_type.value}|{objective_norm}|{primary_tech}"

    def _effective_score(self, tool: str, target_type_value: str, context_key: Optional[str] = None) -> float:
        """Return best available effectiveness score for a tool."""
        baseline = self.tool_effectiveness.get(target_type_value, {}).get(tool, 0.5)
        if context_key:
            return _tool_stats.blended_effectiveness_contextual(tool, baseline, context_key)
        return _tool_stats.blended_effectiveness(tool, baseline)

    def select_optimal_tools(self, profile: TargetProfile, objective: str = "comprehensive") -> List[str]:
        """Select optimal tools based on profile with precision-first ranking."""
        selected_tools = rank_tools_precision_first(
            profile=profile,
            objective=objective,
            tool_effectiveness=self.tool_effectiveness,
            catalog=self.tool_catalog,
            effective_score_fn=lambda tool, target_type_value: self._effective_score(
                tool,
                target_type_value,
                self._build_context_key(profile, objective),
            ),
        )

        if not selected_tools:
            target_type = profile.target_type.value
            effectiveness_map = self.tool_effectiveness.get(target_type, {})
            fallback = sorted(effectiveness_map.keys(), key=lambda t: self._effective_score(t, target_type), reverse=True)
            selected_tools = fallback[:8]

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

    def create_attack_chain(
        self,
        profile: TargetProfile,
        objective: str = "comprehensive",
        runtime_context: Optional[Dict[str, Any]] = None,
    ) -> AttackChain:
        """Create an intelligent attack chain based on target profile."""
        chain = AttackChain(profile)
        if runtime_context is None:
            runtime_context = {}

        objective_overrides = {
            "api_security": "api_testing",
            "internal_network_ad": "internal_network_ad_assessment",
        }
        override_pattern = objective_overrides.get(objective)
        if override_pattern:
            pattern = self.attack_patterns[override_pattern]
        else:
            pattern = self._select_attack_pattern(profile, objective)

        ranked_tools = self.select_optimal_tools(profile, objective)
        ranked_set = set(ranked_tools)

        pattern_tools = [step["tool"] for step in pattern]
        if ranked_tools:
            ordered_tools = [tool for tool in ranked_tools if tool in pattern_tools]
            ordered_tools.extend([tool for tool in ranked_tools if tool not in ordered_tools])
            if not ordered_tools:
                ordered_tools = pattern_tools
        else:
            ordered_tools = pattern_tools

        context_key = self._build_context_key(profile, objective)
        tool_overrides = runtime_context.get("tool_overrides", {}) if isinstance(runtime_context, dict) else {}
        required_caps = self._required_capabilities_for(profile, objective)
        selected_caps_so_far: set = set()

        for tool in ordered_tools:
            if ranked_set and tool not in ranked_set and tool not in pattern_tools:
                continue
            step_defaults = next((step.get("params", {}) for step in pattern if step.get("tool") == tool), {})
            if not isinstance(step_defaults, dict):
                step_defaults = {}
            runtime_override = tool_overrides.get(tool, {}) if isinstance(tool_overrides, dict) else {}
            if not isinstance(runtime_override, dict):
                runtime_override = {}

            merged_context = {
                "objective": objective,
                "target_type": profile.target_type.value,
                "risk_level": profile.risk_level,
                "optimization_profile": "stealth" if objective == "stealth" else "normal",
                "technologies": [tech.value for tech in profile.technologies if tech != TechnologyStack.UNKNOWN],
                "cloud_provider": profile.cloud_provider,
            }
            merged_context.update(step_defaults)
            merged_context.update(runtime_override)

            optimizer_params = self.optimize_parameters(tool, profile, merged_context)

            final_params = {}
            final_params.update(step_defaults)
            final_params.update(optimizer_params)
            final_params.update(runtime_override)

            effectiveness = self._effective_score(tool, profile.target_type.value, context_key)
            success_prob = effectiveness * profile.confidence_score
            exec_time = TIME_ESTIMATES.get(tool, 180)
            reason = explain_selection_reason(
                tool=tool,
                profile=profile,
                objective=objective,
                catalog=self.tool_catalog,
                required=required_caps,
                effective_score=effectiveness,
                selected_capabilities=selected_caps_so_far,
            )

            spec = self.tool_catalog.get(tool)
            if spec:
                selected_caps_so_far.update(spec.capabilities)

            chain.add_step(
                AttackStep(
                    tool=tool,
                    parameters=final_params,
                    expected_outcome=f"Discover vulnerabilities using {tool}",
                    success_probability=success_prob,
                    execution_time_estimate=exec_time,
                    selection_reason=reason,
                )
            )

        chain.calculate_success_probability()
        chain.risk_level = profile.risk_level
        return chain

    def _required_capabilities_for(self, profile: TargetProfile, objective: str) -> set:
        from .tool_catalog import required_capabilities

        return required_capabilities(profile.target_type.value, objective)

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
