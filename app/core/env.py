"""
Unified environment loader (silent, idempotent).

Contract:
- Load only from repo-local `.env.master` if present.
- No fallbacks, no prompts, no stdout noise.
- Safe to call multiple times (no-ops after first).
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional
_loaded = False
def _load_plain(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())
def load_env_once() -> None:
    """Load environment once from repo `.env.master` only."""
    global _loaded
    if _loaded:
        return
    repo_root = Path(__file__).resolve().parents[2]  # app/core/ -> app/ -> repo root
    env_path = repo_root / ".env.master"
    _load_plain(env_path)
    _loaded = True
