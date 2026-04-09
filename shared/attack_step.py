from dataclasses import dataclass, field
from typing import Any, Dict, List

@dataclass
class AttackStep:
    """Individual step in an attack chain"""
    tool: str
    parameters: Dict[str, Any]
    expected_outcome: str
    success_probability: float
    execution_time_estimate: int  # seconds
    dependencies: List[str] = field(default_factory=list)
    selection_reason: Dict[str, Any] = field(default_factory=dict)
