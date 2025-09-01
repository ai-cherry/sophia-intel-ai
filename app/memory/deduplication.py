"""MinHash based deduplication utilities for memory entries."""

from __future__ import annotations

import hashlib
import json
from typing import Iterable, List


def compute_minhash(content: str, num_perm: int = 64) -> List[int]:
    """Compute a simple MinHash signature for the given content."""
    tokens = content.split()
    if not tokens:
        return [0] * num_perm
    signature: List[int] = []
    for i in range(num_perm):
        min_val = None
        for token in tokens:
            h = hashlib.sha256(f"{i}_{token}".encode()).hexdigest()
            v = int(h, 16)
            if min_val is None or v < min_val:
                min_val = v
        signature.append(min_val or 0)
    return signature


def minhash_similarity(sig1: Iterable[int], sig2: Iterable[int]) -> float:
    """Estimate Jaccard similarity between two MinHash signatures."""
    sig1 = list(sig1)
    sig2 = list(sig2)
    if len(sig1) != len(sig2) or not sig1:
        return 0.0
    matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
    return matches / len(sig1)


def group_near_duplicates(entries: List[dict], threshold: float = 0.8) -> dict:
    """Group near-duplicate entries by topic based on MinHash similarity."""
    duplicates: dict[str, List[dict]] = {}
    for i, a in enumerate(entries):
        sig_a = a.get("minhash") or []
        for b in entries[i + 1 :]:
            if a.get("topic") != b.get("topic"):
                continue
            sig_b = b.get("minhash") or []
            if minhash_similarity(sig_a, sig_b) >= threshold:
                duplicates.setdefault(a["topic"], []).append(
                    {
                        "a": a.get("hash_id"),
                        "b": b.get("hash_id"),
                        "similarity": minhash_similarity(sig_a, sig_b),
                    }
                )
    return duplicates
