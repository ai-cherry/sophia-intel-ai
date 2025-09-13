from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class IntegrationInfo:
    name: str
    enabled: bool
    details: Dict[str, Any]


class BaseIntegrationClient:
    """Minimal integration client interface.

    Keep this deliberately small: health() and list_entities().
    Implementations should read configuration from environment in their factory.
    """

    name: str = "integration"

    async def health(self) -> Dict[str, Any]:
        return {"ok": False, "details": {}}

    async def list_entities(
        self,
        since: Optional[str] = None,
        page_token: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        return {"items": [], "next": None}

