"""Agno v2 integration helpers for Developer Studio."""
from __future__ import annotations

import json
import logging
import httpx
import os
from pathlib import Path
from typing import Any

from app.core.http_client import HTTPClientConfig, get_client
from app.models.bi_dashboard import AgnoAgent, AgnoWorkspace

logger = logging.getLogger(__name__)


class AgnoWorkspaceService:
    """Load Agno workspace metadata from remote runtime or local config."""

    def __init__(self, config_path: Path | None = None) -> None:
        self.base_url = os.getenv("AGNO_BASE_URL")
        self.api_key = os.getenv("AGNO_API_KEY")
        self.config_path = config_path or Path("config/agents/agno_workspaces.json")
        self._client_config = HTTPClientConfig()

    async def fetch_workspaces(self) -> list[AgnoWorkspace]:
        workspaces = await self._fetch_remote()
        if not workspaces:
            workspaces = await self._load_from_disk()
        return workspaces

    async def _fetch_remote(self) -> list[AgnoWorkspace]:
        if not self.base_url or not self.api_key:
            logger.info("Agno base url or API key not configured; using config file fallback")
            return []

        try:
            client = await get_client(self.base_url, config=self._client_config)
            response = await client.get(
                "/api/v2/workspaces",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            payload = response.json()
            workspaces: list[AgnoWorkspace] = []

            for item in payload.get("data", []):
                agents = [
                    AgnoAgent(
                        id=entry["id"],
                        name=entry.get("name", entry["id"]),
                        description=entry.get("description", "Agno agent"),
                        owner=entry.get("owner", "Unknown"),
                        tags=entry.get("tags", []),
                        version=str(entry.get("version", "1.0.0"))
                    )
                    for entry in item.get("agents", [])
                ]
                workspaces.append(
                    AgnoWorkspace(
                        id=item["id"],
                        purpose=item.get("purpose", item.get("name", "Unknown")),
                        version=str(item.get("version", "2.0.0")),
                        maintainer=item.get("maintainer", "Unknown"),
                        pipelines=int(item.get("pipelines", 0)),
                        health=item.get("health", "yellow"),
                        agents=agents,
                    )
                )
            return workspaces
        except Exception as exc:  # pragma: no cover - network failure path
            logger.warning("Agno workspace remote fetch failed: %s", exc)
            return []

    async def trigger_agent(self, workspace_id: str, agent_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke an Agno agent from Developer Studio."""

        workspaces = await self.fetch_workspaces()
        workspace = next((item for item in workspaces if item.id == workspace_id), None)
        if not workspace:
            raise ValueError(f"Workspace '{workspace_id}' not found")

        agent = next((entry for entry in workspace.agents if entry.id == agent_id), None)
        if not agent:
            raise ValueError(f"Agent '{agent_id}' not found in workspace '{workspace_id}'")

        if not self.base_url:
            raise RuntimeError("AGNO_BASE_URL not configured")

        client = await get_client(self.base_url, config=self._client_config)
        response = await client.post(
            f"/api/v2/agents/{agent_id}/invoke",
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else None,
            json=payload or {},
        )
        response.raise_for_status()
        return response.json() if response.content else {}

    async def _load_from_disk(self) -> list[AgnoWorkspace]:
        try:
            raw = self.config_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            workspaces: list[AgnoWorkspace] = []
            for item in data:
                agents = [
                    AgnoAgent(
                        id=entry["id"],
                        name=entry["name"],
                        description=entry["description"],
                        owner=entry["owner"],
                        tags=entry.get("tags", []),
                        version=entry["version"],
                    )
                    for entry in item.get("agents", [])
                ]
                workspaces.append(
                    AgnoWorkspace(
                        id=item["id"],
                        purpose=item["purpose"],
                        version=item["version"],
                        maintainer=item["maintainer"],
                        pipelines=int(item["pipelines"]),
                        health=item["health"],
                        agents=agents,
                    )
                )
            return workspaces
        except FileNotFoundError:
            logger.error("Agno workspace config not found at %s", self.config_path)
            return []
        except Exception as exc:
            logger.error("Failed to load Agno workspaces: %s", exc)
            return []


agno_workspace_service = AgnoWorkspaceService()
"""Shared singleton instance."""
