"""
Integration test setup

- Loads .env.local if present (via python-dotenv) so live creds work locally
- Provides a shared pytest marker `integration`
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def load_local_env() -> None:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return  # Optional dependency
    env_path = Path.cwd() / ".env.local"
    if env_path.exists():
        load_dotenv(str(env_path))

