from __future__ import annotations

import os
from typing import Any
import time
import logging

from .base import BaseConnector


class GongConnector(BaseConnector):
    name = "gong"

    def configured(self) -> bool:
        return bool(os.getenv("GONG_ACCESS_KEY") and os.getenv("GONG_CLIENT_SECRET"))

    async def authenticate(self) -> bool:
        return self.configured()

    async def fetch_recent(self, since: str | None = None) -> list[dict[str, Any]]:
        if not self.configured():
            return []
        try:
            from app.integrations.gong_optimized_client import GongOptimizedClient
            t0 = time.monotonic()
            async with GongOptimizedClient(use_oauth=False) as client:
                data = await client.get_calls(limit=20)
                duration_ms = int((time.monotonic() - t0) * 1000)
                logging.getLogger(__name__).info("gong.fetch_recent duration_ms=%s", duration_ms)
                return data.get("calls", [])
        except Exception:
            return []
