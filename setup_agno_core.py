#!/usr/bin/env python3
import os
import asyncio
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger("AgnoSetup")

REQUIRED_ENV = [
    # Placeholder for real keys; do not store secrets in repo
    # Keep validation light to avoid blocking local dev
]

STRUCTURE = [
    "agno_core/agents",
    "agno_core/teams",
    "agno_core/swarms",
    "agno_core/memory",
    "agno_core/tools",
    "agno_core/playground",
]

ORCHESTRATOR_PATH = Path("agno_core/orchestrator.py")

ORCHESTRATOR_CODE = """
from __future__ import annotations
from typing import Dict, Any

try:
    # Optional import; only required when running the HTTP app
    from fastapi import FastAPI
except Exception:  # pragma: no cover
    FastAPI = None  # type: ignore


class Orchestrator:
    def __init__(self) -> None:
        self.agents: Dict[str, Any] = {}
        self.teams: Dict[str, Any] = {}

    def health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "agents": len(self.agents),
            "teams": len(self.teams),
        }


def build_app() -> "FastAPI":
    if FastAPI is None:
        raise RuntimeError("FastAPI not installed; cannot build HTTP app")
    app = FastAPI(title="Agno Orchestrator")
    orch = Orchestrator()

    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        return orch.health()

    return app
""".lstrip()


async def setup_agno_system() -> None:
    logger.info("Setting up Agno Core structure…")

    # Validate environment (non-fatal hints only, to avoid blocking dev)
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        logger.warning("Missing env vars (set via your local env manager): %s", ", ".join(missing))

    for d in STRUCTURE:
        Path(d).mkdir(parents=True, exist_ok=True)

    # Ensure package init
    pkg_init = Path("agno_core/__init__.py")
    if not pkg_init.exists():
        pkg_init.write_text("\n")

    # Create orchestrator module if absent
    if not ORCHESTRATOR_PATH.exists():
        ORCHESTRATOR_PATH.write_text(ORCHESTRATOR_CODE)
        logger.info("Created %s", ORCHESTRATOR_PATH)
    else:
        logger.info("Orchestrator already present: %s", ORCHESTRATOR_PATH)

    logger.info("Agno core setup complete!")


if __name__ == "__main__":
    asyncio.run(setup_agno_system())

