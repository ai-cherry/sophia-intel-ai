from __future__ import annotations

import hashlib
from difflib import SequenceMatcher
from typing import Any, Dict, List


def _norm_str(s: Any) -> str:
    return str(s or "").strip().lower()


class DedupService:
    def __init__(self, policy: Dict[str, Any]) -> None:
        self.policy = policy or {}
        self.order: List[str] = self.policy.get("order", ["content_hash", "row_keys", "fuzzy"])
        self.row_keys: List[str] = self.policy.get("row_keys", ["email", "external_id"])  # default guesses
        self.fuzzy_fields: List[str] = self.policy.get("fuzzy_fields", ["name", "title"])
        self.fuzzy_threshold: float = float(self.policy.get("fuzzy_threshold", 0.88))

    def content_hash(self, content: str) -> str:
        return hashlib.sha256(_norm_str(content).encode()).hexdigest()

    def row_key_signature(self, record: Dict[str, Any]) -> str:
        parts = [f"{k}:{_norm_str(record.get(k))}" for k in self.row_keys]
        base = "|".join(parts)
        return hashlib.sha256(base.encode()).hexdigest()

    def fuzzy_similar(self, a: str, b: str) -> bool:
        return SequenceMatcher(None, _norm_str(a), _norm_str(b)).ratio() >= self.fuzzy_threshold

    def is_duplicate(self, new_item: Dict[str, Any], existing: List[Dict[str, Any]]) -> bool:
        """Decide duplication against existing items according to policy order.

        Each item is expected to have optional 'content', 'record' fields for respective checks.
        """
        for rule in self.order:
            if rule == "content_hash":
                new_hash = self.content_hash(new_item.get("content", ""))
                for e in existing:
                    if self.content_hash(e.get("content", "")) == new_hash:
                        return True
            elif rule == "row_keys":
                sig = self.row_key_signature(new_item.get("record", {}))
                for e in existing:
                    if self.row_key_signature(e.get("record", {})) == sig:
                        return True
            elif rule == "fuzzy":
                for e in existing:
                    for f in self.fuzzy_fields:
                        if self.fuzzy_similar(new_item.get("record", {}).get(f, ""), e.get("record", {}).get(f, "")):
                            return True
        return False

