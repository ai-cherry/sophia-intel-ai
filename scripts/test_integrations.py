#!/usr/bin/env python3
"""
Lightweight Integration Test Runner for Sophia Intel AI

Runs minimal connectivity checks against available integrations based on env.
Skips tests when required credentials are missing. Produces a JSON report.
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

from dotenv import load_dotenv
import sys
from pathlib import Path

# Ensure repo root is importable so `import app...` works
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def env_has(*keys: str) -> bool:
    return all(os.getenv(k) for k in keys)


async def test_slack() -> Dict[str, Any]:
    result: Dict[str, Any] = {"integration": "slack"}
    if not env_has("SLACK_BOT_TOKEN"):
        result.update({"status": "skipped", "reason": "SLACK_BOT_TOKEN missing"})
        return result
    try:
        from slack_sdk.web.async_client import AsyncWebClient  # type: ignore

        client = AsyncWebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        resp = await client.auth_test()
        ok = bool(resp.get("ok"))
        result.update(
            {
                "status": "working" if ok else "failed",
                "team": resp.get("team"),
                "user_id": resp.get("user_id"),
            }
        )
    except Exception as e:
        result.update({"status": "failed", "error": str(e)})
    return result


async def test_hubspot() -> Dict[str, Any]:
    result: Dict[str, Any] = {"integration": "hubspot"}
    if not (os.getenv("HUBSPOT_ACCESS_TOKEN") or os.getenv("HUBSPOT_API_KEY")):
        result.update({"status": "skipped", "reason": "HubSpot token/key missing"})
        return result
    try:
        from app.integrations.hubspot_optimized_client import (
            HubSpotOptimizedClient,
        )

        async with HubSpotOptimizedClient() as client:
            ok = await client.test_connection()
        result.update({"status": "working" if ok else "failed"})
    except Exception as e:
        result.update({"status": "failed", "error": str(e)})
    return result


async def test_salesforce() -> Dict[str, Any]:
    result: Dict[str, Any] = {"integration": "salesforce"}
    # Accept either access token + instance or username/password + token
    have_session = env_has("SALESFORCE_ACCESS_TOKEN", "SALESFORCE_INSTANCE_URL")
    have_userpass = env_has("SALESFORCE_USERNAME", "SALESFORCE_PASSWORD", "SALESFORCE_TOKEN")
    if not (have_session or have_userpass):
        result.update({"status": "skipped", "reason": "Salesforce creds missing"})
        return result
    try:
        from app.integrations.salesforce_optimized_client import (
            SalesforceOptimizedClient,
        )

        client = SalesforceOptimizedClient()
        ok = await client.test_connection()
        result.update({"status": "working" if ok else "failed"})
    except Exception as e:
        result.update({"status": "failed", "error": str(e)})
    return result


async def test_airtable() -> Dict[str, Any]:
    result: Dict[str, Any] = {"integration": "airtable"}
    if not (os.getenv("AIRTABLE_PAT") or os.getenv("AIRTABLE_API_KEY")):
        result.update({"status": "skipped", "reason": "Airtable PAT/API key missing"})
        return result
    try:
        from app.integrations.airtable_optimized_client import (
            AirtableOptimizedClient,
        )

        async with AirtableOptimizedClient() as client:
            ok = await client.test_connection()
        result.update({"status": "working" if ok else "failed"})
    except Exception as e:
        result.update({"status": "failed", "error": str(e)})
    return result


async def test_looker() -> Dict[str, Any]:
    result: Dict[str, Any] = {"integration": "looker"}
    # Allow running if any likely credential is present
    if not (
        os.getenv("LOOKER_CLIENT_ID")
        or os.getenv("LOOKER_CLIENT_SECRET")
        or os.getenv("LOOKER_ACCESS_TOKEN")
    ):
        result.update({"status": "skipped", "reason": "Looker creds missing"})
        return result
    try:
        from app.integrations.looker_optimized_client import LookerOptimizedClient

        client = LookerOptimizedClient()
        ok = await client.test_connection()
        result.update({"status": "working" if ok else "failed"})
    except Exception as e:
        result.update({"status": "failed", "error": str(e)})
    return result


async def test_gong() -> Dict[str, Any]:
    result: Dict[str, Any] = {"integration": "gong"}
    if not env_has("GONG_ACCESS_KEY", "GONG_CLIENT_SECRET"):
        result.update({"status": "skipped", "reason": "Gong creds missing"})
        return result
    try:
        from app.integrations.gong_optimized_client import GongOptimizedClient

        client = GongOptimizedClient()
        ok = await client.test_connection()
        result.update({"status": "working" if ok else "failed"})
    except Exception as e:
        result.update({"status": "failed", "error": str(e)})
    return result

async def test_microsoft() -> Dict[str, Any]:
    result: Dict[str, Any] = {"integration": "microsoft"}
    tenant = os.getenv("MS_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID")
    client_id = os.getenv("MS_CLIENT_ID") or os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET_KEY")
    if not (tenant and client_id and client_secret):
        result.update({"status": "skipped", "reason": "Microsoft env not set"})
        return result
    try:
        try:
            import msal  # type: ignore
        except Exception:
            result.update({"status": "failed", "error": "msal not installed (pip install msal)"})
            return result
        authority = f"https://login.microsoftonline.com/{tenant}"
        app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
        scope = ["https://graph.microsoft.com/.default"]
        token = app.acquire_token_for_client(scopes=scope)
        ok = bool(token and token.get("access_token"))
        result.update({"status": "working" if ok else "failed", "token_type": token.get("token_type")})
    except Exception as e:
        result.update({"status": "failed", "error": str(e)})
    return result

async def main():
    # Load local env if available
    load_dotenv(".env.local")

    tests = [
        test_slack,
        test_gong,
        test_hubspot,
        test_salesforce,
        test_airtable,
        test_looker,
        test_microsoft,
    ]

    results: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
    }

    for test in tests:
        name = test.__name__.replace("test_", "")
        try:
            outcome = await asyncio.wait_for(test(), timeout=20)
        except asyncio.TimeoutError:
            outcome = {"integration": name, "status": "failed", "error": "timeout"}
        except Exception as e:  # Defensive catch-all
            outcome = {"integration": name, "status": "failed", "error": str(e)}
        results["tests"].append(outcome)

    # Derive summary
    working = sum(1 for r in results["tests"] if r.get("status") == "working")
    failed = sum(1 for r in results["tests"] if r.get("status") == "failed")
    skipped = sum(1 for r in results["tests"] if r.get("status") == "skipped")
    results["summary"] = {
        "working": working,
        "failed": failed,
        "skipped": skipped,
        "total": len(results["tests"]),
    }

    with open("integration_runtime_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results["summary"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
