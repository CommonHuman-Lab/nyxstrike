import json
import logging
import os
import shutil
import threading
from collections import deque
from typing import Any, Deque, Dict, List, Optional

import server_core.config_core as config_core


logger = logging.getLogger(__name__)

RUN_HISTORY_FILE_NAME = "run_history.json"
HISTORY_DIR_NAME = "history"


class RunHistoryStore:
  """
  In-memory store of the last N tool executions, including full stdout/stderr.
  Thread-safe. Oldest entries are dropped when the cap is reached.
  """

  MAX_ENTRIES = 500

  def __init__(self, data_dir: Optional[str] = None):
    self._data_dir = data_dir or config_core.default_data_dir()
    self._history_dir = os.path.join(self._data_dir, HISTORY_DIR_NAME)
    self._history_path = os.path.join(self._history_dir, RUN_HISTORY_FILE_NAME)
    self._legacy_history_path = os.path.join(self._data_dir, RUN_HISTORY_FILE_NAME)
    self._lock = threading.Lock()
    self._entries: Deque[Dict[str, Any]] = deque(maxlen=self.MAX_ENTRIES)
    self._id_counter = 0
    self._ensure_dir()
    self._load()

  def record(
    self,
    tool: Optional[str],
    endpoint: Optional[str],
    params: Optional[Dict[str, Any]],
    result: Dict[str, Any],
    session_id: Optional[str] = None,
  ) -> None:
    with self._lock:
      self._id_counter += 1
      self._entries.appendleft({
        "id": self._id_counter,
        "tool": tool or "unknown",
        "endpoint": endpoint or "",
        "params": params or {},
        "session_id": session_id or "",
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "return_code": result.get("return_code", -1),
        "success": result.get("success", False),
        "timed_out": result.get("timed_out", False),
        "partial_results": result.get("partial_results", False),
        "execution_time": result.get("execution_time", 0.0),
        "timestamp": result.get("timestamp", ""),
      })
      self._save_locked()

  def get_all(self) -> List[Dict[str, Any]]:
    with self._lock:
      return list(self._entries)

  def clear(self) -> None:
    with self._lock:
      self._entries.clear()
      self._id_counter = 0
      self._save_locked()

  def _ensure_dir(self) -> None:
    os.makedirs(self._history_dir, exist_ok=True)
    if os.path.exists(self._legacy_history_path) and not os.path.exists(self._history_path):
      try:
        shutil.move(self._legacy_history_path, self._history_path)
      except OSError:
        shutil.copy2(self._legacy_history_path, self._history_path)
        try:
          os.remove(self._legacy_history_path)
        except OSError:
          pass

  def _load(self) -> None:
    if not os.path.exists(self._history_path):
      return
    try:
      with open(self._history_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
      if not isinstance(raw, list):
        logger.warning("run_history_store: invalid history format in %s", self._history_path)
        return
      cleaned: List[Dict[str, Any]] = []
      max_id = 0
      for entry in raw[:self.MAX_ENTRIES]:
        if not isinstance(entry, dict):
          continue
        entry_id = int(entry.get("id", 0) or 0)
        max_id = max(max_id, entry_id)
        cleaned.append({
          "id": entry_id,
          "tool": entry.get("tool", "unknown"),
          "endpoint": entry.get("endpoint", ""),
          "params": entry.get("params", {}),
          "session_id": entry.get("session_id", ""),
          "stdout": entry.get("stdout", ""),
          "stderr": entry.get("stderr", ""),
          "return_code": entry.get("return_code", -1),
          "success": bool(entry.get("success", False)),
          "timed_out": bool(entry.get("timed_out", False)),
          "partial_results": bool(entry.get("partial_results", False)),
          "execution_time": entry.get("execution_time", 0.0),
          "timestamp": entry.get("timestamp", ""),
        })
      self._entries = deque(cleaned, maxlen=self.MAX_ENTRIES)
      self._id_counter = max_id
      logger.debug("run_history_store: loaded %d entries from %s", len(cleaned), self._history_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
      logger.warning("run_history_store: could not load %s (%s)", self._history_path, exc)

  def _save_locked(self) -> None:
    tmp = self._history_path + ".tmp"
    try:
      with open(tmp, "w", encoding="utf-8") as f:
        json.dump(list(self._entries), f, indent=2, default=str)
      os.replace(tmp, self._history_path)
    except OSError as exc:
      logger.error("run_history_store: failed to save %s: %s", self._history_path, exc)
