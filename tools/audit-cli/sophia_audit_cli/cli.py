from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from . import __version__


DEFAULT_EXCLUDES = [
    "node_modules",
    ".venv",
    ".git",
    ".next",
    ".nx",
    "dist",
    "build",
    ".cache",
]


@dataclass
class StructureStats:
    total_files: int
    total_dirs: int
    by_ext: Dict[str, int]
    top_files: List[Tuple[str, int]]  # (path, size_bytes)
    top_dirs: List[Tuple[str, int]]   # (path, size_bytes)


def human_bytes(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    f = float(n)
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.1f} {units[i]}"


def _should_skip_dir(path: Path, excludes: List[str]) -> bool:
    parts = set(path.parts)
    return any(ex in parts for ex in excludes)


def scan_structure(root: Path, top: int = 10, excludes: List[str] | None = None) -> StructureStats:
    excludes = excludes or []
    by_ext: Counter[str] = Counter()
    file_sizes: List[Tuple[Path, int]] = []
    dir_sizes: Dict[Path, int] = defaultdict(int)

    total_files = 0
    total_dirs = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        # prune excluded directories
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(dp / d, excludes)]
        total_dirs += 1
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
    excludes = args.exclude or []
    stats = scan_structure(root, top=args.top, excludes=excludes)
    if args.format == "json":
        payload = {
            "path": str(root),
            "total_files": stats.total_files,
            "total_dirs": stats.total_dirs,
            "by_ext": stats.by_ext,
            "top_files": [{"path": p, "size_bytes": s} for p, s in stats.top_files],
            "top_dirs": [{"path": p, "size_bytes": s} for p, s in stats.top_dirs],
            "excludes": excludes,
        }
        print(json.dumps(payload, indent=2))
    else:
        print_structure_text(stats, root, args.top)
    return 0


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def cmd_deps_vulnerabilities(args: argparse.Namespace) -> int:
    tool = None
    if shutil.which("pip-audit"):
        tool = "pip-audit"
    elif shutil.which("safety"):
        tool = "safety"
    if tool is None:
        print("error: neither pip-audit nor safety is installed", file=sys.stderr)
        return 127

    if tool == "pip-audit":
        cmd = ["pip-audit", "--desc"]
        if args.format == "json":
            cmd += ["--format", "json"]
    else:  # safety
        cmd = ["safety", "check", "--continue-on-error"]
        if args.format == "json":
            cmd += ["--json"]

    res = _run(cmd)
    print(res.stdout)
    return res.returncode


def cmd_py_security(args: argparse.Namespace) -> int:
    if not shutil.which("bandit"):
        print("error: bandit is not installed", file=sys.stderr)
        return 127
    target = args.path
    if args.format == "json":
        cmd = ["bandit", "-r", target, "-f", "json"]
    else:
        cmd = ["bandit", "-r", target]
    res = _run(cmd)
    print(res.stdout)
    return res.returncode


def cmd_repo_size(args: argparse.Namespace) -> int:
    # Alias for structure with sensible defaults
    if not args.exclude:
        args.exclude = DEFAULT_EXCLUDES
    return cmd_codebase_structure(args)


BINARY_EXTS = {".node", ".so", ".dylib", ".dll", ".bin", ".pack", ".zip", ".tar", ".gz"}
SOURCE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".json", ".md", ".yaml", ".yml"}


