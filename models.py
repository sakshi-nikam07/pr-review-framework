"""Common data structures."""
from dataclasses import dataclass
from typing import List


@dataclass
class Finding:
    """A raw finding produced by ONE source (static tool or one agent)."""
    file: str
    line: int
    category: str
    source: str          # "static", "security", "bug", "performance", "style", "llm", "bandit"
    detail: str = ""


@dataclass
class FusedFinding:
    """A final finding after the Coordinator merged all sources."""
    file: str
    line: int
    category: str
    sources: List[str]
    confidence: float
