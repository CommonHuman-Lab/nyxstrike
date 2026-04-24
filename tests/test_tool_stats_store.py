"""
tests/test_tool_stats_store.py

Pure-Python unit tests for ToolStatsStore.

No subprocess, no Flask, no server calls — only the ToolStatsStore class
and its math.  Every test creates its own isolated tmp directory so tests
never touch the real data directory or each other's state.
"""

import math
import os
import time

import pytest

from server_core.tool_stats_store import (
    BAYES_PRIOR_STRENGTH,
    MIN_RUNS_FOR_LIVE,
    RECENCY_HALF_LIFE_DAYS,
    UNCERTAINTY_EXPLORATION_WEIGHT,
    ToolStatsStore,
)


@pytest.fixture()
def store(tmp_path):
    """Fresh ToolStatsStore backed by a temp directory."""
    return ToolStatsStore(data_dir=str(tmp_path))


# ---------------------------------------------------------------------------
# get_stats / record
# ---------------------------------------------------------------------------

class TestRecord:
    def test_unseen_tool_returns_zeros(self, store):
        s = store.get_stats("nmap")
        assert s == {"runs": 0, "successes": 0}

    def test_record_increments_runs(self, store):
        store.record("nmap", success=True)
        store.record("nmap", success=False)
        s = store.get_stats("nmap")
        assert s["runs"] == 2

    def test_record_increments_successes_only_on_success(self, store):
        store.record("nmap", success=True)
        store.record("nmap", success=True)
        store.record("nmap", success=False)
        s = store.get_stats("nmap")
        assert s["successes"] == 2

    def test_record_persists_across_reload(self, tmp_path):
        s1 = ToolStatsStore(data_dir=str(tmp_path))
        s1.record("hydra", success=True)
        s1.record("hydra", success=True)

        s2 = ToolStatsStore(data_dir=str(tmp_path))
        assert s2.get_stats("hydra")["runs"] == 2
        assert s2.get_stats("hydra")["successes"] == 2

    def test_get_all_stats_covers_multiple_tools(self, store):
        store.record("nmap", success=True)
        store.record("sqlmap", success=False)
        all_stats = store.get_all_stats()
        assert "nmap" in all_stats
        assert "sqlmap" in all_stats


# ---------------------------------------------------------------------------
# live_effectiveness
# ---------------------------------------------------------------------------

class TestLiveEffectiveness:
    def test_returns_none_below_min_runs(self, store):
        for _ in range(MIN_RUNS_FOR_LIVE - 1):
            store.record("nmap", success=True)
        assert store.live_effectiveness("nmap") is None

    def test_returns_float_with_enough_runs(self, store):
        # Use 2× MIN_RUNS_FOR_LIVE so recency decay cannot push decayed_runs
        # below the threshold even for runs recorded in rapid succession.
        for _ in range(MIN_RUNS_FOR_LIVE * 2):
            store.record("nmap", success=True)
        result = store.live_effectiveness("nmap")
        assert result is not None
        assert 0.0 <= result <= 1.0

    def test_returns_none_for_unseen_tool(self, store):
        assert store.live_effectiveness("nonexistent_tool") is None

    def test_perfect_success_rate(self, store):
        for _ in range(MIN_RUNS_FOR_LIVE * 2):
            store.record("nmap", success=True)
        rate = store.live_effectiveness("nmap")
        assert rate is not None
        assert rate > 0.9  # recency decay keeps it just below 1.0

    def test_zero_success_rate(self, store):
        for _ in range(MIN_RUNS_FOR_LIVE * 2):
            store.record("nmap", success=False)
        rate = store.live_effectiveness("nmap")
        assert rate is not None
        assert rate < 0.1


# ---------------------------------------------------------------------------
# blended_effectiveness
# ---------------------------------------------------------------------------

