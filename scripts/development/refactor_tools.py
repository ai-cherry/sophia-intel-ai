#!/usr/bin/env python3
"""
Refactoring helper utilities for Phase 2

Features:
- Discover large Python files by size
- Scan for HTTP client imports (requests/httpx/aiohttp)
- Probe imports to verify refactor proxies work
- Generate proxy shim content (optional write)

Usage examples:
  python3 scripts/development/refactor_tools.py discover --path app --min-kb 50
  python3 scripts/development/refactor_tools.py scan-http --path app
  python3 scripts/development/refactor_tools.py probe-import --module app.artemis.agent_factory
  python3 scripts/development/refactor_tools.py gen-proxy --old app/artemis/agent_factory.py --new app/artemis/factories/agent_factory.py --write
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


def _is_python_file(path: Path) -> bool:
    return path.suffix == ".py" and path.is_file()


def human_kb(size_bytes: int) -> float:
    return round(size_bytes / 1024.0, 1)


def discover_large_files(root: Path, min_kb: int) -> List[dict]:
    results: List[dict] = []
    for p in root.rglob("*.py"):
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size >= min_kb * 1024:
            results.append({"path": str(p), "size_kb": human_kb(size)})
    results.sort(key=lambda x: x["size_kb"], reverse=True)
    return results


HTTP_IMPORT_RE = re.compile(
    r"^(\s*from\s+(requests|httpx|aiohttp)\b|\s*import\s+(requests|httpx|aiohttp)\b)"
)


def scan_http_imports(root: Path) -> List[dict]:
    findings: List[dict] = []
    for p in root.rglob("*.py"):
        try:
            with p.open("r", encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, start=1):
                    if HTTP_IMPORT_RE.search(line):
                        findings.append(
                            {"file": str(p), "line": i, "text": line.strip()}
                        )
        except OSError:
            continue
    return findings


def probe_import(module: str) -> dict:
    try:
        importlib.import_module(module)
        return {"module": module, "ok": True}
    except Exception as e:  # noqa: BLE001 - show any failure
        return {
            "module": module,
            "ok": False,
            "error": str(e.__class__.__name__),
            "detail": str(e),
        }


PROXY_TEMPLATE = (
    "from warnings import warn\n"
    'warn("Module moved to {new_module}; this import path is deprecated", '
    "DeprecationWarning, stacklevel=2)\n"
    "from {new_module} import *\n"
)


def gen_proxy_content(new_module: str) -> str:
    return PROXY_TEMPLATE.format(new_module=new_module)


def write_proxy(old_path: Path, new_module: str) -> None:
    old_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.write_text(gen_proxy_content(new_module), encoding="utf-8")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2 refactor helper tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_discover = sub.add_parser("discover", help="List .py files over a size threshold")
    p_discover.add_argument("--path", type=Path, default=Path("app"))
    p_discover.add_argument("--min-kb", type=int, default=50)

    p_scan = sub.add_parser("scan-http", help="Scan for requests/httpx/aiohttp imports")
    p_scan.add_argument("--path", type=Path, default=Path("app"))

    p_probe = sub.add_parser(
        "probe-import", help="Attempt to import a module and report result"
    )
    p_probe.add_argument("--module", required=True)

    p_proxy = sub.add_parser(
        "gen-proxy", help="Generate or write a proxy shim for moved module"
    )
    p_proxy.add_argument(
        "--old",
        type=Path,
        required=True,
        help="Old file path to host proxy (e.g., app/pkg/file.py)",
    )
    p_proxy.add_argument(
        "--new",
        dest="new_module",
        required=True,
        help="New module path (e.g., app.pkg.file)",
    )
    p_proxy.add_argument(
        "--write",
        action="store_true",
        help="Write proxy to --old path (default prints content)",
    )

    args = parser.parse_args(argv)

    if args.cmd == "discover":
        results = discover_large_files(args.path, args.min_kb)
        print(
            json.dumps(
                {"count": len(results), "min_kb": args.min_kb, "results": results},
                indent=2,
            )
        )
        return 0

    if args.cmd == "scan-http":
        findings = scan_http_imports(args.path)
        print(json.dumps({"count": len(findings), "results": findings}, indent=2))
        return 0

    if args.cmd == "probe-import":
        result = probe_import(args.module)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "gen-proxy":
        content = gen_proxy_content(args.new_module)
        if args.write:
            write_proxy(args.old, args.new_module)
            print(json.dumps({"wrote": str(args.old), "new_module": args.new_module}))
        else:
            print(content)
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
