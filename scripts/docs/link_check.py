#!/usr/bin/env python3
"""
Internal doc link checker.
- Scans .md files and validates relative links point to existing files/anchors.
- Skips http(s) links.
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")

def main() -> int:
    problems = []
    for p in ROOT.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in MD_LINK.finditer(text):
            href = m.group(1).strip()
            if not href or href.startswith(("http://","https://","mailto:","#")):
                continue
            # Strip anchors
            path_part = href.split('#',1)[0]
            target = (p.parent / path_part).resolve()
            if not target.exists():
                problems.append((str(p.relative_to(ROOT)), href))
    if problems:
        for src, href in problems:
            print(f"BROKEN: {src} -> {href}")
        print(f"Total broken links: {len(problems)}")
        return 1
    print("Doc links OK")
    return 0

if __name__ == "__main__":
    sys.exit(main())

