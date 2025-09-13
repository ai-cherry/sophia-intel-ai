from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from app.config.aimlapi import get_settings
from app.core.http_client import get_client


def _headers() -> Dict[str, str]:
    s = get_settings()
    return {
        "Authorization": f"Bearer {s.api_key}" if s.api_key else "",
        "Content-Type": "application/json",
    }


def get_aiml_client() -> "AIMLClient":
    return AIMLClient()


class AIMLClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def _ensure_client(self) -> httpx.AsyncClient:
        client = await get_client()
        return client

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model_id: str,
        temperature: float,
        max_tokens: int,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        client = await self._ensure_client()
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **{k: v for k, v in kwargs.items() if v is not None},
        }
        url = f"{self.settings.base_url}/chat/completions"
        resp = await client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        model_id: str,
        temperature: float,
        max_tokens: int,
    ) -> AsyncIterator[str]:
        client = await self._ensure_client()
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        url = f"{self.settings.base_url}/chat/completions"
        async with client.stream("POST", url, headers=_headers(), json=payload) as r:
            async for line in r.aiter_lines():
                if not line:
                    continue
                # Ensure SSE format
                if not line.startswith("data: "):
                    yield f"data: {json.dumps({'content': line})}\n\n"
                else:
                    yield f"{line}\n\n"
            yield "data: [DONE]\n\n"
