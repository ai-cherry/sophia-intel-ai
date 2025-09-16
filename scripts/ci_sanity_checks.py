"""
Lightweight CI sanity checks:
- Compile all Python files
- Validate JSON (excluding secrets and logs)
- Validate YAML (excluding Helm templates and mkdocs custom tags)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None  # YAML validation will be skipped


EXCLUDE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build"}


def iter_files(root: str | Path, exts: Iterable[str]) -> Iterable[Path]:
    root = Path(root)
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        parts = set(p.parts)
        if parts & EXCLUDE_DIRS:
            continue
        if any(str(p).endswith(ext) for ext in exts):
            yield p


def check_python() -> list[str]:
    errors: list[str] = []
    for fp in iter_files(".", [".py"]):
        try:
            compile(fp.read_bytes(), str(fp), "exec")
        except SyntaxError as e:  # pragma: no cover
            errors.append(f"PY: {fp}:{e.lineno}:{e.offset} {e.msg}")
    return errors


def check_json() -> list[str]:
    errors: list[str] = []
    for fp in iter_files(".", [".json"]):
        # Exclude known non-JSON or NDJSON locations
        if any(part in {"secrets", "logs"} for part in Path(fp).parts):
            continue
        try:
            json.load(open(fp, "r", encoding="utf-8"))
        except Exception as e:  # pragma: no cover
            errors.append(f"JSON: {fp} -> {str(e).splitlines()[0]}")
    return errors


def check_yaml() -> list[str]:
    if yaml is None:
        return ["YAML: pyyaml not available; skipping"]
    errors: list[str] = []
    for fp in iter_files(".", [".yml", ".yaml"]):
        s = str(fp)
        if "/templates/" in s or s.endswith("mkdocs.yml"):
            continue
        try:
            list(yaml.safe_load_all(open(fp, "r", encoding="utf-8")))
        except Exception as e:  # pragma: no cover
            errors.append(f"YAML: {fp} -> {str(e).splitlines()[0]}")
    return errors


def main() -> int:
    failures: list[str] = []
    failures += check_python()
    failures += check_json()
    failures += check_yaml()
    if failures:
        print("Sanity check errors:")
        for f in failures:
            print(" -", f)
        return 1
    print("All sanity checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

