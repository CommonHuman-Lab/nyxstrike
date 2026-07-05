"""
tests/test_decision_engine_session_feedback.py

Pure-Python unit tests for session-aware tool scoring in
server_core/intelligence/intelligent_decision_engine.py.

No subprocess, no Flask, no server calls, no real HTTP probes: TargetProfile
is built directly rather than via decision_engine.analyze_target().
"""

import server_core.session_flow as session_flow
from server_core.singletons import decision_engine
from shared.target_profile import TargetProfile
from shared.target_types import TargetType


def _profile(target_type=TargetType.NETWORK_HOST):
    return TargetProfile(target="10.10.10.10", target_type=target_type, confidence_score=0.8)


class _FakeLoadSessionAny:
    """Callable stand-in for session_flow.load_session_any."""

    def __init__(self, session_dict=None):
        self.session_dict = session_dict

    def __call__(self, session_id):
        if self.session_dict is None:
            return None
        return (self.session_dict, "active")


def test_session_penalty_applied_to_last_failed_tool(monkeypatch):
    monkeypatch.setattr(
        session_flow,
        "load_session_any",
        _FakeLoadSessionAny({"run_log": [{"tool": "nmap", "success": False}]}),
    )

    profile = _profile()
    unpenalized = decision_engine._effective_score("nmap", profile.target_type.value)
    penalized = decision_engine._effective_score(
        "nmap", profile.target_type.value, session_penalties=decision_engine._session_failure_penalties("sess1")
    )

    assert penalized < unpenalized


def test_later_success_clears_penalty(monkeypatch):
    monkeypatch.setattr(
        session_flow,
        "load_session_any",
        _FakeLoadSessionAny(
            {
                "run_log": [
                    {"tool": "nmap", "success": False},
                    {"tool": "nmap", "success": True},
                ]
            }
        ),
    )

    penalties = decision_engine._session_failure_penalties("sess1")
    assert "nmap" not in penalties


def test_session_id_omitted_is_no_op(monkeypatch):
    monkeypatch.setattr(
        session_flow,
        "load_session_any",
        _FakeLoadSessionAny({"run_log": [{"tool": "nmap", "success": False}]}),
    )

    profile = _profile()
    without_session_explicit = decision_engine.select_optimal_tools(profile, "comprehensive", session_id=None)
    without_session_default = decision_engine.select_optimal_tools(profile, "comprehensive")

    # Regression guard: omitting session_id (or passing None) must reproduce
    # today's behavior exactly, even though load_session_any is monkeypatched
    # to report a failure — the penalty must never be applied without a session_id.
    assert without_session_explicit == without_session_default
    assert without_session_default != []


def test_missing_session_is_non_fatal(monkeypatch):
    monkeypatch.setattr(session_flow, "load_session_any", _FakeLoadSessionAny(None))

    assert decision_engine._session_failure_penalties("does-not-exist") == {}

    profile = _profile()
    # Must not raise even though the session cannot be loaded.
    tools = decision_engine.select_optimal_tools(profile, "comprehensive", session_id="does-not-exist")
    assert isinstance(tools, list)


def test_malformed_run_log_is_non_fatal(monkeypatch):
    monkeypatch.setattr(
        session_flow,
        "load_session_any",
        _FakeLoadSessionAny({"run_log": "not-a-list"}),
    )
    assert decision_engine._session_failure_penalties("sess1") == {}


def test_penalty_is_dampening_not_exclusion(monkeypatch):
    """A penalized tool must remain selectable (multiplicative factor, not a hard filter)."""
    monkeypatch.setattr(
        session_flow,
        "load_session_any",
        _FakeLoadSessionAny({"run_log": [{"tool": "nmap", "success": False}]}),
    )

    profile = _profile()
    penalties = decision_engine._session_failure_penalties("sess1")
    assert penalties.get("nmap") == 0.2

    score = decision_engine._effective_score("nmap", profile.target_type.value, session_penalties=penalties)
    assert score > 0.0
