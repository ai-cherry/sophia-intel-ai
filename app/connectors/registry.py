from __future__ import annotations

from typing import Dict

from .base import BaseConnector
from .gong import GongConnector
from .slack import SlackConnector
from .asana import AsanaConnector
from .linear import LinearConnector
from .airtable import AirtableConnector


class ConnectorRegistry:
    def __init__(self) -> None:
        self._connectors: Dict[str, BaseConnector] = {
            "gong": GongConnector(),
            "slack": SlackConnector(),
            "asana": AsanaConnector(),
            "linear": LinearConnector(),
            "airtable": AirtableConnector(),
        }

    def get(self, name: str) -> BaseConnector | None:
        return self._connectors.get(name)

    def configured(self, name: str) -> bool:
        c = self.get(name)
        return bool(c and c.configured())

    def list(self):
        return list(self._connectors.keys())
