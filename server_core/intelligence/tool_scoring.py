from typing import Dict, List, Optional, Set, Tuple

from shared.target_profile import TargetProfile

from .decision_engine_constants import TIME_ESTIMATES
from .tool_catalog import ToolSpec, objective_alias, objective_settings, required_capabilities, tech_values_from_profile


def rank_tools_precision_first(
    profile: TargetProfile,
    objective: str,
    tool_effectiveness: Dict[str, Dict[str, float]],
    catalog: Dict[str, ToolSpec],
    effective_score_fn,
) -> List[str]:
    """Rank tools with precision-first weighting and capability coverage constraints."""
    target_type_value = profile.target_type.value
    normalized_objective = objective_alias(objective)
    settings = objective_settings(normalized_objective)
    required = required_capabilities(target_type_value, normalized_objective)
    tech_values = tech_values_from_profile(profile.technologies)

    candidates: List[Tuple[str, float, ToolSpec, Set[str], float]] = []
    effectiveness_map = tool_effectiveness.get(target_type_value, {})
    for tool in effectiveness_map.keys():
        spec = catalog.get(tool)
        if not spec:
            continue
        if target_type_value not in spec.target_types:
            continue

        base = effective_score_fn(tool, target_type_value)
        score = _score_tool(
            tool=tool,
            base=base,
            spec=spec,
            objective=normalized_objective,
            tech_values=tech_values,
            noise_weight=settings["noise_weight"],
            cost_weight=settings["cost_weight"],
        )
        if score < settings["min_score"]:
            continue

        coverage = spec.capabilities & required
        candidates.append((tool, score, spec, coverage, base))

    if not candidates:
        return []

    selected: List[str] = []
    selected_caps: Set[str] = set()
    selected_groups: Set[str] = set()

    candidates.sort(key=lambda row: row[1], reverse=True)

    while len(selected) < int(settings["max_tools"]) and candidates:
        best_idx: Optional[int] = None
        best_value = -1.0

        for idx, (tool, score, spec, coverage, _base) in enumerate(candidates):
            marginal_cov = len(coverage - selected_caps)
            redundancy_penalty = 0.0
            dominant_group = _dominant_capability_group(spec.capabilities)
            if dominant_group in selected_groups:
                redundancy_penalty = 0.04

            value = score + (0.08 * marginal_cov) - redundancy_penalty
            if value > best_value:
                best_value = value
                best_idx = idx

        if best_idx is None:
            break

        tool, _score, spec, _coverage, _base = candidates.pop(best_idx)
        selected.append(tool)
        selected_caps.update(spec.capabilities)
        selected_groups.add(_dominant_capability_group(spec.capabilities))

        if selected_caps >= required and len(selected) >= _minimum_selected_for_objective(normalized_objective):
            if normalized_objective != "comprehensive":
                break

    if not required.issubset(selected_caps):
        missing = required - selected_caps
        for tool, _score, spec, _coverage, _base in candidates:
            if len(selected) >= int(settings["max_tools"]):
                break
            if spec.capabilities & missing:
                selected.append(tool)
                selected_caps.update(spec.capabilities)
                missing = required - selected_caps
            if not missing:
                break

    return selected[: int(settings["max_tools"])]


def explain_selection_reason(
    tool: str,
    profile: TargetProfile,
    objective: str,
    catalog: Dict[str, ToolSpec],
    required: Optional[Set[str]] = None,
    effective_score: Optional[float] = None,
    selected_capabilities: Optional[Set[str]] = None,
) -> Dict[str, object]:
    """Build human-readable and machine-readable rationale for tool selection."""
    spec = catalog.get(tool)
    if not spec:
        return {
            "summary": f"Selected {tool} as fallback due to ranking availability.",
            "objective_match": False,
            "target_type_match": False,
            "capabilities": [],
            "covers_required": [],
            "new_capabilities_added": [],
            "effective_score": effective_score,
        }

    normalized_objective = objective_alias(objective)
    required_caps = required or required_capabilities(profile.target_type.value, normalized_objective)
    selected_so_far = selected_capabilities or set()
    covers_required = sorted(list(spec.capabilities & required_caps))
    newly_added = sorted(list((spec.capabilities & required_caps) - selected_so_far))

    objective_match = normalized_objective in spec.objectives
    target_type_match = profile.target_type.value in spec.target_types
    summary_parts = [f"Selected {tool}"]
    if newly_added:
        summary_parts.append(f"to add required coverage ({', '.join(newly_added)})")
    elif covers_required:
        summary_parts.append(f"for required capability fit ({', '.join(covers_required)})")
    else:
        summary_parts.append("for strong precision score")
    if objective_match:
        summary_parts.append(f"and objective match ({normalized_objective})")

    return {
        "summary": " ".join(summary_parts) + ".",
        "objective": normalized_objective,
        "objective_match": objective_match,
        "target_type": profile.target_type.value,
        "target_type_match": target_type_match,
        "capabilities": sorted(list(spec.capabilities)),
        "covers_required": covers_required,
        "new_capabilities_added": newly_added,
        "noise_score": spec.noise_score,
        "effective_score": effective_score,
    }


def _score_tool(
    tool: str,
    base: float,
    spec: ToolSpec,
    objective: str,
    tech_values: Set[str],
    noise_weight: float,
    cost_weight: float,
) -> float:
    objective_bonus = 0.12 if objective in spec.objectives else -0.05
    tech_bonus = 0.0
    if spec.tech_affinities:
        overlap = len(spec.tech_affinities & tech_values)
        if overlap:
            tech_bonus = min(0.12, overlap * 0.06)

    time_est = TIME_ESTIMATES.get(tool, 180)
    cost_penalty = min(0.16, (time_est / 1200.0) * cost_weight)
    noise_penalty = spec.noise_score * noise_weight

    return max(0.0, min(1.0, base + objective_bonus + tech_bonus - noise_penalty - cost_penalty))


def _dominant_capability_group(capabilities: Set[str]) -> str:
    if "web_vulnerability" in capabilities or "api_assessment" in capabilities:
        return "vuln"
    if "content_discovery" in capabilities or "endpoint_discovery" in capabilities:
        return "discovery"
    if "network_scan" in capabilities or "service_enumeration" in capabilities:
        return "network"
    if "smb_enum" in capabilities or "ad_enum" in capabilities:
        return "ad"
    if "binary_analysis" in capabilities or "binary_exploitation" in capabilities:
        return "binary"
    if "cloud_assessment" in capabilities:
        return "cloud"
    return "misc"


def _minimum_selected_for_objective(objective: str) -> int:
    if objective == "quick":
        return 3
    if objective == "stealth":
        return 3
    if objective == "comprehensive":
        return 6
    return 4
