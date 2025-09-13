from __future__ import annotations

import os
from typing import Dict, Optional

from app.integrations.base import BaseIntegrationClient, IntegrationInfo


class IntegrationRegistry:
    """Env-driven integration registry.

    Keeps a map of name -> client factory. Clients are created lazily when requested.
    """

    def __init__(self) -> None:
        self._factories: Dict[str, callable[[], Optional[BaseIntegrationClient]]] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        # Register placeholder factories for known integrations
        self.register("airtable", self._make_airtable)
        self.register("asana", self._make_asana)
        self.register("linear", self._make_linear)
        self.register("slack", self._make_slack)
        self.register("hubspot", self._make_hubspot)
        self.register("intercom", self._make_intercom)
        self.register("salesforce", self._make_salesforce)
        self.register("microsoft", self._make_microsoft)
        self.register("lattice", self._make_lattice)
        self.register("gong", self._make_gong)

    def register(self, name: str, factory: callable[[], Optional[BaseIntegrationClient]]) -> None:
        self._factories[name] = factory

    def enabled(self) -> Dict[str, IntegrationInfo]:
        out: Dict[str, IntegrationInfo] = {}
        for name in sorted(self._factories.keys()):
            client = self._factories[name]()
            out[name] = IntegrationInfo(name=name, enabled=bool(client), details={})
        return out

    def get(self, name: str) -> Optional[BaseIntegrationClient]:
        f = self._factories.get(name)
        return f() if f else None

    # ---------- Factories (lightweight placeholders) ----------

    def _make_airtable(self) -> Optional[BaseIntegrationClient]:
        pat = os.getenv("AIRTABLE_PAT") or os.getenv("AIRTABLE_ACCESS_TOKEN") or os.getenv("AIRTABLE_API_TOKEN") or os.getenv("AIRTABLE_API_KEY")
        base_id = os.getenv("AIRTABLE_BASE_ID")
        if not pat:
            return None

        class _Airtable(BaseIntegrationClient):
            name = "airtable"

            async def health(self) -> Dict[str, object]:
                return {"ok": bool(base_id), "details": {"base_id_present": bool(base_id)}}

        return _Airtable()

    def _make_asana(self) -> Optional[BaseIntegrationClient]:
        if not (os.getenv("ASANA_PAT") or os.getenv("ASANA_PAT_TOKEN") or os.getenv("ASANA_API_TOKEN")):
            return None

        class _Asana(BaseIntegrationClient):
            name = "asana"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _Asana()

    def _make_linear(self) -> Optional[BaseIntegrationClient]:
        if not os.getenv("LINEAR_API_KEY"):
            return None

        class _Linear(BaseIntegrationClient):
            name = "linear"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _Linear()

    def _make_slack(self) -> Optional[BaseIntegrationClient]:
        if not os.getenv("SLACK_BOT_TOKEN"):
            return None

        class _Slack(BaseIntegrationClient):
            name = "slack"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _Slack()

    def _make_hubspot(self) -> Optional[BaseIntegrationClient]:
        if not (os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or os.getenv("HUBSPOT_ACCESS_TOKEN") or os.getenv("HUBSPOT_API_TOKEN") or os.getenv("HUBSPOT_API_KEY")):
            return None

        class _HubSpot(BaseIntegrationClient):
            name = "hubspot"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _HubSpot()

    def _make_intercom(self) -> Optional[BaseIntegrationClient]:
        if not os.getenv("INTERCOM_ACCESS_TOKEN"):
            return None

        class _Intercom(BaseIntegrationClient):
            name = "intercom"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _Intercom()

    def _make_salesforce(self) -> Optional[BaseIntegrationClient]:
        if not (os.getenv("SALESFORCE_CLIENT_ID") and os.getenv("SALESFORCE_CLIENT_SECRET") and os.getenv("SALESFORCE_REFRESH_TOKEN")):
            return None

        class _Salesforce(BaseIntegrationClient):
            name = "salesforce"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _Salesforce()

    def _make_microsoft(self) -> Optional[BaseIntegrationClient]:
        if not (os.getenv("MS_TENANT_ID") and os.getenv("MS_CLIENT_ID") and os.getenv("MS_CLIENT_SECRET")):
            return None

        class _Microsoft(BaseIntegrationClient):
            name = "microsoft"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {"scopes": [
                    "ChannelMessage.Read.All",
                    "Team.ReadBasic.All",
                    "Files.Read.All",
                    "Sites.Read.All",
                ]}}

        return _Microsoft()

    def _make_lattice(self) -> Optional[BaseIntegrationClient]:
        if not (os.getenv("LATTICE_API_TOKEN") or os.getenv("LATTICE_API_KEY")):
            return None

        class _Lattice(BaseIntegrationClient):
            name = "lattice"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _Lattice()

    def _make_gong(self) -> Optional[BaseIntegrationClient]:
        if not (os.getenv("GONG_ACCESS_KEY") and os.getenv("GONG_CLIENT_SECRET")):
            return None

        class _Gong(BaseIntegrationClient):
            name = "gong"

            async def health(self) -> Dict[str, object]:
                return {"ok": True, "details": {}}

        return _Gong()


registry = IntegrationRegistry()
