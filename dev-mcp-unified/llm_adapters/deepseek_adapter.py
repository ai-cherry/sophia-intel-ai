from __future__ import annotations
from .base_adapter import BaseLLMAdapter, LLMRequest, LLMResponse


class DeepSeekAdapter(BaseLLMAdapter):
    async def complete(self, req: LLMRequest) -> LLMResponse:
        text = f"[deepseek] prompt={req.prompt[:80]}... strategy={req.context.get('strategy')}"
        return LLMResponse(text=text, provider="deepseek", usage=None)

