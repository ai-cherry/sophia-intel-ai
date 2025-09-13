#!/usr/bin/env python3
"""
Simple eval runner for curated evals.
- Scans evals/golden_qa/*.jsonl and prints pass counts for exact-match answers.
- This is a baseline runner; extend as needed.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "evals" / "golden_qa"

def load_jsonl(p: Path):
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue

def main() -> int:
    files = sorted(GOLDEN.glob("*.jsonl"))
    if not files:
        print("No golden_qa/*.jsonl found. Add cases to evals/golden_qa.")
        return 0
    total = 0
    passed = 0
    for f in files:
        for item in load_jsonl(f):
            total += 1
            # Expect {"id":..., "question":..., "expected": ..., "answer": ...}
            exp = (item.get("expected") or item.get("answer"))
            got = item.get("got")
            if got is None:
                # if runner isn't invoked with model responses, treat as pending
                continue
            if isinstance(exp, str) and isinstance(got, str) and exp.strip() == got.strip():
                passed += 1
    print(json.dumps({"suite": "golden_qa", "total": total, "passed": passed}))
    return 0

if __name__ == "__main__":
    sys.exit(main())

