from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    name: str = "base"

    @abstractmethod
    def configured(self) -> bool:  # defensive
        ...

    @abstractmethod
    async def authenticate(self) -> bool:
        ...

    @abstractmethod
    async def fetch_recent(self, since: str | None = None) -> list[dict[str, Any]]:
        ...

    async def get_context_for_entity(self, entity_id: str) -> dict[str, Any]:  # optional
        return {}

    async def index_to_weaviate(self, data: list[dict[str, Any]]) -> int:  # optional
        return 0

    def validate_config(self) -> bool:
        """Non-network validation of required environment for this connector."""
        return self.configured()
