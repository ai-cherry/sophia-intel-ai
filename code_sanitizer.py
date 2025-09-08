#!/usr/bin/env python3
"""
Code Sanitizer (safe stub)
- Replaced malformed implementation to resolve syntax errors.
- Performs minimal archive purge and placeholder scan with a safe pattern list.
"""

import logging
import re
from pathlib import Path
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

SAFE_FORBIDDEN_PATTERNS = [
    r"\bTEMP\b",
    r"\bPLACEHOLDER\b",
]

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "venv",
    "venv-sophia",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}


def get_text_files(root: Path) -> List[Path]:
    exts = {".py", ".js", ".ts", ".yaml", ".yml", ".json", ".md", ".txt", ".sh", ".env"}
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in exts and not any(d in p.parts for d in EXCLUDE_DIRS):
            files.append(p)
    return files


def purge_archives(root: Path) -> None:
    for pattern in [
        "*.old",
        "*.bak",
        "*.archive",
        "*.deprecated",
        "*.backup",
        "*.orig",
        "*.tmp",
        "*.temp",
    ]:
        for fp in root.rglob(pattern):
            if any(d in fp.parts for d in EXCLUDE_DIRS):
                continue
            try:
                fp.unlink()
                logger.info(f"Deleted archive file: {fp}")
            except Exception as e:
                logger.warning(f"Could not delete {fp}: {e}")


def scan_placeholders(root: Path) -> int:
    issues = 0
    for fp in get_text_files(root):
        try:
            content = fp.read_text(encoding="utf-8", errors="ignore")
            for pattern in SAFE_FORBIDDEN_PATTERNS:
                for m in re.finditer(pattern, content, re.IGNORECASE):
                    line = content[: m.start()].count("\n") + 1
                    logger.warning(f"{fp}:{line} - Found forbidden pattern")
                    issues += 1
        except Exception as e:
            logger.warning(f"Failed to scan {fp}: {e}")
    return issues


def main() -> int:
    root = Path(".")
    purge_archives(root)
    issues = scan_placeholders(root)
    logger.info(f"Sanitizer completed. Issues found: {issues}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
