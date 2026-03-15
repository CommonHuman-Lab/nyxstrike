from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class CTFChallenge:
    """CTF challenge information"""
    name: str
    category: str  # web, crypto, pwn, forensics, rev, misc, osint
    description: str
    points: int = 0
    difficulty: str = "unknown"  # easy, medium, hard, insane
    files: List[str] = field(default_factory=list)
    url: str = ""
    hints: List[str] = field(default_factory=list)
    target: Optional[str] = None  # Target for the challenge (e.g., IP, domain, binary)