from __future__ import annotations
import asyncio
import httpx
from .base_adapter import BaseLLMAdapter, LLMRequest, LLMResponse


class OpenAIAdapter(BaseLLMAdapter):
    async def complete(self, req: LLMRequest) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(text="[stub] OpenAI API key not configured", provider="openai")
        
        # Real API call with retry logic
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": req.context.get("model", "gpt-4o"),  # Latest GPT-4o model
                            "messages": [{"role": "user", "content": req.prompt}],
                            "max_tokens": req.max_tokens or 4096,
                            "temperature": req.temperature or 0.7
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return LLMResponse(
                            text=data["choices"][0]["message"]["content"],
                            provider="openai",
                            usage=data.get("usage")
                        )
                    else:
                        if attempt == 2:
                            return LLMResponse(
                                text=f"OpenAI API error: {response.status_code}",
                                provider="openai"
                            )
            except Exception as e:
                if attempt == 2:
                    return LLMResponse(text=f"OpenAI error: {str(e)}", provider="openai")
                await asyncio.sleep(2 ** attempt)