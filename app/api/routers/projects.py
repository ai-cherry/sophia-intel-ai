"""
Project Management API router

Provides a unified, no-sugarcoating project overview across Asana, Linear, Slack, and Airtable.
Designed for the Sophia Intel app dashboards and Sophia chat to query naturally.
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Any
import logging

from fastapi import APIRouter, Header
from app.connectors.registry import ConnectorRegistry
from app.api.utils.simple_cache import TTLCache
from app.api.models.project_models import ProjectsOverview, ProjectsSyncStatus
import hashlib
import json

logger = logging.getLogger(__name__)
_cache = TTLCache(default_ttl=120)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _integration_status() -> dict[str, Any]:
    """Report configured integrations for PM sources.

    Uses environment variables as an indicator. Returns non-failing status even when missing.
    """
    return {
        "asana": {
            "configured": bool(os.getenv("ASANA_PAT") or os.getenv("ASANA_PAT_TOKEN") or os.getenv("ASANA_API_TOKEN")),
            "details": "Asana PAT present; OAuth supported later"
        },
        "linear": {
            "configured": bool(os.getenv("LINEAR_API_KEY")),
            "details": "Linear API key present"
        },
        "slack": {
            "configured": bool(os.getenv("SLACK_BOT_TOKEN")),
            "details": "Slack bot token present"
        },
        "airtable": {
            "configured": bool(os.getenv("AIRTABLE_PAT") or os.getenv("AIRTABLE_ACCESS_TOKEN") or os.getenv("AIRTABLE_API_TOKEN") or os.getenv("AIRTABLE_API_KEY")),
            "details": "Airtable API credential present; base id recommended"
        },
    }


@router.get("/sync-status", response_model=ProjectsSyncStatus)
async def get_sync_status() -> dict[str, Any]:
    """Lightweight, resilient integration readiness report for PM sources."""
    status = _integration_status()
    now = datetime.utcnow().isoformat()
    return {
        "checked_at": now,
        "sources": status,
    }


@router.get("/overview", response_model=ProjectsOverview)
async def get_project_overview(
    refresh: int | None = None,
    if_none_match: str | None = Header(default=None, convert_underscores=False),
) -> Any:
    """Return a cross-platform project overview that calls out risks and blockers.

    This function is defensive: if any source lacks credentials or fails, it still returns
    a coherent payload with partial data and explicit source status.
    """
    # Return cached value if present (unless refresh requested)
    cache_key = "projects_overview_v1"
    if not refresh:
        cached = _cache.get(cache_key)
        if cached is not None:
            # ETag support for cached object
            try:
                etag = hashlib.sha256(json.dumps(cached, sort_keys=True).encode()).hexdigest()
                if if_none_match and etag == if_none_match:
                    from fastapi.responses import Response
                    return Response(status_code=304)
            except Exception:
                pass
            return cached

    sources = _integration_status()
    overview: dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat(),
        "window": {
            "from": (datetime.utcnow() - timedelta(days=14)).isoformat(),
            "to": datetime.utcnow().isoformat(),
        },
        "sources": sources,
        # Company OKRs and alignment scaffolding
        "okrs": [],  # e.g., [{"name": "Revenue per employee", "id": "okr_1"}]
        "okr_alignment": {},  # e.g., {"okr_1": {"aligned_projects": 12, "notes": []}}
        "major_projects": [],
        "blockages": [],
        "communication_issues": [],
        "departments_scorecard": [],
        "notes": [],
    }

    registry = ConnectorRegistry()

    # Slack comm issues via registry (defensive)
    if registry.configured("slack"):
        try:
            slack = registry.get("slack")
            channels = await slack.fetch_recent()
            if channels:
                overview["communication_issues"].extend([
                    {"issue": f"Channel stale: {c.get('name')}", "source": "slack"}
                    for c in channels if c.get("is_archived")
                ])
        except Exception as e:  # noqa: BLE001
            logger.warning("Slack fetch failed: %s", e)
            overview["notes"].append(f"Slack fetch failed: {e}")
    else:
        overview["notes"].append("Slack not configured")

    # Asana via registry
    if registry.configured("asana"):
        try:
            asana = registry.get("asana")
            projects = await asana.fetch_recent()
            for p in (projects or [])[:15]:
                overview["major_projects"].append(
                    {
                        "name": p.get("name") or p.get("project", {}).get("name"),
                        "owner": p.get("owner"),
                        "status": p.get("status", "active"),
                        "due_date": p.get("due_date"),
                        "is_overdue": p.get("is_overdue", False),
                        "source": "asana",
                    }
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Asana fetch failed: %s", e)
            overview["notes"].append(f"Asana fetch failed: {e}")
    else:
        overview["notes"].append("Asana not configured")

    # Linear via registry
    if registry.configured("linear"):
        try:
            linear = registry.get("linear")
            health = await linear.fetch_recent()
            for ph in (health or [])[:10]:
                overview["major_projects"].append(
                    {
                        "name": ph.get("name") or ph.get("project", {}).get("name"),
                        "owner": ph.get("owner"),
                        "status": ph.get("status", "active"),
                        "risk": ph.get("risk", "unknown"),
                        "source": "linear",
                    }
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Linear fetch failed: %s", e)
            overview["notes"].append(f"Linear fetch failed: {e}")
    else:
        overview["notes"].append("Linear not configured")

    # Slack - communication issues (via connector registry; defensive)
    try:
        slack = registry.get("slack")
        if slack and slack.configured():
            channels = await slack.fetch_recent()
            for ch in (channels or [])[:10]:
                name = ch.get("name")
                members = ch.get("num_members") or 0
                if members and members > 50:
                    overview["communication_issues"].append(
                        {
                            "pattern": "High-membership channel; monitor unanswered requests",
                            "impact": "Potential support backlog",
                            "channel": f"#{name}",
                            "source": "slack",
                        }
                    )
        else:
            overview["notes"].append("Slack not configured (connector)")
    except Exception as e:
        overview["notes"].append(f"Slack analysis failed: {e}")

    # Airtable via registry
    if registry.configured("airtable"):
        try:
            airtable = registry.get("airtable")
            docs = await airtable.fetch_recent()
            if docs:
                # Heuristic: surface any documents with 'OKR' in title/name as OKRs
                okrs = []
                for d in docs:
                    title = (d.get("title") or d.get("name") or "").lower()
                    if "okr" in title:
                        okrs.append({
                            "name": d.get("title") or d.get("name") or "OKR",
                            "id": d.get("id") or d.get("record_id") or "",
                        })
                overview["okrs"] = okrs
                if not okrs:
                    overview["notes"].append("Airtable configured but no OKR records found")
        except Exception as e:  # noqa: BLE001
            overview["notes"].append(f"Airtable fetch failed: {e}")
    else:
        overview["notes"].append("Airtable not configured")

    # No-sugarcoating: elevate individuals/departments with notable risk signals
    # Basic heuristic if we don't have strong signals yet
    risky_projects = [p for p in overview["major_projects"] if p.get("is_overdue") or p.get("risk") in {"high", "critical"}]
    if risky_projects:
        overview["notes"].append(
            f"High-risk initiatives detected: {min(len(risky_projects), 5)} highlighted"
        )

    # Store in short-lived cache and return
    _cache.set(cache_key, overview, ttl=120)
    try:
        etag = hashlib.sha256(json.dumps(overview, sort_keys=True).encode()).hexdigest()
    except Exception:
        etag = None
    if etag:
        from fastapi.responses import JSONResponse
        return JSONResponse(content=overview, headers={"ETag": etag})
    return overview
