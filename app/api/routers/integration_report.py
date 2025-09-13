from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.integrations.registry import registry

router = APIRouter(prefix="/api/integrations", tags=["integrations"]) 


def _env_present(*keys: str) -> bool:
    return all(bool(os.getenv(k)) for k in keys)


def _stoplight(ok: bool, partial: bool = False) -> str:
    if ok:
        return "green"
    if partial:
        return "yellow"
    return "red"


@router.get("/report")
async def report() -> Dict[str, Any]:
    """Consolidated integrations report (env-driven + registry health).

    Returns a stoplight-style view for known providers and a summary.
    """
    now = datetime.utcnow().isoformat()

    items: Dict[str, Dict[str, Any]] = {}

    # Slack
    slack_env = _env_present("SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET")
    items["slack"] = {
        "status": _stoplight(slack_env),
        "env": {"bot_token": bool(os.getenv("SLACK_BOT_TOKEN")), "signing": bool(os.getenv("SLACK_SIGNING_SECRET"))},
        "endpoints": ["/api/slack/health", "/api/slack/webhook", "/api/slack/commands", "/api/slack/interactivity"],
    }

    # Salesforce (accept access token as partial readiness)
    sfdc_env_base = _env_present("SALESFORCE_CLIENT_ID", "SALESFORCE_CLIENT_SECRET")
    sfdc_refresh = bool(os.getenv("SALESFORCE_REFRESH_TOKEN"))
    sfdc_access = bool(os.getenv("SALESFORCE_ACCESS_TOKEN"))
    items["salesforce"] = {
        "status": _stoplight(sfdc_env_base and sfdc_refresh, partial=(sfdc_env_base or sfdc_access)),
        "env": {"client_id": bool(os.getenv("SALESFORCE_CLIENT_ID")), "refresh_token": sfdc_refresh, "access_token": sfdc_access},
        "endpoints": ["/api/salesforce/health", "/api/salesforce/oauth/start", "/api/salesforce/cdc"],
    }

    # Microsoft Graph
    ms_env = _env_present("MS_TENANT_ID", "MS_CLIENT_ID", "MS_CLIENT_SECRET")
    items["microsoft"] = {
        "status": _stoplight(ms_env),
        "env": {"tenant": bool(os.getenv("MS_TENANT_ID")), "client": bool(os.getenv("MS_CLIENT_ID"))},
        "endpoints": ["/api/microsoft/health", "/api/microsoft/oauth/start", "/api/microsoft/notifications"],
    }

    # Asana (support PAT token variants)
    asana_oauth = _env_present("ASANA_CLIENT_ID", "ASANA_CLIENT_SECRET")
    asana_pat = bool(os.getenv("ASANA_PAT") or os.getenv("ASANA_PAT_TOKEN") or os.getenv("ASANA_API_TOKEN"))
    items["asana"] = {
        "status": _stoplight(asana_oauth or asana_pat, partial=asana_pat or asana_oauth),
        "env": {"client_id": bool(os.getenv("ASANA_CLIENT_ID")), "pat": asana_pat},
        "endpoints": ["/api/asana/health", "/api/asana/oauth/start", "/api/asana/webhooks"],
    }

    # Linear
    linear_env = bool(os.getenv("LINEAR_API_KEY"))
    items["linear"] = {
        "status": _stoplight(linear_env),
        "env": {"api_key": linear_env},
        "endpoints": [],
    }

    # Gong
    gong_env = _env_present("GONG_ACCESS_KEY", "GONG_CLIENT_SECRET")
    items["gong"] = {
        "status": _stoplight(gong_env),
        "env": {"access_key": bool(os.getenv("GONG_ACCESS_KEY"))},
        "endpoints": ["/api/gong/calls", "/api/gong/client-health"],
    }

    # Looker (placeholder)
    looker_env = bool(os.getenv("LOOKER_SERVICE_ACCOUNT_JSON")) or (
        bool(os.getenv("LOOKER_CLIENT_ID")) and bool(os.getenv("LOOKER_CLIENT_SECRET"))
    )
    items["looker"] = {
        "status": _stoplight(looker_env, partial=looker_env),
        "env": {"service_account": bool(os.getenv("LOOKER_SERVICE_ACCOUNT_JSON"))},
        "endpoints": ["/api/looker/health"],
    }

    # HubSpot (accept multiple variants)
    hubspot_env = bool(
        os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
        or os.getenv("HUBSPOT_ACCESS_TOKEN")
        or os.getenv("HUBSPOT_API_TOKEN")
        or os.getenv("HUBSPOT_API_KEY")
    )
    items["hubspot"] = {
        "status": _stoplight(hubspot_env),
        "env": {"private_app": hubspot_env},
        "endpoints": [],
    }

    # Intercom
    intercom_env = bool(os.getenv("INTERCOM_ACCESS_TOKEN"))
    items["intercom"] = {
        "status": _stoplight(intercom_env),
        "env": {"access_token": intercom_env},
        "endpoints": [],
    }

    # NetSuite (placeholder)
    netsuite_env = _env_present("NETSUITE_ACCOUNT_ID", "NETSUITE_CONSUMER_KEY", "NETSUITE_CONSUMER_SECRET")
    items["netsuite"] = {
        "status": _stoplight(netsuite_env),
        "env": {"account": bool(os.getenv("NETSUITE_ACCOUNT_ID"))},
        "endpoints": [],
    }

    # Registry health snapshot for enabled integrations
    reg_snapshot = {k: v.__dict__ for k, v in registry.enabled().items()}

    summary = {
        "timestamp": now,
        "counts": {
            "green": sum(1 for v in items.values() if v["status"] == "green"),
            "yellow": sum(1 for v in items.values() if v["status"] == "yellow"),
            "red": sum(1 for v in items.values() if v["status"] == "red"),
        },
    }

    return {"summary": summary, "items": items, "registry": reg_snapshot}
