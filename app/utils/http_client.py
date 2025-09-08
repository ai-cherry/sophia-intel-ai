from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx


class HttpClient:
    """Minimal HTTPX wrapper with sane defaults and simple retries.

    - Async only to match most call sites
    - Per-call timeout
    - Exponential backoff with jitter
    """

    def __init__(self, timeout: float = 20.0, max_retries: int = 2):
        self.timeout = timeout
        self.max_retries = max_retries

    async def _with_retries(self, func, *args, **kwargs) -> httpx.Response:
        delay = 0.5
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    return await func(client, *args, **kwargs)
            except (
                httpx.ConnectError,
                httpx.ReadTimeout,
                httpx.WriteTimeout,
                httpx.PoolTimeout,
            ) as e:
                last_exc = e
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(delay)
                delay *= 2
        assert last_exc is not None
        raise last_exc

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        async def _do(client: httpx.AsyncClient):
            return await client.get(url, headers=headers, params=params)

        return await self._with_retries(_do)

    async def post(
        self,
        url: str,
        json: Any = None,
        data: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        async def _do(client: httpx.AsyncClient):
            return await client.post(url, json=json, data=data, headers=headers)

        return await self._with_retries(_do)
