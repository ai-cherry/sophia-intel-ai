from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from app.llm.multi_transport import MultiTransportLLM

try:
    from prometheus_client import Counter, Histogram
except Exception:  # optional metrics
    Counter = Histogram = None
import random
import asyncio


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
        # metrics (optional)
        if Counter and Histogram:
            self._m_requests = Counter(
                "router_requests_total",
                "Router requests",
                ["provider", "model", "task_type"],
            )
            self._m_errors = Counter(
                "router_errors_total",
                "Router errors",
                ["provider", "model", "task_type"],
            )
            self._m_latency = Histogram(
                "router_latency_seconds",
                "Router latency",
                ["provider", "model", "task_type"],
            )
        else:
            self._m_requests = self._m_errors = self._m_latency = None

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

    async def complete(
        self,
        task_type: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 512,
        temperature: float = 0.2,
        provider_override: Optional[str] = None,
        model_override: Optional[str] = None,
        retries: int = 2,
    ) -> str:
        r = self._route_for(task_type)
        provider = provider_override or r.provider
        model = model_override or r.model
        attempt = 0
        while True:
            attempt += 1
            if self._m_requests:
                self._m_requests.labels(provider, model, task_type).inc()
            start = time.perf_counter()
            try:
                resp = await self.llm.complete(
                    provider=provider,
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if self._m_latency:
                    self._m_latency.labels(provider, model, task_type).observe(
                        time.perf_counter() - start
                    )
                return resp.text
            except Exception:
                if self._m_errors:
                    self._m_errors.labels(provider, model, task_type).inc()
                # Fallback if configured
                if r.fallback_provider and r.fallback_model:
                    provider, model = r.fallback_provider, r.fallback_model
                    # single fallback only once
                    r = Route(provider, model)
                    await asyncio.sleep(0.1)
                    continue
                # Retry with backoff if attempts remain
                if attempt <= retries:
                    await asyncio.sleep(0.2 * attempt + random.random() * 0.1)
                    continue
                raise
