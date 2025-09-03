from __future__ import annotations
from .base_adapter import BaseLLMAdapter, LLMRequest, LLMResponse


class ClaudeAdapter(BaseLLMAdapter):
    async def complete(self, req: LLMRequest) -> LLMResponse:
        # For local use, we avoid making outbound calls in this scaffold.
        # If ANTHROPIC_API_KEY is available, you can implement httpx call here.
        text = f"[claude] prompt={req.prompt[:80]}... strategy={req.context.get('strategy')}"
        return LLMResponse(text=text, provider="claude", usage=None)

