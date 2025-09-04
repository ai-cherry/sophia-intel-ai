from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from . import __version__


@dataclass
class StructureStats:
    total_files: int
    total_dirs: int
    by_ext: Dict[str, int]
    top_files: List[Tuple[str, int]]  # (path, size_bytes)
    top_dirs: List[Tuple[str, int]]   # (path, size_bytes)


def human_bytes(n: int) -> str:
    # Simple human-readable formatter without extra deps
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    f = float(n)
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.1f} {units[i]}"


def scan_structure(root: Path, top: int = 10) -> StructureStats:
    by_ext: Counter[str] = Counter()
    file_sizes: List[Tuple[Path, int]] = []
    dir_sizes: Dict[Path, int] = defaultdict(int)

    total_files = 0
    total_dirs = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        total_dirs += 1
        # Accumulate directory sizes from file sizes directly under this dir
        for name in filenames:
            p = dp / name
            try:
                size = p.stat().st_size
            except OSError:
                continue
            total_files += 1
            file_sizes.append((p, size))
            dir_sizes[dp] += size
            ext = p.suffix.lower() or "(noext)"
            by_ext[ext] += 1

    # Propagate sizes up so top-level directories reflect cumulative sizes
    for d in sorted(dir_sizes.keys(), key=lambda x: len(x.parts), reverse=True):
        parent = d.parent
        if parent != d and parent in dir_sizes:
            dir_sizes[parent] += dir_sizes[d]

    top_files = sorted(file_sizes, key=lambda x: x[1], reverse=True)[:top]
    top_dirs = sorted(dir_sizes.items(), key=lambda x: x[1], reverse=True)[:top]

    return StructureStats(
        total_files=total_files,
        total_dirs=total_dirs,
        by_ext=dict(by_ext.most_common(50)),
        top_files=[(str(p), s) for p, s in top_files],
        top_dirs=[(str(p), s) for p, s in top_dirs],
    )


def print_structure_text(stats: StructureStats, root: Path, top: int) -> None:
    print(f"📁 Codebase structure for: {root}")
    print(f"- Directories: {stats.total_dirs}")
    print(f"- Files: {stats.total_files}")
    print("- Top file extensions:")
    for ext, count in list(stats.by_ext.items())[:10]:
        print(f"  • {ext}: {count}")
    print(f"- Top {top} largest files:")
    for path, size in stats.top_files:
        print(f"  • {path} — {human_bytes(size)}")
    print(f"- Top {top} heaviest directories:")
    for path, size in stats.top_dirs:
        print(f"  • {path} — {human_bytes(size)}")


def cmd_codebase_structure(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    if not root.exists():
        print(f"error: path not found: {root}", file=sys.stderr)
        return 2
    stats = scan_structure(root, top=args.top)
    if args.format == "json":
        payload = {
            "path": str(root),
            "total_files": stats.total_files,
            "total_dirs": stats.total_dirs,
            "by_ext": stats.by_ext,
            "top_files": [{"path": p, "size_bytes": s} for p, s in stats.top_files],
            "top_dirs": [{"path": p, "size_bytes": s} for p, s in stats.top_dirs],
        }
        print(json.dumps(payload, indent=2))
    else:
        print_structure_text(stats, root, args.top)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit",
        description="Project audit CLI",
    )
    parser.add_argument("--version", action="version", version=f"audit {__version__}")

    subparsers = parser.add_subparsers(dest="category", metavar="category")

    # audit codebase ...
    codebase = subparsers.add_parser("codebase", help="Codebase-related audits")
    codebase_sub = codebase.add_subparsers(dest="command", metavar="command")

    # audit codebase structure
    structure = codebase_sub.add_parser(
        "structure",
        help="Analyze repository structure and sizes",
    )
    structure.add_argument("--path", default=".", help="Path to analyze (default: .)")
    structure.add_argument("--format", choices=["text", "json"], default="text")
    structure.add_argument("--top", type=int, default=10, help="Top N heavy files/dirs (default: 10)")
    structure.set_defaults(func=cmd_codebase_structure)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "category", None):
        parser.print_help()
        return 1
    if hasattr(args, "func"):
        return int(args.func(args))
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

