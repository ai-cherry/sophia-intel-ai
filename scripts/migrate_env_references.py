#!/usr/bin/env python3
"""Migration helper for environment configuration standardization.

Rewrites references to deprecated environment template filenames
(e.g., `.env.master`, `.env.example`) to the canonical `.env.template`.

The tool runs in dry-run mode by default so teams can review planned
modifications. Use `--apply` to write the updates after approval.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

LEGACY_TO_CANONICAL: Tuple[Tuple[str, str], ...] = (
    (".env.master", ".env.template"),
    (".env.example", ".env.template"),
    ("env.example", ".env.template"),
)

EXCLUDED_DIRS = {
    ".git",
    "logs",
    "tmp",
    "artifacts",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}

TEXT_SUFFIXES = {
    ".py",
    ".sh",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".txt",
    "",
}


@dataclass
class PlannedChange:
    path: Path
    updated_text: str
    legacy_counts: Dict[str, int]


def iter_candidate_files(root: Path) -> Iterable[Path]:
    """Yield candidate files that might require migration."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            if not path.is_file():
                continue
            if path.suffix not in TEXT_SUFFIXES:
                continue
            yield path


def plan_migration(path: Path, replacements: Sequence[Tuple[str, str]]) -> PlannedChange | None:
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None

    updated = original
    counter: Counter[str] = Counter()

    for legacy, target in replacements:
        occurrences = updated.count(legacy)
        if not occurrences:
            continue
        updated = updated.replace(legacy, target)
        counter[legacy] += occurrences

    if not counter:
        return None

    return PlannedChange(path=path, updated_text=updated, legacy_counts=dict(counter))


def summarize_changes(changes: List[PlannedChange]) -> None:
    print("📋 Migration summary:")
    for change in changes:
        details = ", ".join(f"{legacy} -> {count}" for legacy, count in sorted(change.legacy_counts.items()))
        print(f" - {change.path.as_posix()} ({details})")


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Rewrite deprecated environment file references to .env.template.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to scan.")
    parser.add_argument("--apply", action="store_true", help="Write changes to disk (default is dry-run).")

    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.exists():
        print(f"❌ Root path does not exist: {root}", file=sys.stderr)
        return 2

    changes = []
    for file_path in iter_candidate_files(root):
        planned = plan_migration(file_path, LEGACY_TO_CANONICAL)
        if planned:
            changes.append(planned)

    if not changes:
        print("✅ No deprecated environment references found.")
        return 0

    summarize_changes(changes)

    if not args.apply:
        print("\nDry run complete. Re-run with --apply to write changes.")
        return 0

    for change in changes:
        change.path.write_text(change.updated_text, encoding="utf-8")

    print(f"✅ Applied updates to {len(changes)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
