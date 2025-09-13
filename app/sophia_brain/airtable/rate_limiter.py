from __future__ import annotations

import asyncio
from typing import Any, Iterable, List


class AirtableRateLimiter:
    """
    Simple rate limiter + batch helper for Airtable-like APIs.

    - rate_limit: requests per second
    - batch_size: number of records per batch
    - backoff: sequence of seconds to wait on 429
    """

    def __init__(self, rate_limit: float = 5.0, batch_size: int = 10, backoff: Iterable[float] | None = None):
        self.rate_limit = max(0.1, rate_limit)
        self.batch_size = max(1, batch_size)
        self.backoff = list(backoff or [1, 2, 4, 8, 16])
        self._lock = asyncio.Lock()

    async def pace(self) -> None:
        async with self._lock:
            await asyncio.sleep(1.0 / self.rate_limit)

    def chunk(self, records: List[Any]) -> List[List[Any]]:
        return [records[i:i + self.batch_size] for i in range(0, len(records), self.batch_size)]

    async def backoff_on_rate_limit(self) -> None:
        for delay in self.backoff:
            await asyncio.sleep(delay)

