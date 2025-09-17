"""Flowwise integration helpers for the Agent Factory tab."""
from __future__ import annotations

import json
import logging
import httpx
import os
from pathlib import Path
from typing import Any

from app.core.http_client import HTTPClientConfig, get_client
from app.models.bi_dashboard import FlowwiseAgent, FlowwiseFactory

logger = logging.getLogger(__name__)


class FlowwiseGateway:
    """Fetch Flowwise factory metadata from remote service or local config."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.base_url = os.getenv("FLOWWISE_BASE_URL")
        self.api_key = os.getenv("FLOWWISE_API_KEY")
        self.config_path = config_path or Path("config/agents/flowwise_factories.json")
        self._client_config = HTTPClientConfig()

    async def fetch_factories(self) -> list[FlowwiseFactory]:
        """Return Flowwise factories with canonical agent naming."""

        factories = await self._fetch_remote()
        if not factories:
            factories = await self._load_from_disk()
        return factories

    async def _fetch_remote(self) -> list[FlowwiseFactory]:
        if not self.base_url or not self.api_key:
            logger.info("Flowwise base url or API key not configured; falling back to config file")
            return []

        try:
            client = await get_client(self.base_url, config=self._client_config)
            response = await client.get(
                "/api/v1/factories",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            payload = response.json()
            factories: list[FlowwiseFactory] = []

            for item in payload.get("data", []):
                agents = [
                    FlowwiseAgent(
                        id=entry["id"],
                        name=entry.get("name", entry["id"]),
                        description=entry.get("description", "Flowwise automation"),
                        owner=entry.get("owner", "Unknown"),
                        tags=entry.get("tags", []),
                        version=str(entry.get("version", "1.0.0")),
                        endpoint=self._build_endpoint(entry.get("endpoint"))
                    )
                    for entry in item.get("agents", [])
                ]
                factories.append(
                    FlowwiseFactory(
                        id=item["id"],
                        department=item.get("department", "Unknown"),
                        function=item.get("function", item.get("name", "Unknown")),
                        status=item.get("status", "degraded"),
                        agents=agents,
                    )
                )
            return factories
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("Flowwise remote fetch failed: %s", exc)
            return []

    async def dispatch_agent(self, factory_id: str, agent_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke a Flowwise agent via MCP receiver."""

        factories = await self.fetch_factories()
        target_factory = next((item for item in factories if item.id == factory_id), None)
        if not target_factory:
            raise ValueError(f"Factory '{factory_id}' not found")

        target_agent = next((agent for agent in target_factory.agents if agent.id == agent_id), None)
        if not target_agent:
            raise ValueError(f"Agent '{agent_id}' not found in factory '{factory_id}'")

        endpoint = target_agent.endpoint
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = payload or {}

        if endpoint.startswith('http://') or endpoint.startswith('https://'):
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(endpoint, json=data, headers=headers)
        else:
            if not self.base_url:
                raise RuntimeError("Flowwise base URL required for relative endpoints")
            client = await get_client(self.base_url, config=self._client_config)
            response = await client.post(endpoint, json=data, headers=headers)
        response.raise_for_status()
        return response.json() if response.content else {}

    async def _load_from_disk(self) -> list[FlowwiseFactory]:
        try:
            raw = self.config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            factories: list[FlowwiseFactory] = []
            for item in data:
                agents = [
                    FlowwiseAgent(
                        id=entry["id"],
                        name=entry["name"],
                        description=entry["description"],
                        owner=entry["owner"],
                        tags=entry.get("tags", []),
                        version=entry["version"],
                        endpoint=self._build_endpoint(entry.get("endpoint_path"))
                    )
                    for entry in item.get("agents", [])
                ]
                factories.append(
                    FlowwiseFactory(
                        id=item["id"],
                        department=item["department"],
                        function=item["function"],
                        status=item["status"],
                        agents=agents,
                    )
                )
            return factories
        except FileNotFoundError:
            logger.error("Flowwise factory config not found at %s", self.config_path)
            return []
        except Exception as exc:
            logger.error("Failed to load Flowwise factories: %s", exc)
            return []

    def _build_endpoint(self, value: str | None) -> str:
        if not value:
            return ""

        if value.startswith("http://") or value.startswith("https://"):
            return value

        if not self.base_url:
            return value

        return f"{self.base_url.rstrip('/')}{value}"


flowwise_gateway = FlowwiseGateway()
"""
Shared singleton for application code.
"""
