from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/airtable", tags=["airtable"])


def _get_token() -> Optional[str]:
    return (
        os.getenv("AIRTABLE_ACCESS_TOKEN")
        or os.getenv("AIRTABLE_API_TOKEN")
        or os.getenv("AIRTABLE_PAT")
        or os.getenv("AIRTABLE_API_KEY")
    )


@router.get("/whoami")
async def whoami() -> Dict[str, Any]:
    token = _get_token()
    if not token:
        raise HTTPException(400, "Airtable token missing (AIRTABLE_ACCESS_TOKEN or similar)")
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.airtable.com/v0/meta/whoami"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=headers)
            if r.status_code >= 400:
                raise HTTPException(r.status_code, r.text)
            return r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"whoami failed: {e}")


@router.get("/bases")
async def list_bases() -> Dict[str, Any]:
    """Attempt to list bases using the Metadata API.

    Note: Some accounts require OAuth or specific permissions for this endpoint. If this
    returns 403, use the manual methods (UI URL or API docs) to get the Base ID (appXXXX).
    """
    token = _get_token()
    if not token:
        raise HTTPException(400, "Airtable token missing (AIRTABLE_ACCESS_TOKEN or similar)")
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.airtable.com/v0/meta/bases"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, headers=headers)
            if r.status_code >= 400:
                raise HTTPException(r.status_code, r.text)
            return r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"list bases failed: {e}")


@router.get("/bases/{base_id}/tables")
async def base_tables(base_id: str) -> Dict[str, Any]:
    token = _get_token()
    if not token:
        raise HTTPException(400, "Airtable token missing (AIRTABLE_ACCESS_TOKEN or similar)")
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, headers=headers)
            if r.status_code >= 400:
                raise HTTPException(r.status_code, r.text)
            return r.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, f"list tables failed: {e}")

