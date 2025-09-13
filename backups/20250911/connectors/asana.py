from __future__ import annotations

import os
from typing import Any
import time
import logging

from .base import BaseConnector
from .utils import async_retry


class AsanaConnector(BaseConnector):
    name = "asana"

    def configured(self) -> bool:
        return bool(os.getenv("ASANA_API_TOKEN") or os.getenv("ASANA_PAT_TOKEN"))

    async def authenticate(self) -> bool:
        return self.configured()

    def validate_config(self) -> bool:
        return self.configured()

    @async_retry(max_attempts=2, base_delay=0.5)
    async def fetch_recent(self, since: str | None = None) -> list[dict[str, Any]]:
        if not self.configured():
            return []
        # Defensive: try to import optional client; otherwise return []
        try:
            from app.integrations.asana_client import AsanaClient  # type: ignore
            t0 = time.monotonic()
            async with AsanaClient() as asana:
                workspaces = await asana.get_workspaces()
                if not workspaces:
                    return []
                ws_id = workspaces[0].get("gid")
                if not ws_id:
                    return []
                health = await asana.analyze_project_health(ws_id)
                duration_ms = int((time.monotonic() - t0) * 1000)
                logging.getLogger(__name__).info("asana.fetch_recent duration_ms=%s", duration_ms)
                return health.get("project_details", []) if isinstance(health, dict) else []
        except Exception:
            return []
