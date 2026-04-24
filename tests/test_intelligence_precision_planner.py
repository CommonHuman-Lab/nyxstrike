from server_core.intelligence.tool_catalog import build_tool_catalog, validate_tool_catalog
from server_core.singletons import decision_engine


def _tools_for(target: str, objective: str):
    profile = decision_engine.analyze_target(target)
    return decision_engine.select_optimal_tools(profile, objective), profile


def test_catalog_validation_passes():
    catalog = build_tool_catalog()
    issues = validate_tool_catalog(catalog)
    assert issues == []


def test_quick_mode_precision_is_compact():
    tools, _profile = _tools_for("https://example.com", "quick")
    assert 1 <= len(tools) <= 4


def test_comprehensive_mode_allows_safer_coverage_tool_count():
    tools, _profile = _tools_for("https://example.com", "comprehensive")
    assert len(tools) <= 8
    assert len(tools) >= 5


def test_api_security_prefers_api_capabilities():
    tools, _profile = _tools_for("https://example.com/api", "api_security")
    lowered = set(tools)
    assert "arjun" in lowered or "x8" in lowered or "paramspider" in lowered
    assert "httpx" in lowered or "nuclei" in lowered or "api-schema-analyzer" in lowered


def test_network_quick_prefers_network_scanners():
    tools, _profile = _tools_for("10.10.10.10", "quick")
    lowered = set(tools)
    assert "nmap" in lowered or "nmap_advanced" in lowered or "rustscan" in lowered


def test_cloud_domain_classification_and_selection():
    tools, profile = _tools_for("https://aws.amazon.com", "comprehensive")
    assert profile.target_type.value == "cloud_service"
    lowered = set(tools)
    assert "checkov" in lowered or "trivy" in lowered or "scout-suite" in lowered


def test_create_attack_chain_respects_runtime_overrides():
    profile = decision_engine.analyze_target("https://example.com/api")
    # Pick whatever tool the planner actually selects first for this objective,
    # then assert the override is applied to it.
    tools = decision_engine.select_optimal_tools(profile, "api_security")
    assert tools, "Expected at least one tool for api_security objective"
    first_tool = tools[0]

    chain = decision_engine.create_attack_chain(
        profile,
        objective="api_security",
        runtime_context={
            "tool_overrides": {
                first_tool: {"_test_override_marker": "sentinel_value"},
            }
        },
    )

    matching_steps = [step for step in chain.steps if step.tool == first_tool]
    assert matching_steps, f"{first_tool} should appear in api_security attack chain"
    assert matching_steps[0].parameters.get("_test_override_marker") == "sentinel_value", (
        f"runtime override was not applied to {first_tool} step"
    )


def test_planner_mode_switch_per_call_supports_legacy_and_advanced():
    profile = decision_engine.analyze_target("https://example.com")
    advanced_tools = decision_engine.select_optimal_tools(profile, "comprehensive", planner_mode="advanced")
    legacy_tools = decision_engine.select_optimal_tools(profile, "comprehensive", planner_mode="legacy")

    assert advanced_tools
    assert legacy_tools
    assert len(advanced_tools) <= 8
    assert len(legacy_tools) <= 8
    # The two planners must produce different selections — if they're identical
    # the mode-switch has no effect and the test is vacuous.
    assert set(advanced_tools) != set(legacy_tools), (
        "advanced and legacy planners returned identical tool sets — "
        "mode switching appears to have no effect"
    )


def test_planner_mode_switch_global_toggle():
    original_mode = decision_engine.get_planner_mode()
    try:
        decision_engine.enable_legacy_planner()
        assert decision_engine.get_planner_mode() == "legacy"

        profile = decision_engine.analyze_target("https://example.com/api")
        selected_tools = decision_engine.select_optimal_tools(profile, "api_security")
        assert selected_tools

        decision_engine.enable_advanced_planner()
        assert decision_engine.get_planner_mode() == "advanced"
    finally:
        decision_engine.set_planner_mode(original_mode)
