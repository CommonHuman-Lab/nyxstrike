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

import server_core.config_core as config_core

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

# ── Process management ────────────────────────────────────────────────────────
from .enhanced_process_manager import EnhancedProcessManager

enhanced_process_manager = EnhancedProcessManager()

# ── Error handling ────────────────────────────────────────────────────────────
from .error_handling import IntelligentErrorHandler, GracefulDegradation

error_handler = IntelligentErrorHandler()
degradation_manager = GracefulDegradation()

# ── Vulnerability intelligence ────────────────────────────────────────────────
from .intelligence.cve_intelligence_manager import CVEIntelligenceManager
from .ai_exploit_generator import AIExploitGenerator
from .vulnerability_correlator import VulnerabilityCorrelator

cve_intelligence = CVEIntelligenceManager()
exploit_generator = AIExploitGenerator()
vulnerability_correlator = VulnerabilityCorrelator()

# ── Decision engine ───────────────────────────────────────────────────────────
from .intelligence.intelligent_decision_engine import IntelligentDecisionEngine

decision_engine = IntelligentDecisionEngine()

# ── Bug bounty ────────────────────────────────────────────────────────────────
from .workflows.bugbounty.workflow import BugBountyWorkflowManager
from .workflows.bugbounty.testing import FileUploadTestingFramework

bugbounty_manager = BugBountyWorkflowManager()
fileupload_framework = FileUploadTestingFramework()

# ── CTF ───────────────────────────────────────────────────────────────────────
from .workflows.ctf.workflowManager import CTFWorkflowManager
from .workflows.ctf.toolManager import CTFToolManager
from .workflows.ctf.automator import CTFChallengeAutomator
from .workflows.ctf.coordinator import CTFTeamCoordinator

ctf_manager = CTFWorkflowManager()
ctf_tools = CTFToolManager()
ctf_automator = CTFChallengeAutomator()
ctf_coordinator = CTFTeamCoordinator()

# ── Wordlist paths (resolved once) ────────────────────────────────────────────
ROCKYOU_PATH = wordlist_store.get_word_list_path("rockyou")
COMMON_DIRB_PATH = wordlist_store.get_word_list_path("common_dirb")
COMMON_DIRSEARCH_PATH = wordlist_store.get_word_list_path("common_dirsearch")

# ── LLM & database (optional — graceful degradation if unavailable) ───────────
from .db import NyxStrikeDB
from .llm_client import LLMClient

db = NyxStrikeDB()
llm_client = LLMClient()