def cmd_code_smells(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    excludes = args.exclude or []
    large_threshold = int(args.large_file_mb * 1024 * 1024)
    long_threshold = args.long_file_lines

    smells: Dict[str, List[Dict[str, object]]] = {
        "large_files": [],
        "long_source_files": [],
        "binary_artifacts": [],
    }

    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not _should_skip_dir(dp / d, excludes)]
        for name in filenames:
            p = dp / name
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size >= large_threshold:
                smells["large_files"].append({"path": str(p), "size_bytes": size})
            if p.suffix.lower() in BINARY_EXTS:
                smells["binary_artifacts"].append({"path": str(p), "size_bytes": size})
            if p.suffix.lower() in SOURCE_EXTS:
                try:
                    with p.open("r", encoding="utf-8", errors="ignore") as f:
                        line_count = sum(1 for _ in f)
                    if line_count >= long_threshold:
                        smells["long_source_files"].append({"path": str(p), "lines": line_count})
                except Exception:
                    pass

    # sort and trim top N
    top = args.top
    smells["large_files"] = sorted(smells["large_files"], key=lambda x: x["size_bytes"], reverse=True)[:top]
    smells["binary_artifacts"] = sorted(smells["binary_artifacts"], key=lambda x: x["size_bytes"], reverse=True)[:top]
    smells["long_source_files"] = sorted(smells["long_source_files"], key=lambda x: x["lines"], reverse=True)[:top]

    if args.format == "json":
        print(json.dumps({
            "path": str(root),
            "excludes": excludes,
            "large_file_threshold_bytes": large_threshold,
            "long_file_threshold_lines": long_threshold,
            "findings": smells,
        }, indent=2))
    else:
        print(f"🔎 Code smells for: {root}")
        print(f"- Excludes: {', '.join(excludes) if excludes else '(none)'}")
        print(f"- Large files (>{args.large_file_mb} MB):")
        for item in smells["large_files"]:
            print(f"  • {item['path']} — {human_bytes(int(item['size_bytes']))}")
        print("- Binary artifacts:")
        for item in smells["binary_artifacts"]:
            print(f"  • {item['path']} — {human_bytes(int(item['size_bytes']))}")
        print(f"- Long source files (>{long_threshold} lines):")
        for item in smells["long_source_files"]:
            print(f"  • {item['path']} — {item['lines']} lines")
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
    structure.add_argument("--exclude", action="append", help="Directory name to exclude (repeatable)")
    structure.set_defaults(func=cmd_codebase_structure)

    # audit deps vulnerabilities
    deps = subparsers.add_parser("deps", help="Dependency-related audits")
    deps_sub = deps.add_subparsers(dest="command", metavar="command")
    deps_vuln = deps_sub.add_parser("vulnerabilities", help="Scan Python dependencies for known vulnerabilities")
    deps_vuln.add_argument("--format", choices=["text", "json"], default="text")
    deps_vuln.set_defaults(func=cmd_deps_vulnerabilities)

    # audit py security
    py = subparsers.add_parser("py", help="Python code audits")
    py_sub = py.add_subparsers(dest="command", metavar="command")
    py_sec = py_sub.add_parser("security", help="Run Bandit security linter")
    py_sec.add_argument("--path", default="app/", help="Path to scan (default: app/)")
    py_sec.add_argument("--format", choices=["text", "json"], default="text")
    py_sec.set_defaults(func=cmd_py_security)

    # audit repo size (alias)
    repo = subparsers.add_parser("repo", help="Repository-wide audits")
    repo_sub = repo.add_subparsers(dest="command", metavar="command")
    repo_size = repo_sub.add_parser("size", help="Summarize repository size (excludes heavy dirs by default)")
    repo_size.add_argument("--path", default=".", help="Path to analyze (default: .)")
    repo_size.add_argument("--format", choices=["text", "json"], default="text")
    repo_size.add_argument("--top", type=int, default=10)
    repo_size.add_argument("--exclude", action="append", help="Directory name to exclude (repeatable)")
    repo_size.set_defaults(func=cmd_repo_size)

    # audit code smells
    smells = subparsers.add_parser("smells", help="Code smell heuristics")
    smells.add_argument("--path", default=".")
    smells.add_argument("--exclude", action="append", help="Directory name to exclude (repeatable)")
    smells.add_argument("--large-file-mb", type=float, default=10.0)
    smells.add_argument("--long-file-lines", type=int, default=2000)
    smells.add_argument("--top", type=int, default=10)
    smells.add_argument("--format", choices=["text", "json"], default="text")
    smells.set_defaults(func=cmd_code_smells)

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

