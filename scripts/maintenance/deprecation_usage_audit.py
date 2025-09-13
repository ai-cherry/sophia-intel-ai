#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "logs/deprecation_usage_report.md"

MARKER_PATTERNS = [
    r"@deprecated",
    r"\bDEPRECATED\b",
    r"\bDeprecated\b",
    r"#\s*deprecated",
    r"//\s*deprecated",
]

NAME_PATTERNS = [
    r"deprecated",
    r"legacy",
    r"obsolete",
    r"old",
]

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "out",
    "archives",  # leave archived items alone
}

CODE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json"}


def is_ignored(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & IGNORE_DIRS)


def gather_candidates(root: Path) -> List[Path]:
    name_re = re.compile("|".join(NAME_PATTERNS), re.IGNORECASE)
    marker_res = [re.compile(p, re.IGNORECASE) for p in MARKER_PATTERNS]
    candidates: List[Path] = []
    for p in root.rglob("*"):
        if p.is_dir() or is_ignored(p):
            continue
        if p.suffix not in CODE_EXTS:
            # consider filenames that look deprecated even if not code (rare)
            if name_re.search(p.name):
                candidates.append(p)
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        if name_re.search(p.name) or any(r.search(text) for r in marker_res):
            candidates.append(p)
    return candidates


def build_search_terms(p: Path) -> List[str]:
    stem = p.stem
    terms = {stem}
    # Add file name and common import substrings
    terms.add(p.name)
    # attempt class-like (PascalCase) and module-like (snake) variants
    if "_" in stem:
        parts = stem.split("_")
        terms.add("".join(s.capitalize() for s in parts))
    else:
        # camel to snake
        snake = re.sub(r"(?<!^)(?=[A-Z])", "_", stem).lower()
        if snake != stem:
            terms.add(snake)
    return sorted(terms)


def find_references(root: Path, target: Path, terms: List[str]) -> List[Tuple[Path, int]]:
    refs: List[Tuple[Path, int]] = []
    term_re = re.compile(r"(" + "|".join(re.escape(t) for t in terms) + r")")
    for p in root.rglob("*"):
        if p.is_dir() or is_ignored(p) or p == target:
            continue
        if p.suffix not in CODE_EXTS:
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        count = 0
        # quick checks for import-like usage
        if term_re.search(text):
            count = len(term_re.findall(text))
        if count:
            refs.append((p, count))
    return refs


def main() -> int:
    root = ROOT
    candidates = gather_candidates(root)
    items = []
    for c in candidates:
        terms = build_search_terms(c)
        refs = find_references(root, c, terms)
        total = sum(n for _, n in refs)
        items.append((c, total, refs))

    # Sort: zero refs first, then by total refs
    items.sort(key=lambda x: (x[1], str(x[0])))

    lines: List[str] = []
    lines.append("# Deprecation Usage Audit\n")
    lines.append("This report lists files flagged as deprecated/legacy/old or containing deprecation markers, along with reference counts across the repo.\n")
    lines.append("\n")
    lines.append("## Summary\n")
    zero = [str(p) for p, total, _ in items if total == 0]
    lines.append(f"- Candidates with zero references: {len(zero)}\n")
    lines.append(f"- Total candidates: {len(items)}\n")
    lines.append("\n")

    if zero:
        lines.append("## Likely Safe to Remove (no references found)\n")
        for z in zero:
            lines.append(f"- `{z}`\n")
        lines.append("\n")

    lines.append("## Detailed Results\n")
    for p, total, refs in items:
        lines.append(f"### `{p}` — references: {total}\n")
        if not refs:
            lines.append("- No references found.\n\n")
            continue
        # Show up to a few referencing files
        for ref_path, count in sorted(refs, key=lambda x: -x[1])[:10]:
            rel = ref_path.relative_to(root)
            lines.append(f"- `{rel}` — {count}\n")
        lines.append("\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines))
    print(f"Wrote report: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
