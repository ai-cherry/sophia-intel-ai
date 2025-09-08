"""
Integrations Health Endpoints for Sophia
Checks configuration and basic readiness for core business integrations.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.core.env import load_env_once

load_env_once()

router = APIRouter(prefix="/health", tags=["health"])


def _env_present(*keys: str) -> bool:
    return all(bool(os.getenv(k)) for k in keys)


def _status(ok: bool, details: str = "") -> Dict[str, Any]:
    return {
        "ok": ok,
        "details": details,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/integrations")
def integrations_health() -> Dict[str, Any]:
    """Return health/config status for business integrations used by Sophia.

    This is a configuration-level check (no external calls) to remain fast and safe in local dev.
    """
    return {
        "salesforce": _status(
            _env_present(
                "SALESFORCE_INSTANCE_URL",
                "SALESFORCE_CLIENT_ID",
                "SALESFORCE_CLIENT_SECRET",
                "SALESFORCE_USERNAME",
                "SALESFORCE_PASSWORD",
                "SALESFORCE_SECURITY_TOKEN",
            ),
            "requires: SALESFORCE_*",
        ),
        "gong": _status(
            _env_present("GONG_ACCESS_KEY", "GONG_CLIENT_SECRET"),
            "requires: GONG_ACCESS_KEY, GONG_CLIENT_SECRET",
        ),
        "hubspot": _status(
            _env_present("HUBSPOT_API_KEY"), "requires: HUBSPOT_API_KEY"
        ),
        "looker": _status(
            _env_present(
                "LOOKERSDK_BASE_URL", "LOOKERSDK_CLIENT_ID", "LOOKERSDK_CLIENT_SECRET"
            ),
            "requires: LOOKERSDK_*",
        ),
        "slack": _status(
            _env_present("SLACK_BOT_TOKEN"), "requires: SLACK_BOT_TOKEN"
        ),
        "asana": _status(
            _env_present("ASANA_ACCESS_TOKEN"), "requires: ASANA_ACCESS_TOKEN"
        ),
        "linear": _status(
            _env_present("LINEAR_API_KEY"), "requires: LINEAR_API_KEY"
        ),
        "airtable": _status(
            _env_present("AIRTABLE_API_KEY", "AIRTABLE_BASE_ID"),
            "requires: AIRTABLE_API_KEY, AIRTABLE_BASE_ID",
        ),
        "weaviate": _status(_env_present("WEAVIATE_URL"), "requires: WEAVIATE_URL"),
        "redis": _status(_env_present("REDIS_URL"), "requires: REDIS_URL"),
        "postgres": _status(
            _env_present("POSTGRES_URL"), "requires: POSTGRES_URL"
        ),
    }

