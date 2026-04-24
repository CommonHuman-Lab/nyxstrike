"""
server_core/tool_stats_store.py

Persistent per-tool effectiveness tracker.

Stores the number of times each tool has been invoked and how many of those
runs produced a successful result (non-error, non-empty output).  Data is
written to a JSON file inside the standard application data directory so it
survives server restarts.

A "successful" run is defined as:
    result["success"] is True  AND  result["stdout"].strip() is non-empty

This gives a real, observable success-rate number rather than a static guess.

The live success rate is blended with the static baseline from tool_registry.py
when fewer than MIN_RUNS_FOR_LIVE have been recorded — ensuring the number shown
is always meaningful even for rarely-used tools.

Design:
  - KISS: plain JSON file, one dict of {tool: {"runs": int, "successes": int}}
  - Thread-safe via a single lock
  - Atomic writes (write to .tmp then os.replace) to avoid corruption
  - Idempotent: safe to call record() repeatedly
"""

import json
import logging
import math
import os
import shutil
import threading
import time
from typing import Dict, Optional, Tuple, Union
import server_core.config_core as config_core

logger = logging.getLogger(__name__)

# Minimum number of recorded runs before we trust the live rate over the baseline.
MIN_RUNS_FOR_LIVE = 5

# Bayesian + recency parameters for adaptive effectiveness scoring.
BAYES_PRIOR_STRENGTH = 6.0
RECENCY_HALF_LIFE_DAYS = 21.0
UNCERTAINTY_EXPLORATION_WEIGHT = 0.06

STATS_FILE_NAME = "tool_stats.json"
CONTEXT_STATS_FILE_NAME = "tool_stats_context.json"
STATS_DIR_NAME = "stats"
StatsValue = Union[int, float]

