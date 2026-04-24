"""
Core shared singletons.

All stateful service objects are constructed exactly once here.
Import from this module instead of constructing new instances in each blueprint.

Usage:
    from server_core.singletons import (
        cache, session_store, wordlist_store, telemetry,
        enhanced_process_manager, error_handler, degradation_manager,
        cve_intelligence, exploit_generator, vulnerability_correlator,
        decision_engine, bugbounty_manager, fileupload_framework,
        ctf_manager, ctf_tools, ctf_automator, ctf_coordinator,
        db, llm_client,
    )
"""

import threading
import server_core.config_core as config_core


class _Lazy:
    """Thread-safe lazy singleton wrapper.

    The wrapped instance is constructed on first attribute access, not at
    import time.  Uses double-checked locking so construction happens exactly
    once even under concurrent access.

    Transparent to callers — attribute access and method calls work identically
    to accessing the real object directly.
    """

    def __init__(self, factory):
        # Use object.__setattr__ to avoid triggering our own __setattr__
        object.__setattr__(self, "_factory", factory)
        object.__setattr__(self, "_instance", None)
        object.__setattr__(self, "_lock", threading.Lock())

    def _get_instance(self):
        instance = object.__getattribute__(self, "_instance")
        if instance is None:
            lock = object.__getattribute__(self, "_lock")
            with lock:
                instance = object.__getattribute__(self, "_instance")
                if instance is None:
                    factory = object.__getattribute__(self, "_factory")
                    instance = factory()
                    object.__setattr__(self, "_instance", instance)
        return instance

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)

    def __setattr__(self, name, value):
        setattr(self._get_instance(), name, value)

    def __repr__(self):
        instance = object.__getattribute__(self, "_instance")
        if instance is None:
            factory = object.__getattribute__(self, "_factory")
            return f"<_Lazy[{factory.__name__}] (not yet initialized)>"
        return repr(instance)

# ── Cache & stores ────────────────────────────────────────────────────────────
from .cache import CommandResultCache
from .session_store import SessionStore
from .wordlist_store import WordlistStore
from .run_history_store import RunHistoryStore
from .tool_stats_store import ToolStatsStore

cache = CommandResultCache()
session_store = SessionStore()
wordlist_store = WordlistStore()
run_history = RunHistoryStore()
tool_stats = ToolStatsStore()

# ── Telemetry (module-level singleton in enhanced_command_executor) ───────────
from .enhanced_command_executor import telemetry  # noqa: F401 — re-export

# ── Process management ──────
from .enhanced_process_manager import EnhancedProcessManager

enhanced_process_manager = _Lazy(EnhancedProcessManager)

# ── Error handling ────────────────────────────────────────────────────────────
from .error_handling import IntelligentErrorHandler, GracefulDegradation

error_handler = IntelligentErrorHandler()
degradation_manager = GracefulDegradation()

# ── Vulnerability intelligence ──────
from .intelligence.cve_intelligence_manager import CVEIntelligenceManager
from .ai_exploit_generator import AIExploitGenerator
from .vulnerability_correlator import VulnerabilityCorrelator

cve_intelligence = _Lazy(CVEIntelligenceManager)
exploit_generator = _Lazy(AIExploitGenerator)
vulnerability_correlator = _Lazy(VulnerabilityCorrelator)

# ── Decision engine ───────────────────────────────────────────────────────────
from .intelligence.intelligent_decision_engine import IntelligentDecisionEngine

decision_engine = IntelligentDecisionEngine()

# ── Bug bounty ───────────────────────────────────────────────────────────────
from .workflows.bugbounty.workflow import BugBountyWorkflowManager
from .workflows.bugbounty.testing import FileUploadTestingFramework

bugbounty_manager = _Lazy(BugBountyWorkflowManager)
fileupload_framework = _Lazy(FileUploadTestingFramework)

# ── CTF ─────────────────────────────────────────────────────────────────────
from .workflows.ctf.workflowManager import CTFWorkflowManager
from .workflows.ctf.toolManager import CTFToolManager
from .workflows.ctf.automator import CTFChallengeAutomator
from .workflows.ctf.coordinator import CTFTeamCoordinator

ctf_manager = _Lazy(CTFWorkflowManager)
ctf_tools = _Lazy(CTFToolManager)
ctf_automator = _Lazy(CTFChallengeAutomator)
ctf_coordinator = _Lazy(CTFTeamCoordinator)

# ── Wordlist paths (resolved once) ────────────────────────────────────────────
ROCKYOU_PATH = wordlist_store.get_word_list_path("rockyou")
COMMON_DIRB_PATH = wordlist_store.get_word_list_path("common_dirb")
COMMON_DIRSEARCH_PATH = wordlist_store.get_word_list_path("common_dirsearch")

# ── LLM & database (optional — graceful degradation if unavailable) ───────────
from .db import NyxStrikeDB
from .llm_client import LLMClient

db = NyxStrikeDB()
llm_client = LLMClient()
