from openai import AsyncOpenAI
import httpx
import os
import logging
from typing import List, Dict, Any, Optional
import time
from prometheus_client import Counter, Histogram, CollectorRegistry, REGISTRY

# Initialize Prometheus metrics with duplicate handling
try:
    model_tokens_total = Counter(
        'model_tokens_total',
        'Total tokens processed per model',
        ['model', 'type']
    )
except ValueError:
    # Metric already exists, get it from registry
    model_tokens_total = REGISTRY._names_to_collectors['model_tokens_total']

try:
    model_latency_seconds = Histogram(
        'model_latency_seconds',
        'Model request latency',
        ['model']
    )
except ValueError:
    model_latency_seconds = REGISTRY._names_to_collectors['model_latency_seconds']

try:
    model_cost_usd_total = Counter(
        'model_cost_usd_total',
        'Total cost in USD per model',
        ['model', 'type']
    )
except ValueError:
    model_cost_usd_total = REGISTRY._names_to_collectors['model_cost_usd_total']

try:
    model_cost_usd_today = Counter(
        'model_cost_usd_today',
        'Cost so far today per model',
        ['model']
    )
except ValueError:
    model_cost_usd_today = REGISTRY._names_to_collectors['model_cost_usd_today']

AVAILABLE_MODELS = {
    "openai/gpt-5": {
        "context": 400000,
        "input_cost": 1.25,
        "output_cost": 10.0,
        "capabilities": ["chat", "code", "reasoning", "multimodal"],
        "priority": "premium"
    },
    "x-ai/grok-4": {
        "context": 128000,
        "input_cost": 0.8,
        "output_cost": 6.0,
        "capabilities": ["chat", "code", "analysis"],
        "priority": "premium"
    },
    "anthropic/claude-sonnet-4": {
        "context": 200000,
        "input_cost": 0.5,
        "output_cost": 4.0,
        "capabilities": ["chat", "code", "writing"],
        "priority": "standard"
    },
    "x-ai/grok-code-fast-1": {
        "context": 32000,
        "input_cost": 0.3,
        "output_cost": 2.0,
        "capabilities": ["code"],
        "priority": "specialized"
    },
    "google/gemini-2.5-flash": {
        "context": 100000,
        "input_cost": 0.1,
        "output_cost": 0.5,
        "capabilities": ["chat", "fast"],
        "priority": "economy"
    },
    "google/gemini-2.5-pro": {
        "context": 200000,
        "input_cost": 0.6,
        "output_cost": 4.5,
        "capabilities": ["chat", "code", "multimodal"],
        "priority": "standard"
    },
    "deepseek/deepseek-chat-v3.1": {
        "context": 64000,
        "input_cost": 0.2,
        "output_cost": 1.5,
        "capabilities": ["chat", "memory"],
        "priority": "economy"
    },
    "z-ai/glm-4.5-air": {
        "context": 32000,
        "input_cost": 0.05,
        "output_cost": 0.3,
        "capabilities": ["chat", "lightweight"],
        "priority": "economy"
    }
}

class OpenRouterGateway:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            http_client=httpx.AsyncClient(
                timeout=60.0,
                limits=httpx.Limits(max_keepalive_connections=10)
            )
        )

    async def chat_completion(self, model: str, messages: List[Dict], **kwargs):
        """Unified chat completion for OpenRouter models with GPT-5 optimizations"""
        # GPT-5 specific text transformation when enabled
        if model == "openai/gpt-5" and kwargs.get("think_hard"):
            messages[0]["content"] = f"Think step-by-step about this: {messages[0]['content']}"

        start_time = time.time()
        try:
            completion = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": "https://sophia-intel-ai.com",
                    "X-Title": "Sophia Intel AI"
                },
                **kwargs
            )
            latency = time.time() - start_time
            model_latency_seconds.labels(model=model).observe(latency)
            self._track_cost(model, completion.usage)
            return completion
        except Exception as e:
            # Fallback chain on failure
            fallback_model = self._get_fallback(model)
            if fallback_model:
                # Avoid infinite recursion in fallbacks
                new_kwargs = kwargs.copy()
                new_kwargs["think_hard"] = False
                return await self.chat_completion(fallback_model, messages, **new_kwargs)
            raise

    def _track_cost(self, model: str, usage):
        """Track model usage costs for Prometheus metrics"""
        if model not in AVAILABLE_MODELS:
            return
        model_info = AVAILABLE_MODELS[model]
        input_cost = (usage.prompt_tokens / 1_000_000) * model_info["input_cost"]
        output_cost = (usage.completion_tokens / 1_000_000) * model_info["output_cost"]
        
        # Update Prometheus counters
        model_tokens_total.labels(model=model, type="input").inc(usage.prompt_tokens)
        model_tokens_total.labels(model=model, type="output").inc(usage.completion_tokens)
        model_cost_usd_total.labels(model=model, type="input").inc(input_cost)
        model_cost_usd_total.labels(model=model, type="output").inc(output_cost)
        model_cost_usd_today.labels(model=model).inc(input_cost + output_cost)

    def _get_fallback(self, model: str) -> Optional[str]:
        """Generate fallback chain for unavailable models"""
        fallback_chain = {
            "openai/gpt-5": [
                "anthropic/claude-sonnet-4", 
                "google/gemini-2.5-pro", 
                "z-ai/glm-4.5-air"
            ],
            "x-ai/grok-4": [
                "anthropic/claude-sonnet-4", 
                "google/gemini-2.5-pro", 
                "z-ai/glm-4.5-air"
            ],
            "anthropic/claude-sonnet-4": [
                "google/gemini-2.5-pro", 
                "z-ai/glm-4.5-air"
            ],
            "x-ai/grok-code-fast-1": [
                "google/gemini-2.5-flash", 
                "z-ai/glm-4.5-air"
            ],
            "google/gemini-2.5-flash": [
                "google/gemini-2.5-pro", 
                "z-ai/glm-4.5-air"
            ],
            "google/gemini-2.5-pro": [
                "google/gemini-2.5-flash", 
                "z-ai/glm-4.5-air"
            ],
            "deepseek/deepseek-chat-v3.1": [
                "z-ai/glm-4.5-air"
            ],
            "z-ai/glm-4.5-air": None
        }
        return fallback_chain.get(model, [None])[0] if fallback_chain.get(model) else None

# Test only for local development
if __name__ == "__main__":
    import asyncio
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test_gateway():
        gateway = OpenRouterGateway()
        print("Testing GPT-5 with think_hard")
        response = await gateway.chat_completion(
            "openai/gpt-5",
            [{"role": "user", "content": "What is the capital of France?"}],
            max_tokens=10,
            temperature=0.1,
            think_hard=True
        )
        print(f"GPT-5 Response: {response.choices[0].message.content}")
        
        print("\nTesting fallback chain (invalid model)")
        try:
            response = await gateway.chat_completion(
                "invalid-model",
                [{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            print(f"Fallback Response: {response.choices[0].message.content}")
        except Exception as e:
            print(f"Fallback failed: {str(e)}")
    
    asyncio.run(test_gateway())
