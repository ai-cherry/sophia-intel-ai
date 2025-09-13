from __future__ import annotations

import time
from typing import Any, Optional


class TTLCache:
    """
    Minimal in-process TTL cache for lightweight endpoint responses.
    Not shared across workers; intended for small, short-lived caching.
    """

    def __init__(self, default_ttl: int = 120) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = max(1, int(default_ttl))

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if now >= expires_at:
            # expired
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        duration = self._default_ttl if ttl is None else max(1, int(ttl))
        self._store[key] = (time.time() + duration, value)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        self._store.clear()

