import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional


class RunHistoryStore:
  """
  In-memory store of the last N tool executions, including full stdout/stderr.
  Thread-safe. Oldest entries are dropped when the cap is reached.
  """

  MAX_ENTRIES = 500

  def __init__(self):
    self._lock = threading.Lock()
    self._entries: deque = deque(maxlen=self.MAX_ENTRIES)
    self._id_counter = 0

  def record(
    self,
    tool: Optional[str],
    endpoint: Optional[str],
    params: Optional[Dict[str, Any]],
    result: Dict[str, Any],
  ) -> None:
    with self._lock:
      self._id_counter += 1
      self._entries.appendleft({
        "id": self._id_counter,
        "tool": tool or "unknown",
        "endpoint": endpoint or "",
        "params": params or {},
        "stdout": result.get("stdout", ""),
        "stderr": result.get("stderr", ""),
        "return_code": result.get("return_code", -1),
        "success": result.get("success", False),
        "timed_out": result.get("timed_out", False),
        "partial_results": result.get("partial_results", False),
        "execution_time": result.get("execution_time", 0.0),
        "timestamp": result.get("timestamp", ""),
      })

  def get_all(self) -> List[Dict[str, Any]]:
    with self._lock:
      return list(self._entries)

  def clear(self) -> None:
    with self._lock:
      self._entries.clear()
