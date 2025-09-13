from __future__ import annotations

"""
Shim to load central repo environment exactly once.

This delegates to `app.core.env.load_env_once()` so all tooling that imports
`builder_cli.lib.env` gets the same single-source server-side env behavior.
"""

from app.core.env import load_env_once as _load_env_once


def load_central_env() -> None:
    """Load repo `.env.master` once (idempotent)."""
    _load_env_once()

