#!/usr/bin/env python3
"""
Consolidate root-level documentation into canonical files and delete the rest.
Rules:
- _* and ARCHITECTURE_* -> ARCHITECTURE.md
- PHASE_* and IMPLEMENTATION_* -> ROADMAP.md
- DEPLOYMENT_* and DEPLOY_*     -> DEPLOYMENT_GUIDE.md
- *_REPORT*, *_AUDIT*, *_STATUS* -> TROUBLESHOOTING.md
Only processes files in the repository root (no subdirectories).
"""
from __future__ import annotations
import argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
KEEP = {
    "README.md",
    "LOCAL_DEV_AND_DEPLOYMENT.md",
    "ARCHITECTURE.md",
    "DEPLOYMENT_GUIDE.md",
    "API_REFERENCE.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "TROUBLESHOOTING.md",
    "INTEGRATIONS.md",
    "SECURITY.md",
    "ROADMAP.md",
}
MERGE_MAP = {
    "ARCHITECTURE.md": ("_*.md", "ARCHITECTURE_*.md"),
    "ROADMAP.md": ("PHASE_*.md", "IMPLEMENTATION_*.md"),
    "DEPLOYMENT_GUIDE.md": ("DEPLOYMENT_*.md", "DEPLOY_*.md"),
    "TROUBLESHOOTING.md": ("*_REPORT*.md", "*_AUDIT*.md", "*_STATUS*.md"),
}
def root_glob(pattern: str) -> list[Path]:
    return [p for p in ROOT.glob(pattern) if p.parent == ROOT]
def append_with_header(target: Path, src: Path) -> None:
    header = f"\n\n---\n## Consolidated from {src.name}\n\n"
    existing = target.read_text() if target.exists() else ""
    target.write_text(existing + header + src.read_text())
def consolidate(dry_run: bool = False) -> tuple[list[str], list[str]]:
    merged = []
    deleted = []
    # Ensure TROUBLESHOOTING.md exists if referenced
    for target in MERGE_MAP.keys():
        if target not in KEEP:
            KEEP.add(target)
    (ROOT / "TROUBLESHOOTING.md").touch(exist_ok=True)
    for target, patterns in MERGE_MAP.items():
        tpath = ROOT / target
        for pat in patterns:
            for f in root_glob(pat):
                if f.name == target:
                    continue
                merged.append(f"{f.name} -> {target}")
                if not dry_run:
                    append_with_header(tpath, f)
                    f.unlink()
                    deleted.append(str(f))
    # Delete any other root-level markdown not in KEEP
    for f in ROOT.glob("*.md"):
        if f.name in KEEP:
            continue
        # Already deleted? skip
        if not f.exists():
            continue
        if not dry_run:
            f.unlink()
            deleted.append(str(f))
    return merged, deleted
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Show actions without modifying files")
    args = ap.parse_args()
    merged, deleted = consolidate(dry_run=args.dry_run)
    print("📚 Consolidation plan:")
    for m in merged:
        print(f"  - {m}")
    print(f"\n🗑️ Deleted: {len(deleted)} files")
    for d in deleted:
        print(f"  - {d}")
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
