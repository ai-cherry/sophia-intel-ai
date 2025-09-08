from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from app.llm.multi_transport import MultiTransportLLM


@dataclass
class Route:
    provider: str
    model: str
    fallback_provider: Optional[str] = None
    fallback_model: Optional[str] = None


class EnhancedProviderRouter:
    def __init__(self, config_path: str | None = None) -> None:
        self.cfg = self._load_cfg(config_path)
        self.llm = MultiTransportLLM()

    def _load_cfg(self, config_path: str | None) -> Dict[str, Any]:
        p = Path(config_path or "config/agents/routing.yml")
        if p.exists():
            return yaml.safe_load(p.read_text()) or {}
        return {"tasks": {}}

    def _route_for(self, task_type: str) -> Route:
        t = (self.cfg.get("tasks") or {}).get(task_type, {})
        fb = t.get("fallback", {})
        return Route(
            provider=t.get("provider", "openrouter"),
            model=t.get("model", "anthropic/claude-3.5-sonnet"),
            fallback_provider=fb.get("provider"),
            fallback_model=fb.get("model"),
        )

    async def complete(self, task_type: str, messages: list[dict[str, Any]], max_tokens: int = 512, temperature: float = 0.2, provider_override: Optional[str] = None, model_override: Optional[str] = None) -> str:
        r = self._route_for(task_type)
        provider = provider_override or r.provider
        model = model_override or r.model
        # First attempt
        try:
            resp = await self.llm.complete(provider=provider, model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
            return resp.text
        except Exception:
            # Fallback attempt
            if r.fallback_provider and r.fallback_model:
                resp = await self.llm.complete(provider=r.fallback_provider, model=r.fallback_model, messages=messages, max_tokens=max_tokens, temperature=temperature)
                return resp.text
            raise

