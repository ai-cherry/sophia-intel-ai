from __future__ import annotations

import os
from typing import Any
import time
import logging

from .base import BaseConnector
from .utils import async_retry


class LinearConnector(BaseConnector):
    name = "linear"

    def configured(self) -> bool:
        return bool(os.getenv("LINEAR_API_KEY"))

    async def authenticate(self) -> bool:
        return self.configured()

    def validate_config(self) -> bool:
        return self.configured()

    @async_retry(max_attempts=2, base_delay=0.5)
    async def fetch_recent(self, since: str | None = None) -> list[dict[str, Any]]:
        if not self.configured():
            return []
        try:
            from app.integrations.linear_client import LinearClient  # type: ignore
            t0 = time.monotonic()
            async with LinearClient() as linear:
                summary = await linear.create_intelligence_summary()  # type: ignore[attr-defined]
                if isinstance(summary, dict):
                    duration_ms = int((time.monotonic() - t0) * 1000)
                    logging.getLogger(__name__).info("linear.fetch_recent duration_ms=%s", duration_ms)
                    return summary.get("project_health", []) or []
                return []
        except Exception:
            return []
