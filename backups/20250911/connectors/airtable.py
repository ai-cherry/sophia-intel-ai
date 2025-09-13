from __future__ import annotations

import os
from typing import Any
import time
import logging

from .base import BaseConnector
from .utils import async_retry


class AirtableConnector(BaseConnector):
    name = "airtable"

    def configured(self) -> bool:
        return bool(os.getenv("AIRTABLE_API_KEY") or os.getenv("AIRTABLE_ACCESS_TOKEN"))

    async def authenticate(self) -> bool:
        return self.configured()

    def validate_config(self) -> bool:
        return self.configured()

    @async_retry(max_attempts=2, base_delay=0.5)
    async def fetch_recent(self, since: str | None = None) -> list[dict[str, Any]]:
        if not self.configured():
            return []
        try:
            from app.integrations.airtable_client import AirtableClient  # type: ignore
            t0 = time.monotonic()
            client = AirtableClient()
            rows = await client.fetch_recent_rows()
            duration_ms = int((time.monotonic() - t0) * 1000)
            logging.getLogger(__name__).info("airtable.fetch_recent duration_ms=%s", duration_ms)
            return rows or []
        except Exception:
            return []