class TestBlendedEffectiveness:
    def test_returns_baseline_with_no_data(self, store):
        result = store.blended_effectiveness("nmap", baseline=0.75)
        # No runs → result should be close to baseline (Bayesian prior only)
        assert abs(result - 0.75) < 0.15

    def test_result_is_clamped_between_0_and_1(self, store):
        result = store.blended_effectiveness("nmap", baseline=0.9)
        assert 0.0 <= result <= 1.0

    def test_many_successes_pull_above_low_baseline(self, store):
        for _ in range(20):
            store.record("nmap", success=True)
        result_high = store.blended_effectiveness("nmap", baseline=0.3)
        result_baseline = 0.3
        assert result_high > result_baseline

    def test_many_failures_pull_below_high_baseline(self, store):
        for _ in range(20):
            store.record("nmap", success=False)
        result = store.blended_effectiveness("nmap", baseline=0.9)
        assert result < 0.9


# ---------------------------------------------------------------------------
# blended_effectiveness_contextual
# ---------------------------------------------------------------------------

class TestBlendedEffectivenessContextual:
    def test_empty_context_key_falls_back_to_global(self, store):
        store.record("nmap", success=True)
        global_score = store.blended_effectiveness("nmap", baseline=0.7)
        ctx_score = store.blended_effectiveness_contextual("nmap", baseline=0.7, context_key="")
        assert abs(global_score - ctx_score) < 1e-9

    def test_contextual_record_does_not_pollute_global(self, store):
        store.record_contextual("nmap", success=True, context_key="web_application")
        global_stats = store.get_stats("nmap")
        assert global_stats["runs"] == 0

    def test_result_in_unit_interval(self, store):
        store.record_contextual("nmap", success=True, context_key="api")
        result = store.blended_effectiveness_contextual("nmap", baseline=0.6, context_key="api")
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_clears_global_stats(self, store):
        store.record("nmap", success=True)
        store.reset("nmap")
        assert store.get_stats("nmap") == {"runs": 0, "successes": 0}

    def test_reset_clears_contextual_stats(self, store):
        store.record_contextual("nmap", success=True, context_key="web")
        store.reset("nmap")
        rate = store.live_effectiveness_contextual("nmap", context_key="web")
        assert rate is None

    def test_reset_unknown_tool_is_noop(self, store):
        store.reset("nonexistent_tool")  # must not raise


# ---------------------------------------------------------------------------
# Bayesian math sanity checks
# ---------------------------------------------------------------------------

class TestBayesianMath:
    def test_uncertainty_bonus_is_positive_with_no_data(self, store):
        """With zero runs the posterior is entirely the prior — exploration
        bonus should nudge the result slightly above the bare baseline."""
        baseline = 0.5
        result = store.blended_effectiveness("never_run_tool", baseline=baseline)
        # The exploration bonus is uncertainty * UNCERTAINTY_EXPLORATION_WEIGHT.
        # With a 0.5 baseline the uncertainty is maximised — result must be
        # above the baseline, not below it.
        assert result >= baseline

    def test_high_run_count_reduces_exploration_bonus(self, store):
        """After many runs the posterior dominates and the uncertainty bonus
        shrinks — blended score should converge toward the observed rate."""
        for _ in range(50):
            store.record("nmap", success=True)
        result = store.blended_effectiveness("nmap", baseline=0.5)
        # 50 successes → observed rate ~1.0; result should be well above 0.8
        assert result > 0.8

    def test_clamp_never_exceeds_one(self, store):
        for _ in range(100):
            store.record("nmap", success=True)
        assert store.blended_effectiveness("nmap", baseline=1.0) <= 1.0

    def test_clamp_never_goes_below_zero(self, store):
        for _ in range(100):
            store.record("nmap", success=False)
        assert store.blended_effectiveness("nmap", baseline=0.0) >= 0.0


# ---------------------------------------------------------------------------
# Legacy-file migration
# ---------------------------------------------------------------------------

class TestMigration:
    def test_legacy_file_is_migrated_on_init(self, tmp_path):
        import json
        legacy_path = tmp_path / "tool_stats.json"
        legacy_path.write_text(json.dumps({"nmap": {"runs": 3, "successes": 2}}))

        store = ToolStatsStore(data_dir=str(tmp_path))
        stats = store.get_stats("nmap")
        assert stats["runs"] == 3
        assert stats["successes"] == 2
        # Legacy file should have been moved; new location exists
        new_path = tmp_path / "stats" / "tool_stats.json"
        assert new_path.exists()
