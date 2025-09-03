from __future__ import annotations
import asyncio
import httpx
from .base_adapter import BaseLLMAdapter, LLMRequest, LLMResponse


class ClaudeAdapter(BaseLLMAdapter):
    async def complete(self, req: LLMRequest) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(text="[stub] Claude API key not configured", provider="claude")
        
        # Real API call with retry logic
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": self.api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": req.context.get("model", "claude-3-5-sonnet-20241022"),  # Latest Claude 3.5 Sonnet
                            "messages": [{"role": "user", "content": req.prompt}],
                            "max_tokens": req.max_tokens or 4096,
                            "temperature": req.temperature or 0.7
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return LLMResponse(
                            text=data["content"][0]["text"],
                            provider="claude",
                            usage=data.get("usage")
                        )
                    else:
                        if attempt == 2:
                            return LLMResponse(
                                text=f"Claude API error: {response.status_code}",
                                provider="claude"
                            )
            except Exception as e:
                if attempt == 2:
                    return LLMResponse(text=f"Claude error: {str(e)}", provider="claude")
                await asyncio.sleep(2 ** attempt)