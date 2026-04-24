"""
tests/test_tool_catalog.py

Pure-Python unit tests for the standalone functions in
server_core/intelligence/tool_catalog.py.

No subprocess, no Flask, no server calls.
"""

import pytest

from server_core.intelligence.tool_catalog import (
    build_tool_catalog,
    objective_alias,
    objective_settings,
    required_capabilities,
    tech_values_from_profile,
    validate_tool_catalog,
    DEFAULT_OBJECTIVE,
)
from shared.target_types import TargetType, TechnologyStack


# ---------------------------------------------------------------------------
# objective_alias
# ---------------------------------------------------------------------------

class TestObjectiveAlias:
    @pytest.mark.parametrize("raw,expected", [
        ("recon",              "reconnaissance"),
        ("reconnaissance",     "reconnaissance"),
        ("vulnerability",      "vulnerability_hunting"),
        ("vulnerability_hunting", "vulnerability_hunting"),
        ("api",                "api_security"),
        ("api_security",       "api_security"),
        ("ad",                 "internal_network_ad"),
        ("internal_network_ad","internal_network_ad"),
        ("comprehensive",      "comprehensive"),
        ("quick",              "quick"),
        ("stealth",            "stealth"),
        ("intelligence",       "intelligence"),
    ])
    def test_known_alias(self, raw, expected):
        assert objective_alias(raw) == expected

    def test_unknown_alias_returns_default(self):
        assert objective_alias("totally_unknown") == DEFAULT_OBJECTIVE

    def test_empty_string_returns_default(self):
        assert objective_alias("") == DEFAULT_OBJECTIVE

    def test_whitespace_is_stripped(self):
        assert objective_alias("  recon  ") == "reconnaissance"

    def test_case_insensitive(self):
        assert objective_alias("RECON") == "reconnaissance"
        assert objective_alias("Api") == "api_security"


# ---------------------------------------------------------------------------
# required_capabilities
# ---------------------------------------------------------------------------

class TestRequiredCapabilities:
    def test_api_security_always_includes_api_discovery(self):
        caps = required_capabilities(TargetType.WEB_APPLICATION.value, "api_security")
        assert "api_discovery" in caps
        assert "param_discovery" in caps

    def test_internal_network_ad_includes_smb_and_ad(self):
        caps = required_capabilities(TargetType.NETWORK_HOST.value, "internal_network_ad")
        assert "smb_enum" in caps
        assert "ad_enum" in caps

    def test_quick_network_host_is_network_scan_only(self):
        caps = required_capabilities(TargetType.NETWORK_HOST.value, "quick")
        assert caps == {"network_scan"}

    def test_quick_binary_file_is_binary_analysis(self):
        caps = required_capabilities(TargetType.BINARY_FILE.value, "quick")
        assert "binary_analysis" in caps

    def test_quick_cloud_service_is_cloud_assessment(self):
        caps = required_capabilities(TargetType.CLOUD_SERVICE.value, "quick")
        assert "cloud_assessment" in caps

    def test_comprehensive_network_host_includes_smb(self):
        caps = required_capabilities(TargetType.NETWORK_HOST.value, "comprehensive")
        assert "smb_enum" in caps
        assert "network_scan" in caps

    def test_comprehensive_web_app_includes_surface_and_vuln(self):
        caps = required_capabilities(TargetType.WEB_APPLICATION.value, "comprehensive")
        assert "surface" in caps
        assert "web_vulnerability" in caps

    def test_reconnaissance_network_host_includes_service_enum(self):
        caps = required_capabilities(TargetType.NETWORK_HOST.value, "reconnaissance")
        assert "service_enumeration" in caps

    def test_alias_recon_resolves_correctly(self):
        caps_alias = required_capabilities(TargetType.NETWORK_HOST.value, "recon")
        caps_full  = required_capabilities(TargetType.NETWORK_HOST.value, "reconnaissance")
        assert caps_alias == caps_full

    def test_returns_set(self):
        caps = required_capabilities(TargetType.WEB_APPLICATION.value, "quick")
        assert isinstance(caps, set)


# ---------------------------------------------------------------------------
# objective_settings
# ---------------------------------------------------------------------------

class TestObjectiveSettings:
    def test_returns_dict(self):
        settings = objective_settings("quick")
        assert isinstance(settings, dict)

    def test_alias_resolves_before_lookup(self):
        assert objective_settings("recon") == objective_settings("reconnaissance")

    def test_unknown_objective_returns_default_settings(self):
        settings = objective_settings("completely_unknown_objective")
        default  = objective_settings(DEFAULT_OBJECTIVE)
        assert settings == default

    def test_returns_copy_not_reference(self):
        s1 = objective_settings("quick")
        s2 = objective_settings("quick")
        s1["__mutation_test__"] = True
        assert "__mutation_test__" not in s2


# ---------------------------------------------------------------------------
# tech_values_from_profile
# ---------------------------------------------------------------------------

class TestTechValuesFromProfile:
    def test_filters_out_unknown(self):
        techs = [TechnologyStack.WORDPRESS, TechnologyStack.UNKNOWN, TechnologyStack.PHP]
        result = tech_values_from_profile(techs)
        assert TechnologyStack.UNKNOWN.value not in result
        assert TechnologyStack.WORDPRESS.value in result
        assert TechnologyStack.PHP.value in result

    def test_all_unknown_returns_empty_set(self):
        result = tech_values_from_profile([TechnologyStack.UNKNOWN])
        assert result == set()

    def test_empty_list_returns_empty_set(self):
        assert tech_values_from_profile([]) == set()

    def test_returns_set_of_strings(self):
        result = tech_values_from_profile([TechnologyStack.WORDPRESS])
        assert isinstance(result, set)
        for v in result:
            assert isinstance(v, str)


# ---------------------------------------------------------------------------
# build_tool_catalog / validate_tool_catalog (already in precision_planner
# but worth a dedicated sanity check here too)
# ---------------------------------------------------------------------------

class TestCatalogStructure:
    def test_catalog_is_non_empty(self):
        catalog = build_tool_catalog()
        assert len(catalog) > 0

    def test_every_spec_has_required_fields(self):
        catalog = build_tool_catalog()
        for name, spec in catalog.items():
            assert spec.name == name, f"{name}: spec.name mismatch"
            assert isinstance(spec.capabilities, set), f"{name}: capabilities must be a set"
            assert isinstance(spec.target_types, set), f"{name}: target_types must be a set"
            assert 0.0 <= spec.noise_score <= 1.0, f"{name}: noise_score out of range"

    def test_validate_returns_no_issues(self):
        issues = validate_tool_catalog(build_tool_catalog())
        assert issues == []
