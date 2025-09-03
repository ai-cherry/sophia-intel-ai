from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMRequest:
    prompt: str
    context: Dict[str, Any]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None


@dataclass
class LLMResponse:
    text: str
    provider: str
    usage: Dict[str, Any] | None = None


class BaseLLMAdapter:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    async def complete(self, req: LLMRequest) -> LLMResponse:
        raise NotImplementedError

