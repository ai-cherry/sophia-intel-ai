#!/usr/bin/env python3
"""
Minimal bootstrap indexer.

Seeds MCP Vector with a few repo files (if present) and runs a quick search
to warm caches. Silent on failure; prints concise status lines.
"""
from __future__ import annotations
import os
import json
from pathlib import Path
from typing import List

import requests


def post_index(vec_url: str, path: Path) -> bool:
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        r = requests.post(f"{vec_url}/index", json={"path": str(path), "content": content}, timeout=10)
        return r.status_code in (200, 201)
    except Exception:
        return False


def quick_search(vec_url: str, query: str) -> bool:
    try:
        r = requests.post(f"{vec_url}/search", json={"query": query, "limit": 1}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def main() -> None:
    port = os.getenv("MCP_VECTOR_PORT", "8085")
    vec_url = f"http://localhost:{port}"
    candidates: List[Path] = [
        Path("README.md"),
        Path("docs/ONE_TRUE_DEV_FLOW.md"),
        Path("docs/MCP_CANONICAL_SERVERS.md"),
    ]
    to_index = [p for p in candidates if p.exists()]
    if not to_index:
        print("bootstrap: no candidate files found")
        return
    ok_count = 0
    for p in to_index:
        ok = post_index(vec_url, p)
        print(f"bootstrap index {p}: {'OK' if ok else 'FAIL'}")
        ok_count += 1 if ok else 0
    srch = quick_search(vec_url, "bootstrap")
    print(f"bootstrap search: {'OK' if srch else 'FAIL'}")
    # No strict exit; env_master_check enforces roundtrip


if __name__ == "__main__":
    main()

