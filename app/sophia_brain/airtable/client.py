from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from app.api.utils.http_client import get_async_client, with_retries
from .rate_limiter import AirtableRateLimiter


class AirtableClient:
    """
    Minimal Airtable client with rate limiting and retries.
    Reads API key/base URL from environment variables.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("AIRTABLE_PAT") or os.getenv("AIRTABLE_API_KEY")
        # Base should be like: https://api.airtable.com/v0/{baseId}
        self.base_url = base_url or os.getenv("AIRTABLE_BASE_URL", "https://api.airtable.com/v0")
        self.rate_limiter = AirtableRateLimiter(rate_limit=5.0, batch_size=10)
        if not self.api_key:
            raise RuntimeError("Airtable API key not configured")

    async def _request(self, method: str, url: str, *, params: Dict[str, Any] | None = None, json: Dict[str, Any] | None = None) -> httpx.Response:
        client = await get_async_client()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

        async def do():
            resp = await client.request(method.upper(), url, params=params, json=json, headers=headers)
            if resp.status_code == 429:
                # pace/backoff
                await self.rate_limiter.backoff_on_rate_limit()
            resp.raise_for_status()
            return resp

        await self.rate_limiter.pace()
        return await with_retries(do)

    async def list_records(self, base_id: str, table: str, *, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{base_id}/{table}"
        resp = await self._request("GET", url, params=params)
        return resp.json()

    async def create_records(self, base_id: str, table: str, records: list[Dict[str, Any]]) -> Dict[str, Any]:
        url = f"{self.base_url}/{base_id}/{table}"
        batches = self.rate_limiter.chunk(records)
        results: list[Dict[str, Any]] = []
        for batch in batches:
            data = {"records": batch}
            resp = await self._request("POST", url, json=data)
            results.append(resp.json())
        return {"results": results}

