#!/usr/bin/env python3
"""
Audit script: list occurrences of 'sophia' (case-insensitive) in non-archived code/config.
Does not fail CI by default; prints a summary for manual migration tracking.
"""
from __future__ import annotations
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
IGNORE_DIRS = {'.git', 'node_modules', '__pycache__', '.next', 'dist', 'build', '.venv', 'logs', 'archives'}
PAT = re.compile(r'sophia', re.IGNORECASE)
COUNT = 0

def should_skip(p: Path) -> bool:
    return any(part in IGNORE_DIRS for part in p.parts)

def main() -> int:
    strict = '--strict' in sys.argv
    global COUNT
    for p in ROOT.rglob('*'):
        if p.is_dir() or should_skip(p):
            continue
        if p.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.lock'}:
            continue
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if PAT.search(text):
            COUNT += 1
            print(str(p.relative_to(ROOT)))
    print(f"TOTAL_FILES_WITH_ARTEMIS: {COUNT}")
    if strict and COUNT > 0:
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
