from __future__ import annotations
import asyncio
import httpx
from .base_adapter import BaseLLMAdapter, LLMRequest, LLMResponse


class OpenRouterAdapter(BaseLLMAdapter):
    """Smart routing to optimal models based on task type"""
    
    def select_model(self, task: str) -> str:
        """Select best model based on task type - using latest models"""
        model_map = {
            "code_generation": "openai/gpt-4o",  # Latest GPT-4o
            "code_review": "anthropic/claude-3-5-sonnet-20241022",  # Latest Claude 3.5
            "analysis": "anthropic/claude-3-5-sonnet-20241022",
            "quick_answer": "meta-llama/llama-3.1-70b-instruct",  # Llama 3.1
            "web_search": "perplexity/llama-3.1-sonar-huge-128k-online",  # Latest Perplexity
            "refactoring": "deepseek/deepseek-coder-v3",  # Latest DeepSeek V3
            "testing": "openai/gpt-4o",
            "documentation": "anthropic/claude-3-5-haiku-20241022",  # Latest Haiku
            "explain": "anthropic/claude-3-5-sonnet-20241022",
            "debug": "deepseek/deepseek-coder-v3",
            "general": "anthropic/claude-3-5-sonnet-20241022"
        }
        return model_map.get(task, "anthropic/claude-3-5-sonnet-20241022")
    
    async def complete(self, req: LLMRequest) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(text="[stub] OpenRouter API key not configured", provider="openrouter")
        
        # Determine task type from context
        task = req.context.get("task", "general")
        model = self.select_model(task)
        
        # Real API call with retry logic
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "HTTP-Referer": "http://localhost:3333",
                            "X-Title": "MCP Dev Server",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": [{"role": "user", "content": req.prompt}],
                            "max_tokens": req.max_tokens or 2000,
                            "temperature": req.temperature or 0.7
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return LLMResponse(
                            text=data["choices"][0]["message"]["content"],
                            provider=f"openrouter/{model.split('/')[0]}",
                            usage=data.get("usage")
                        )
                    else:
                        if attempt == 2:
                            return LLMResponse(
                                text=f"OpenRouter API error: {response.status_code}",
                                provider="openrouter"
                            )
            except Exception as e:
                if attempt == 2:
                    return LLMResponse(text=f"OpenRouter error: {str(e)}", provider="openrouter")
                await asyncio.sleep(2 ** attempt)