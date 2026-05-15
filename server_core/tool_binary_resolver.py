import os
import shutil
import subprocess
from typing import List, Optional

from server_core import config_core


def _path_candidates(binary_name: str) -> List[str]:
  """Build a de-duplicated list of executable path candidates."""
  home_path = os.path.expanduser("~")
  paths_overrides = config_core.get("PATHS", {})
  go_bin_template = paths_overrides.get("GO_BINARYS", "{HOME}/go/bin/")
  go_bin_dir = go_bin_template.replace("{HOME}", home_path)
  configured_candidate = os.path.join(go_bin_dir, binary_name)

  candidates: List[str] = [configured_candidate]

  default_go_candidate = os.path.join(home_path, "go", "bin", binary_name)
  candidates.append(default_go_candidate)

  resolved_from_path = shutil.which(binary_name)
  if resolved_from_path:
    candidates.append(resolved_from_path)

  for path_dir in os.get_exec_path():
    candidates.append(os.path.join(path_dir, binary_name))

  unique_candidates: List[str] = []
  seen = set()
  for candidate in candidates:
    if candidate in seen:
      continue
    seen.add(candidate)
    unique_candidates.append(candidate)

  return unique_candidates


def _is_executable(path: str) -> bool:
  return os.path.isfile(path) and os.access(path, os.X_OK)


def _is_projectdiscovery_httpx(path: str) -> bool:
  """Check whether a path is the ProjectDiscovery httpx binary."""
  if not _is_executable(path):
    return False

  try:
    probe = subprocess.run(
      [path, "-h"],
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT,
      text=True,
      timeout=3,
    )
  except Exception:
    return False

  output = (probe.stdout or "").lower()
  markers = ("projectdiscovery", "-tech-detect", "-probe")
  return any(marker in output for marker in markers)


def resolve_projectdiscovery_httpx() -> Optional[str]:
  """Resolve a runnable ProjectDiscovery httpx binary path.

  Selection order:
  1) configured GO_BINARYS path,
  2) common Go path (~/go/bin),
  3) current PATH entries.

  Returns:
      Absolute path to ProjectDiscovery httpx binary when found, else None.
  """
  candidates = _path_candidates("httpx")

  for candidate in candidates:
    if _is_projectdiscovery_httpx(candidate):
      return candidate

  return None
