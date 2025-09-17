#!/usr/bin/env python3
"""Repository-wide environment reference inventory.

Scans the codebase for references to environment template files so we can
identify non-canonical usage (e.g., `.env.master`, `.env.template`). The tool
outputs a JSON summary by default and can optionally emit a table for quick
CLI review.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

# Environment filename patterns we want to track explicitly.
KNOWN_PATTERNS: Sequence[str] = (
    ".env.template",
    ".env.master",
    ".env.template",
    ".env.template",
)

# Directories that should be ignored when scanning. These cover third-party
# artifacts, caches, and generated assets that add noise or slow the walk.
EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    "logs",
    "artifacts",
    "tmp",
    ".mypy_cache",
    ".pytest_cache",
}


def iter_repository_files(root: Path) -> Iterable[Path]:
    """Yield text-like files from the repository, pruning excluded dirs."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Mutate dirnames in-place so os.walk() prunes excluded directories.
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for filename in filenames:
            path = Path(dirpath) / filename
            if not path.is_file():
                continue
            if path.suffix in {".pyc", ".so", ".dll"}:
                continue
            yield path


def scan_file_for_patterns(path: Path, patterns: Sequence[str]) -> Dict[str, List[Dict[str, str]]]:
    """Return all matching pattern references for a file."""
    matches: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return matches

    # Quick check to bypass files that have no `.env` substring at all.
    if ".env" not in text:
        return matches

    lines = text.splitlines()
    lowered_patterns = {pattern: pattern.lower() for pattern in patterns}

    for line_number, line in enumerate(lines, start=1):
        lowered_line = line.lower()
        if ".env" not in lowered_line:
            continue
        for pattern, lowered_pattern in lowered_patterns.items():
            if lowered_pattern in lowered_line:
                matches[pattern].append(
                    {
                        "file": str(path.as_posix()),
                        "line": line_number,
                        "content": line.strip(),
                    }
                )
    return matches


def aggregate_inventory(root: Path, patterns: Sequence[str]) -> Dict[str, List[Dict[str, str]]]:
    """Create aggregated mapping of pattern -> occurrences across repo."""
    inventory: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for file_path in iter_repository_files(root):
        file_matches = scan_file_for_patterns(file_path, patterns)
        for pattern, occurrences in file_matches.items():
            inventory[pattern].extend(occurrences)
    return inventory


def emit_table(inventory: Dict[str, List[Dict[str, str]]]) -> str:
    """Render a human-readable table summarizing counts per pattern."""
    header = f"{'Pattern':<20} | {'Count':>5}"
    separator = "-" * len(header)
    rows = [header, separator]
    for pattern in KNOWN_PATTERNS:
        count = len(inventory.get(pattern, []))
        rows.append(f"{pattern:<20} | {count:>5}")
    return "\n".join(rows)


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description="Inventory environment file references across the repository.")
    parser.add_argument(
        "--root",
        default=Path.cwd(),
        type=Path,
        help="Repository root to scan (default: current working directory).",
    )
    parser.add_argument(
        "--format",
        choices=("json", "table"),
        default="json",
        help="Output format. 'json' includes per-occurrence detail; 'table' summarizes counts.",
    )
    parser.add_argument(
        "--include-canonical",
        action="store_true",
        help="If set, include occurrences of the canonical template (`.env.template`) in the output. By default this pattern is omitted to keep the report focused on non-conforming usage.",
    )
    parser.add_argument(
        "--fail-noncanonical",
        action="store_true",
        help="Exit with status 3 if deprecated environment patterns are found in the tree.",
    )

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if not root.exists():
        print(f"❌ Root path does not exist: {root}", file=sys.stderr)
        return 2

    inventory = aggregate_inventory(root, KNOWN_PATTERNS)

    if not args.include_canonical:
        inventory.pop(".env.template", None)

    if args.format == "table":
        print(emit_table(inventory))
    else:
        summary = {
            "root": root.as_posix(),
            "patterns": KNOWN_PATTERNS,
            "include_canonical": args.include_canonical,
            "inventory": inventory,
        }
        print(json.dumps(summary, indent=2))

    if args.fail_noncanonical:
        offenders = {
            pattern: len(inventory.get(pattern, []))
            for pattern in (".env.master", ".env.template", ".env.template")
        }
        offenders = {pattern: count for pattern, count in offenders.items() if count}
        if offenders:
            details = ", ".join(f"{pattern}: {count}" for pattern, count in offenders.items())
            print(f"❌ Non-canonical environment references found -> {details}", file=sys.stderr)
            return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
