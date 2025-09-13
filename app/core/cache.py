from __future__ import annotations

import os
from typing import Optional

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional dep
    redis = None  # type: ignore


_redis_client: Optional["redis.Redis"] = None  # type: ignore


async def get_redis() -> Optional["redis.Redis"]:  # type: ignore
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    url = os.getenv("REDIS_URL")
    if not url or redis is None:
        return None
    _redis_client = await redis.from_url(url, decode_responses=True)  # type: ignore
    return _redis_client

