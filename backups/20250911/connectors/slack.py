from __future__ import annotations

import os
from typing import Any
import time
import logging

from .base import BaseConnector


class SlackConnector(BaseConnector):
    name = "slack"

    def configured(self) -> bool:
        return bool(os.getenv("SLACK_BOT_TOKEN"))

    async def authenticate(self) -> bool:
        return self.configured()

    async def fetch_recent(self, since: str | None = None) -> list[dict[str, Any]]:
        if not self.configured():
            return []
        try:
            from app.integrations.slack_integration import SlackClient
            t0 = time.monotonic()
            client = SlackClient()
            res = await client.list_channels()
            duration_ms = int((time.monotonic() - t0) * 1000)
            logging.getLogger(__name__).info("slack.fetch_recent duration_ms=%s", duration_ms)
            return res.get("channels", [])
        except Exception:
            return []
