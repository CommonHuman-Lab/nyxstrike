"""
server_core/tool_stats_store.py

Persistent per-tool effectiveness tracker.

Stores the number of times each tool has been invoked and how many of those
runs produced a successful result (non-error, non-empty output).  Data is
written to a JSON file inside the standard HexStrike data directory so it
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
import os
import threading
from typing import Dict, Optional
import server_core.config_core as config_core

logger = logging.getLogger(__name__)

# Minimum number of recorded runs before we trust the live rate over the baseline.
MIN_RUNS_FOR_LIVE = 5

STATS_FILE_NAME = "tool_stats.json"

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
        self._stats_path = os.path.join(self._data_dir, STATS_FILE_NAME)
        self._lock = threading.Lock()
        self._stats: Dict[str, Dict[str, int]] = {}
        self._ensure_dir()
        self._load()

    # ── Public API ────────────────────────────────────────────────────

    def record(self, tool: str, success: bool) -> None:
        """Record one tool execution outcome.

        Args:
            tool:    Tool name (e.g. "nmap")
            success: True if the run returned useful output, False otherwise
        """
        with self._lock:
            entry = self._stats.setdefault(tool, {"runs": 0, "successes": 0})
            entry["runs"] += 1
            if success:
                entry["successes"] += 1
            self._save_locked()

    def get_stats(self, tool: str) -> Dict[str, int]:
        """Return {"runs": int, "successes": int} for a tool (zeros if unseen)."""
        with self._lock:
            return dict(self._stats.get(tool, {"runs": 0, "successes": 0}))

    def get_all_stats(self) -> Dict[str, Dict[str, int]]:
        """Return a copy of the full stats dict."""
        with self._lock:
            return {k: dict(v) for k, v in self._stats.items()}

    def live_effectiveness(self, tool: str) -> Optional[float]:
        """
        Return the observed success rate for a tool, or None if there are
        fewer than MIN_RUNS_FOR_LIVE recorded runs.

        Returns:
            float in [0.0, 1.0], or None
        """
        stats = self.get_stats(tool)
        if stats["runs"] < MIN_RUNS_FOR_LIVE:
            return None
        return stats["successes"] / stats["runs"]

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
        live = self.live_effectiveness(tool)
        if live is None:
            return baseline
        return live

    def reset(self, tool: str) -> None:
        """Clear recorded stats for a single tool."""
        with self._lock:
            self._stats.pop(tool, None)
            self._save_locked()

    # ── Internal ──────────────────────────────────────────────────────

    def _ensure_dir(self) -> None:
        os.makedirs(self._data_dir, exist_ok=True)

    def _load(self) -> None:
        if not os.path.exists(self._stats_path):
            self._stats = {}
            return
        try:
            with open(self._stats_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # Validate shape: {str: {runs: int, successes: int}}
            cleaned: Dict[str, Dict[str, int]] = {}
            for tool, entry in raw.items():
                if isinstance(entry, dict):
                    cleaned[tool] = {
                        "runs": int(entry.get("runs", 0)),
                        "successes": int(entry.get("successes", 0)),
                    }
            self._stats = cleaned
            logger.debug("tool_stats_store: loaded %d tool entries from %s", len(cleaned), self._stats_path)
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            logger.warning("tool_stats_store: could not load %s (%s) — starting fresh", self._stats_path, exc)
            self._stats = {}

    def _save_locked(self) -> None:
        """Write stats to disk. Must be called with self._lock held."""
        tmp = self._stats_path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, indent=2)
            os.replace(tmp, self._stats_path)
        except OSError as exc:
            logger.error("tool_stats_store: failed to save %s: %s", self._stats_path, exc)
