#!/usr/bin/env python3
"""
Nuclear option: force doc consolidation and delete non-canonical files/dirs.
This script is intentionally destructive.
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
KILL_DIRS = [".", ".claude", ".cursor", ".sophia"]
KILL_FILES = []  # handled by consolidate_docs + policy checks
def rm_dirs() -> list[str]:
    removed: list[str] = []
    for d in KILL_DIRS:
        p = ROOT / d
        if p.exists():
            shutil.rmtree(p)
            removed.append(d)
    return removed
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true", help="Execute destructive actions")
    args = ap.parse_args()
    if not args.confirm:
        print("⚠️ Use --confirm to execute destructive cleanup.")
        return 1
    # Consolidate and delete root docs
    from scripts.consolidate_docs import consolidate
    merged, deleted = consolidate(dry_run=False)
    print(f"📚 Consolidated {len(merged)} items into canonical docs")
    # Remove AI dirs
    removed_dirs = rm_dirs()
    if removed_dirs:
        print("🗂️ Removed directories:")
        for d in removed_dirs:
            print(f"  - {d}")
    print("✅ Nuke complete")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
