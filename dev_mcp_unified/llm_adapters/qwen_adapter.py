from __future__ import annotations
from .base_adapter import BaseLLMAdapter, LLMRequest, LLMResponse


class QwenAdapter(BaseLLMAdapter):
    async def complete(self, req: LLMRequest) -> LLMResponse:
        text = f"[qwen] {req.prompt[:80]}... strategy={req.context.get('strategy')}"
        return LLMResponse(text=text, provider="qwen", usage=None)

