"""
tests/test_attack_chain.py

Pure-Python unit tests for AttackChain and AttackStep.

No subprocess, no Flask, no server calls.
"""

import pytest

from shared.attack_chain import AttackChain
from shared.attack_step import AttackStep
from shared.target_profile import TargetProfile
from shared.target_types import TargetType


def _make_profile(target="https://example.com"):
    p = TargetProfile(target=target)
    p.target_type = TargetType.WEB_APPLICATION
    return p


def _make_step(tool="nmap", prob=0.8, exec_time=30):
    return AttackStep(
        tool=tool,
        parameters={},
        expected_outcome="scan results",
        success_probability=prob,
        execution_time_estimate=exec_time,
    )


# ---------------------------------------------------------------------------
# add_step
# ---------------------------------------------------------------------------

class TestAddStep:
    def test_add_step_appends_to_steps(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step("nmap"))
        assert len(chain.steps) == 1
        assert chain.steps[0].tool == "nmap"

    def test_add_step_accumulates_estimated_time(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step(exec_time=30))
        chain.add_step(_make_step(exec_time=60))
        assert chain.estimated_time == 90

    def test_add_step_collects_required_tools(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step("nmap"))
        chain.add_step(_make_step("sqlmap"))
        assert "nmap" in chain.required_tools
        assert "sqlmap" in chain.required_tools

    def test_duplicate_tool_appears_once_in_required_tools(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step("nmap"))
        chain.add_step(_make_step("nmap"))
        assert chain.required_tools == {"nmap"}


# ---------------------------------------------------------------------------
# calculate_success_probability
# ---------------------------------------------------------------------------

class TestCalculateSuccessProbability:
    def test_empty_chain_gives_zero(self):
        chain = AttackChain(_make_profile())
        chain.calculate_success_probability()
        assert chain.success_probability == 0.0

    def test_single_step_equals_step_probability(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step(prob=0.75))
        chain.calculate_success_probability()
        assert abs(chain.success_probability - 0.75) < 1e-9

    def test_two_steps_are_multiplied(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step(prob=0.8))
        chain.add_step(_make_step(prob=0.5))
        chain.calculate_success_probability()
        assert abs(chain.success_probability - 0.4) < 1e-9

    def test_three_steps_compound_probability(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step(prob=0.9))
        chain.add_step(_make_step(prob=0.9))
        chain.add_step(_make_step(prob=0.9))
        chain.calculate_success_probability()
        expected = 0.9 ** 3
        assert abs(chain.success_probability - expected) < 1e-9

    def test_any_zero_probability_step_makes_chain_zero(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step(prob=0.9))
        chain.add_step(_make_step(prob=0.0))
        chain.add_step(_make_step(prob=0.9))
        chain.calculate_success_probability()
        assert chain.success_probability == 0.0

    def test_all_certain_steps_give_one(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step(prob=1.0))
        chain.add_step(_make_step(prob=1.0))
        chain.calculate_success_probability()
        assert abs(chain.success_probability - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

class TestToDict:
    def test_to_dict_contains_required_keys(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step("nmap", prob=0.8, exec_time=30))
        chain.calculate_success_probability()
        d = chain.to_dict()

        assert "target" in d
        assert "steps" in d
        assert "success_probability" in d
        assert "estimated_time" in d
        assert "required_tools" in d
        assert "risk_level" in d

    def test_to_dict_steps_contain_tool_name(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step("nuclei", prob=0.7))
        d = chain.to_dict()
        assert d["steps"][0]["tool"] == "nuclei"

    def test_to_dict_required_tools_is_list(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step("nmap"))
        d = chain.to_dict()
        assert isinstance(d["required_tools"], list)

    def test_to_dict_target_matches_profile(self):
        profile = _make_profile("https://target.example.com")
        chain = AttackChain(profile)
        d = chain.to_dict()
        assert d["target"] == "https://target.example.com"

    def test_to_dict_success_probability_reflects_calculation(self):
        chain = AttackChain(_make_profile())
        chain.add_step(_make_step(prob=0.6))
        chain.add_step(_make_step(prob=0.5))
        chain.calculate_success_probability()
        d = chain.to_dict()
        assert abs(d["success_probability"] - 0.3) < 1e-9
