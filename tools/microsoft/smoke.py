#!/usr/bin/env python3
"""
Microsoft Graph live smoke test (app-only)

Requires env in .env.local or shell:
  - MS_TENANT_ID|MICROSOFT_TENANT_ID
  - MS_CLIENT_ID|MICROSOFT_CLIENT_ID
  - MS_CLIENT_SECRET|MICROSOFT_SECRET_KEY

Usage:
  python tools/microsoft/smoke.py
"""
from __future__ import annotations
import os
from pathlib import Path


def main() -> int:
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        load_dotenv = None
    if load_dotenv:
        env_path = Path.cwd() / ".env.local"
        if env_path.exists():
            load_dotenv(str(env_path))

    tenant = os.getenv("MS_TENANT_ID") or os.getenv("MICROSOFT_TENANT_ID")
    client_id = os.getenv("MS_CLIENT_ID") or os.getenv("MICROSOFT_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET") or os.getenv("MICROSOFT_SECRET_KEY")
    if not (tenant and client_id and client_secret):
        print("Microsoft Graph env not set. Set MS_* or MICROSOFT_* variables.")
        return 2

    try:
        from app.integrations.microsoft_graph_client import MicrosoftGraphClient
    except Exception as e:
        print(f"Import failed: {e}")
        return 2

    import asyncio

    async def run():
        client = MicrosoftGraphClient()
        users = await client.list_users(top=5)
        print(f"users: {len(users.get('value', []))}")
        teams = await client.list_teams(top=5)
        print(f"groups/teams: {len(teams.get('value', []))}")
        drive = await client.drive_root()
        print(f"drive id: {drive.get('id')}")

    try:
        asyncio.run(run())
        return 0
    except Exception as e:
        print(f"Graph smoke failed: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

