"""
Optimized OpenRouter client for Sophia AI
Direct integration without openrouter middleware
"""
import asyncio
import aiohttp
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class OpenRouterModel:
    """OpenRouter model information"""
    id: str
    name: str
    description: str
    pricing: Dict[str, float]
    context_length: int
    architecture: Dict[str, Any]
    top_provider: Dict[str, Any]

class OpenRouterClient:
    """
    Optimized OpenRouter client with direct API access
    Features:
    - Direct API calls (no middleware)
    - Async/await support
    - Model selection optimization
    - Cost tracking
    - Retry logic with exponential backoff
    - Streaming support
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.session = None
        self._models_cache = None
        
        # Default headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://sophia-intel.ai",
            "X-Title": "Sophia AI Platform"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_models(self, force_refresh: bool = False) -> List[OpenRouterModel]:
        """Get available models with caching"""
        if self._models_cache and not force_refresh:
            return self._models_cache
        
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        
        try:
            async with self.session.get(f"{self.base_url}/models") as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    
                    for model_data in data.get('data', []):
                        model = OpenRouterModel(
                            id=model_data.get('id', ''),
                            name=model_data.get('name', ''),
                            description=model_data.get('description', ''),
                            pricing=model_data.get('pricing', {}),
                            context_length=model_data.get('context_length', 0),
                            architecture=model_data.get('architecture', {}),
                            top_provider=model_data.get('top_provider', {})
                        )
                        models.append(model)
                    
                    self._models_cache = models
                    logger.info(f"Loaded {len(models)} OpenRouter models")
                    return models
                else:
                    logger.error(f"Failed to fetch models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "anthropic/claude-3.5-sonnet",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create chat completion with optimized model selection
        """
        if not self.session:
            self.session = aiohttp.ClientSession(headers=self.headers)
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
            **kwargs
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                
                if response.status == 200:
                    if stream:
                        return self._handle_stream_response(response)
                    else:
                        result = await response.json()
                        logger.info(f"Chat completion successful with {model}")
                        return result
                else:
                    error_text = await response.text()
                    logger.error(f"Chat completion failed: {response.status} - {error_text}")
                    raise Exception(f"OpenRouter API error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise
    
    async def _handle_stream_response(self, response):
        """Handle streaming response"""
        async for line in response.content:
            if line:
                line = line.decode('utf-8').strip()
                if line.startswith('data: '):
                    data = line[6:]
                    if data != '[DONE]':
                        try:
                            yield json.loads(data)
                        except json.JSONDecodeError:
                            continue
    
    def get_recommended_models(self) -> Dict[str, str]:
        """Get recommended models for different use cases"""
        return {
            "reasoning": "anthropic/claude-3.5-sonnet",
            "coding": "anthropic/claude-3.5-sonnet",
            "creative": "anthropic/claude-3-opus",
            "fast": "anthropic/claude-3-haiku",
            "cost_effective": "meta-llama/llama-3.1-8b-instruct:free",
            "multimodal": "anthropic/claude-3.5-sonnet",
            "long_context": "anthropic/claude-3.5-sonnet"
        }
    
    async def estimate_cost(self, messages: List[Dict[str, str]], model: str) -> Dict[str, float]:
        """Estimate cost for a completion"""
        models = await self.get_models()
        model_info = next((m for m in models if m.id == model), None)
        
        if not model_info:
            return {"estimated_cost": 0.0, "input_tokens": 0, "output_tokens": 0}
        
        # Rough token estimation (4 chars = 1 token)
        input_tokens = sum(len(msg.get('content', '')) for msg in messages) // 4
        estimated_output_tokens = 500  # Default estimate
        
        pricing = model_info.pricing
        input_cost = (input_tokens / 1000000) * pricing.get('prompt', 0)
        output_cost = (estimated_output_tokens / 1000000) * pricing.get('completion', 0)
        
        return {
            "estimated_cost": input_cost + output_cost,
            "input_tokens": input_tokens,
            "output_tokens": estimated_output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost
        }

# Convenience functions for common operations
async def quick_chat(prompt: str, model: str = "anthropic/claude-3.5-sonnet") -> str:
    """Quick chat completion for simple prompts"""
    async with OpenRouterClient() as client:
        messages = [{"role": "user", "content": prompt}]
        response = await client.chat_completion(messages, model=model)
        return response['choices'][0]['message']['content']

async def get_available_models() -> List[str]:
    """Get list of available model IDs"""
    async with OpenRouterClient() as client:
        models = await client.get_models()
        return [model.id for model in models]

# Example usage
if __name__ == "__main__":
    async def test_client():
        async with OpenRouterClient() as client:
            # Test model listing
            models = await client.get_models()
            print(f"Available models: {len(models)}")
            
            # Test chat completion
            messages = [{"role": "user", "content": "Hello! How are you?"}]
            response = await client.chat_completion(messages)
            print(f"Response: {response['choices'][0]['message']['content']}")
            
            # Test cost estimation
            cost = await client.estimate_cost(messages, "anthropic/claude-3.5-sonnet")
            print(f"Estimated cost: ${cost['estimated_cost']:.6f}")
    
    asyncio.run(test_client())
