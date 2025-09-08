"""
Unified environment loader for application entrypoints.

Loads in priority order:
  1) ~/.config/artemis/env
  2) .env
  3) .env.local

Safe to call multiple times (no-ops after first).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

_loaded = False


def _load_plain(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())


def load_env_once() -> None:
    global _loaded
    if _loaded:
        return

    # Try python-dotenv if available
    try:
        from dotenv import load_dotenv  # type: ignore

        load_dotenv(Path("~/.config/artemis/env").expanduser(), override=False)
        load_dotenv(Path(".env").resolve(), override=False)
        load_dotenv(Path(".env.local").resolve(), override=False)
    except Exception:
        # Fallback to plain loader
        _load_plain(Path("~/.config/artemis/env").expanduser())
        _load_plain(Path(".env").resolve())
        _load_plain(Path(".env.local").resolve())

    _loaded = True

