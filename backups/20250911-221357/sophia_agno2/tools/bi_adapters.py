from __future__ import annotations

"""
Business integrations tool adapters for Sophia domain (BI only).

These are lightweight mappers; if Agno exposes HTTPTool/CustomTool constructs,
we can return those. Otherwise return structured dicts as stubs.
"""

from typing import Any, Dict


def _try_import_agno_tools():
    try:
        from agno.tools import Tool  # type: ignore

        return Tool
    except Exception:
        return None


class BIToolFactory:
    def __init__(self) -> None:
        self._Tool = _try_import_agno_tools()

    def _wrap(self, name: str, config: Dict[str, Any]) -> Any:
        if self._Tool:
            try:
                return self._Tool(name=name, **config)
            except Exception:
                pass
        return {"type": "bi_tool", "name": name, **config}

    def looker(self):
        return self._wrap("looker.query", {"endpoint": "/api/looker"})

    def hubspot(self):
        return self._wrap("hubspot.api", {"endpoint": "/api/hubspot"})

    def salesforce(self):
        return self._wrap("salesforce.query", {"endpoint": "/api/salesforce"})

    def gong(self):
        return self._wrap("gong.calls", {"endpoint": "/api/gong"})

    def map_tool(self, name: str):
        name = name.lower()
        if name.startswith("looker"):
            return self.looker()
        if name.startswith("hubspot"):
            return self.hubspot()
        if name.startswith("salesforce"):
            return self.salesforce()
        if name.startswith("gong"):
            return self.gong()
        # default to a generic BI tool stub
        return self._wrap(name, {"endpoint": "/api"})

