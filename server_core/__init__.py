"""
Core Module
Shared infrastructure components for the framework
"""

from .cache import CommandResultCache
from .session_store import SessionStore
from .wordlist_store import WordlistStore
from .telemetry_collector import TelemetryCollector
from .modern_visual_engine import ModernVisualEngine
from .operation_types import determine_operation_type as _determine_operation_type
from .command_params import rebuild_command_with_params as _rebuild_command_with_params
from .file_ops import file_manager
from .command_executor import execute_command as _execute_command
from .recovery_executor import execute_command_with_recovery as _execute_command_with_recovery
from .vulnerability_correlator import VulnerabilityCorrelator
from .enhanced_process_manager import EnhancedProcessManager
from .technology_detector import TechnologyDetector
from .parameter_optimizer import ParameterOptimizer
from .rate_limit_detector import RateLimitDetector
from .failure_recovery_system import FailureRecoverySystem
from .performance_monitor import PerformanceMonitor
from .ai_exploit_generator import AIExploitGenerator
from .intelligence.cve_intelligence_manager import CVEIntelligenceManager
from .intelligence.intelligent_decision_engine import IntelligentDecisionEngine

from .workflows.ctf.CTFChallenge import CTFChallenge
from .workflows.bugbounty.target import BugBountyTarget
from .workflows.bugbounty.workflow import BugBountyWorkflowManager
from .workflows.bugbounty.testing import FileUploadTestingFramework
from .workflows.ctf.workflowManager import CTFWorkflowManager
from .workflows.ctf.toolManager import CTFToolManager
from .workflows.ctf.automator import CTFChallengeAutomator
from .workflows.ctf.coordinator import CTFTeamCoordinator

from .python_env_manager import env_manager

from .error_handling import (
    ErrorType,
    RecoveryAction,
    ErrorContext,
    IntelligentErrorHandler,
    GracefulDegradation,
)

# Shared singletons — import instances directly rather than constructing new ones
from .singletons import (
    cache,
    session_store,
    wordlist_store,
    telemetry,
    enhanced_process_manager,
    error_handler,
    degradation_manager,
    cve_intelligence,
    exploit_generator,
    vulnerability_correlator,
    decision_engine,
    bugbounty_manager,
    fileupload_framework,
    ctf_manager,
    ctf_tools,
    ctf_automator,
    ctf_coordinator,
    ROCKYOU_PATH,
    COMMON_DIRB_PATH,
    COMMON_DIRSEARCH_PATH,
)

__all__ = [
    # Classes
    "env_manager",
    "ModernVisualEngine",
    "CommandResultCache",
    "TelemetryCollector",
    "SessionStore",
    "WordlistStore",
    "CVEIntelligenceManager",
    "IntelligentDecisionEngine",
    "CTFChallenge",
    "BugBountyTarget",
    "BugBountyWorkflowManager",
    "FileUploadTestingFramework",
    "CTFWorkflowManager",
    "CTFToolManager",
    "CTFChallengeAutomator",
    "CTFTeamCoordinator",
    "EnhancedProcessManager",
    "TechnologyDetector",
    "ParameterOptimizer",
    "RateLimitDetector",
    "FailureRecoverySystem",
    "PerformanceMonitor",
    "ErrorType",
    "RecoveryAction",
    "ErrorContext",
    "IntelligentErrorHandler",
    "GracefulDegradation",
    "_determine_operation_type",
    "file_manager",
    "_rebuild_command_with_params",
    "_execute_command",
    "_execute_command_with_recovery",
    "VulnerabilityCorrelator",
    "AIExploitGenerator",
    # Shared singleton instances
    "cache",
    "session_store",
    "wordlist_store",
    "telemetry",
    "enhanced_process_manager",
    "error_handler",
    "degradation_manager",
    "cve_intelligence",
    "exploit_generator",
    "vulnerability_correlator",
    "decision_engine",
    "bugbounty_manager",
    "fileupload_framework",
    "ctf_manager",
    "ctf_tools",
    "ctf_automator",
    "ctf_coordinator",
    "ROCKYOU_PATH",
    "COMMON_DIRB_PATH",
    "COMMON_DIRSEARCH_PATH",
]
