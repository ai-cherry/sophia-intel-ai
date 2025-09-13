from __future__ import annotations

import math
import re
from typing import Dict, List


class PIIAssessment(dict):
    def __init__(self) -> None:
        super().__init__(risks=[])

    def add_risk(self, kind: str, confidence: float) -> None:
        self["risks"].append({"type": kind, "confidence": confidence})


class PIIDetector:
    def __init__(self) -> None:
        self.patterns: Dict[str, str] = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "phone": r"\b\d{3}-\d{3}-\d{4}\b",
        }
        self.context_clues = ["salary", "wage", "personal", "confidential"]

    def detect_and_classify(self, content: str, field_name: str) -> PIIAssessment:
        assessment = PIIAssessment()
        # Pattern matching
        for pii_type, pattern in self.patterns.items():
            if re.search(pattern, content or ""):
                assessment.add_risk(pii_type, confidence=0.9)
        # Context analysis
        if any(clue in (field_name or "").lower() for clue in self.context_clues):
            assessment.add_risk("contextual_pii", confidence=0.7)
        # Entropy heuristic
        if self._entropy(content or "") > 3.5:
            assessment.add_risk("high_entropy", confidence=0.6)
        return assessment

    def _entropy(self, s: str) -> float:
        if not s:
            return 0.0
        prob = [float(s.count(c)) / len(s) for c in set(s)]
        return -sum(p * math.log(p, 2) for p in prob)