class ToolStatsStore:
    """
    Tracks per-tool run counts and success counts on disk.

    Attributes exposed via public methods:
        record(tool, success)       — record one run outcome
        get_stats(tool)             — {"runs": int, "successes": int}
        get_all_stats()             — full dict of all tools
        live_effectiveness(tool)    — float in [0, 1] or None if < MIN_RUNS_FOR_LIVE
        blended_effectiveness(tool, baseline) — float blending live + baseline
        reset(tool)                 — clear stats for one tool (admin use)
    """

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self._data_dir = data_dir or config_core.default_data_dir()
        self._stats_dir = os.path.join(self._data_dir, STATS_DIR_NAME)
        self._stats_path = os.path.join(self._stats_dir, STATS_FILE_NAME)
        self._context_stats_path = os.path.join(self._stats_dir, CONTEXT_STATS_FILE_NAME)
        self._legacy_stats_path = os.path.join(self._data_dir, STATS_FILE_NAME)
        self._legacy_context_stats_path = os.path.join(self._data_dir, CONTEXT_STATS_FILE_NAME)
        self._lock = threading.Lock()
        self._stats: Dict[str, Dict[str, StatsValue]] = {}
        self._context_stats: Dict[str, Dict[str, StatsValue]] = {}
        self._ensure_dir()
        self._load()

    # ── Public API ────────────────────────────────────────────────────

    def record(self, tool: str, success: bool) -> None:
        """Record one tool execution outcome.

        Args:
            tool:    Tool name (e.g. "nmap")
            success: True if the run returned useful output, False otherwise
        """
        now_ts = time.time()
        with self._lock:
            entry = self._stats.setdefault(
                tool,
                {
                    "runs": 0,
                    "successes": 0,
                    "decayed_runs": 0.0,
                    "decayed_successes": 0.0,
                    "last_updated": now_ts,
                },
            )
            self._apply_decay_inplace(entry, now_ts)
            entry["runs"] += 1
            if success:
                entry["successes"] += 1
            entry["decayed_runs"] = float(entry.get("decayed_runs", 0.0)) + 1.0
            if success:
                entry["decayed_successes"] = float(entry.get("decayed_successes", 0.0)) + 1.0
            entry["last_updated"] = now_ts
            self._save_locked()

    def record_contextual(self, tool: str, success: bool, context_key: str) -> None:
        """Record one tool execution outcome scoped to a context key."""
        if not context_key:
            return
        bucket = f"{tool}|{context_key}"
        now_ts = time.time()
        with self._lock:
            entry = self._context_stats.setdefault(
                bucket,
                {
                    "runs": 0,
                    "successes": 0,
                    "decayed_runs": 0.0,
                    "decayed_successes": 0.0,
                    "last_updated": now_ts,
                },
            )
            self._apply_decay_inplace(entry, now_ts)
            entry["runs"] += 1
            if success:
                entry["successes"] += 1
            entry["decayed_runs"] = float(entry.get("decayed_runs", 0.0)) + 1.0
            if success:
                entry["decayed_successes"] = float(entry.get("decayed_successes", 0.0)) + 1.0
            entry["last_updated"] = now_ts
            self._save_locked()

    def get_stats(self, tool: str) -> Dict[str, int]:
        """Return {"runs": int, "successes": int} for a tool (zeros if unseen)."""
        with self._lock:
            entry = self._stats.get(tool, {})
            return {
                "runs": int(entry.get("runs", 0)),
                "successes": int(entry.get("successes", 0)),
            }

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """Return a copy of the full stats dict."""
        with self._lock:
            return {
                k: {
                    "runs": int(v.get("runs", 0)),
                    "successes": int(v.get("successes", 0)),
                }
                for k, v in self._stats.items()
            }

    def live_effectiveness(self, tool: str) -> Optional[float]:
        """
        Return the observed success rate for a tool, or None if there are
        fewer than MIN_RUNS_FOR_LIVE recorded runs.

        Returns:
            float in [0.0, 1.0], or None
        """
        with self._lock:
            entry = dict(self._stats.get(tool, {"runs": 0, "successes": 0}))
        runs, successes = self._effective_counts(entry)
        if runs < float(MIN_RUNS_FOR_LIVE):
            return None
        return successes / runs

    def live_effectiveness_contextual(self, tool: str, context_key: str) -> Optional[float]:
        """Return observed success rate for a context bucket if enough data exists."""
        if not context_key:
            return None
        bucket = f"{tool}|{context_key}"
        with self._lock:
            entry = dict(self._context_stats.get(bucket, {"runs": 0, "successes": 0}))
        runs, successes = self._effective_counts(entry)
        if runs < float(MIN_RUNS_FOR_LIVE):
            return None
        return successes / runs

    def blended_effectiveness(self, tool: str, baseline: float) -> float:
        """
        Blend the live success rate with the static baseline.

        When runs < MIN_RUNS_FOR_LIVE the baseline is returned unchanged.
        Once enough data exists the live rate takes over completely.

        Args:
            tool:     Tool name
            baseline: Static effectiveness value from tool_registry (0.0–1.0)

        Returns:
            float in [0.0, 1.0]
        """
        with self._lock:
            entry = dict(self._stats.get(tool, {"runs": 0, "successes": 0}))
        return self._adaptive_effectiveness_from_entry(entry, baseline)

    def blended_effectiveness_contextual(self, tool: str, baseline: float, context_key: str) -> float:
        """Blend contextual and global rates with fallback to baseline."""
        bucket = f"{tool}|{context_key}" if context_key else ""
        with self._lock:
            global_entry = dict(self._stats.get(tool, {"runs": 0, "successes": 0}))
            contextual_entry = dict(self._context_stats.get(bucket, {"runs": 0, "successes": 0})) if bucket else {}

        global_score = self._adaptive_effectiveness_from_entry(global_entry, baseline)
        if not bucket:
            return global_score

        contextual_score = self._adaptive_effectiveness_from_entry(contextual_entry, baseline)
        contextual_runs, _ = self._effective_counts(contextual_entry)
        contextual_weight = min(0.8, contextual_runs / (float(MIN_RUNS_FOR_LIVE) + contextual_runs))
        return self._clamp((contextual_score * contextual_weight) + (global_score * (1.0 - contextual_weight)))

    def reset(self, tool: str) -> None:
        """Clear recorded stats for a single tool."""
        with self._lock:
            self._stats.pop(tool, None)
            for key in [k for k in self._context_stats.keys() if k.startswith(f"{tool}|")]:
                self._context_stats.pop(key, None)
            self._save_locked()

    # ── Internal ──────────────────────────────────────────────────────

    def _ensure_dir(self) -> None:
        os.makedirs(self._stats_dir, exist_ok=True)
        self._migrate_legacy_file(self._legacy_stats_path, self._stats_path)
        self._migrate_legacy_file(self._legacy_context_stats_path, self._context_stats_path)

    def _migrate_legacy_file(self, old_path: str, new_path: str) -> None:
        if not os.path.exists(old_path) or os.path.exists(new_path):
            return
        try:
            shutil.move(old_path, new_path)
        except OSError:
            shutil.copy2(old_path, new_path)
            try:
                os.remove(old_path)
            except OSError:
                pass

    def _load(self) -> None:
        if not os.path.exists(self._stats_path):
            self._stats = {}
            return
        try:
            with open(self._stats_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Validate shape: {str: {runs: int, successes: int}}
            cleaned: Dict[str, Dict[str, StatsValue]] = {}
            for tool, entry in raw.items():
                if isinstance(entry, dict):
                    runs = int(entry.get("runs", 0))
                    successes = int(entry.get("successes", 0))
                    cleaned[tool] = {
                        "runs": runs,
                        "successes": successes,
                        "decayed_runs": float(entry.get("decayed_runs", runs)),
                        "decayed_successes": float(entry.get("decayed_successes", successes)),
                        "last_updated": float(entry.get("last_updated", time.time())),
                    }
            self._stats = cleaned
            logger.debug("tool_stats_store: loaded %d tool entries from %s", len(cleaned), self._stats_path)
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            logger.warning("tool_stats_store: could not load %s (%s) — starting fresh", self._stats_path, exc)
            self._stats = {}

        if not os.path.exists(self._context_stats_path):
            self._context_stats = {}
            return

        try:
            with open(self._context_stats_path, "r", encoding="utf-8") as f:
                raw_context = json.load(f)
            cleaned_context: Dict[str, Dict[str, StatsValue]] = {}
            for key, entry in raw_context.items():
                if isinstance(entry, dict):
                    runs = int(entry.get("runs", 0))
                    successes = int(entry.get("successes", 0))
                    cleaned_context[key] = {
                        "runs": runs,
                        "successes": successes,
                        "decayed_runs": float(entry.get("decayed_runs", runs)),
                        "decayed_successes": float(entry.get("decayed_successes", successes)),
                        "last_updated": float(entry.get("last_updated", time.time())),
                    }
            self._context_stats = cleaned_context
            logger.debug(
                "tool_stats_store: loaded %d contextual tool entries from %s",
                len(cleaned_context),
                self._context_stats_path,
            )
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            logger.warning("tool_stats_store: could not load %s (%s) — starting fresh", self._context_stats_path, exc)
            self._context_stats = {}

    def _save_locked(self) -> None:
        """Write stats to disk. Must be called with self._lock held."""
        tmp = self._stats_path + ".tmp"
        context_tmp = self._context_stats_path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, indent=2)
            os.replace(tmp, self._stats_path)

            with open(context_tmp, "w", encoding="utf-8") as f:
                json.dump(self._context_stats, f, indent=2)
            os.replace(context_tmp, self._context_stats_path)
        except OSError as exc:
            logger.error("tool_stats_store: failed to save %s: %s", self._stats_path, exc)

    def _effective_counts(self, entry: Dict[str, StatsValue]) -> Tuple[float, float]:
        """Return recency-adjusted effective runs and successes."""
        if not entry:
            return 0.0, 0.0

        now_ts = time.time()
        last_updated = float(entry.get("last_updated", now_ts))
        decayed_runs = float(entry.get("decayed_runs", entry.get("runs", 0.0)))
        decayed_successes = float(entry.get("decayed_successes", entry.get("successes", 0.0)))

        if last_updated <= 0:
            return max(0.0, decayed_runs), max(0.0, decayed_successes)

        age_seconds = max(0.0, now_ts - last_updated)
        half_life_seconds = RECENCY_HALF_LIFE_DAYS * 86400.0
        if half_life_seconds <= 0:
            return max(0.0, decayed_runs), max(0.0, decayed_successes)

        decay_factor = math.exp(-math.log(2.0) * (age_seconds / half_life_seconds))
        return max(0.0, decayed_runs * decay_factor), max(0.0, decayed_successes * decay_factor)

    def _apply_decay_inplace(self, entry: Dict[str, StatsValue], now_ts: float) -> None:
        """Decay in-place counters up to now_ts to keep updates recency-weighted."""
        last_updated = float(entry.get("last_updated", now_ts))
        decayed_runs = float(entry.get("decayed_runs", entry.get("runs", 0.0)))
        decayed_successes = float(entry.get("decayed_successes", entry.get("successes", 0.0)))

        half_life_seconds = RECENCY_HALF_LIFE_DAYS * 86400.0
        if half_life_seconds > 0 and now_ts > last_updated:
            age_seconds = now_ts - last_updated
            factor = math.exp(-math.log(2.0) * (age_seconds / half_life_seconds))
            decayed_runs *= factor
            decayed_successes *= factor

        entry["decayed_runs"] = max(0.0, decayed_runs)
        entry["decayed_successes"] = max(0.0, decayed_successes)
        entry["last_updated"] = now_ts

    def _adaptive_effectiveness_from_entry(self, entry: Dict[str, StatsValue], baseline: float) -> float:
        """Compute Bayesian effectiveness with recency and uncertainty bonus."""
        prior_strength = max(1.0, float(BAYES_PRIOR_STRENGTH))
        baseline_clamped = self._clamp(float(baseline))
        alpha_prior = max(0.01, baseline_clamped * prior_strength)
        beta_prior = max(0.01, (1.0 - baseline_clamped) * prior_strength)

        runs, successes = self._effective_counts(entry)
        posterior_total = alpha_prior + beta_prior + runs
        posterior_mean = (alpha_prior + successes) / posterior_total

        confidence = min(1.0, runs / float(MIN_RUNS_FOR_LIVE))
        blended = (posterior_mean * confidence) + (baseline_clamped * (1.0 - confidence))

        uncertainty = math.sqrt(max(0.0, posterior_mean * (1.0 - posterior_mean) / (posterior_total + 1.0)))
        exploration_bonus = uncertainty * UNCERTAINTY_EXPLORATION_WEIGHT
        return self._clamp(blended + exploration_bonus)

    def _clamp(self, value: float) -> float:
        if value < 0.0:
            return 0.0
        if value > 1.0:
            return 1.0
        return value
