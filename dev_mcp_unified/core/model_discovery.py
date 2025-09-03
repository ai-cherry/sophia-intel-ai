"""
Model Discovery Service for OpenRouter Integration
Fetches, validates, and categorizes available models
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import httpx
from pathlib import Path

@dataclass
class ModelInfo:
    """Model metadata and capabilities"""
    id: str
    name: str
    provider: str
    description: Optional[str] = None
    context_window: int = 4096
    max_tokens: Optional[int] = None
    pricing: Optional[Dict[str, float]] = None
    capabilities: List[str] = None
    performance_tier: str = "standard"
    is_free: bool = False
    is_available: bool = True
    last_tested: Optional[str] = None
    test_score: float = 0.0
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.pricing is None:
            self.pricing = {}

class ModelDiscoveryService:
    """Service for discovering and managing available models"""
    
    def __init__(self, cache_dir: str = "/Users/lynnmusil/sophia-intel-ai/dev-mcp-unified/data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "models_cache.json"
        self.categories_file = self.cache_dir / "model_categories.json"
        self.test_results_file = self.cache_dir / "test_results.json"
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.cache_duration = timedelta(hours=6)
        
        # Initialize categorization rules
        self.provider_mapping = {
            "openai": "OpenAI",
            "anthropic": "Anthropic", 
            "meta-llama": "Meta",
            "meta": "Meta",
            "google": "Google",
            "mistralai": "Mistral AI",
            "mistral": "Mistral AI",
            "x-ai": "xAI",
            "deepseek": "DeepSeek",
            "qwen": "Qwen",
            "z-ai": "Zhipu AI",
            "cohere": "Cohere",
            "ai21": "AI21 Labs",
            "amazon": "Amazon",
            "microsoft": "Microsoft",
            "nvidia": "NVIDIA",
            "databricks": "Databricks",
            "together": "Together AI"
        }
        
        # Capability detection patterns
        self.capability_patterns = {
            "code": ["code", "coder", "codestral", "starcoder", "deepseek-coder"],
            "vision": ["vision", "4v", "multimodal", "gemini-pro-vision", "gpt-4-vision"],
            "reasoning": ["o1", "reasoning", "think", "r1"],
            "chat": ["chat", "turbo", "instruct", "sonnet", "haiku", "opus"],
            "long_context": ["32k", "64k", "128k", "200k", "turbo-128k", "claude-100k"],
            "function_calling": ["function", "tools", "gpt-4", "claude-3"],
            "creative": ["creative", "opus", "gemini-ultra"],
            "fast": ["fast", "turbo", "flash", "haiku", "7b", "mini"],
            "free": [":free", "free-", "-free"]
        }
        
        # Performance tier classification
        self.tier_rules = {
            "premium": ["gpt-4", "claude-3-opus", "claude-4", "gpt-5", "gemini-ultra", "o1"],
            "balanced": ["gpt-3.5", "claude-3-sonnet", "claude-3.5", "mistral-medium", "gemini-pro"],
            "budget": ["7b", "mini", "haiku", "flash", "small", "tiny"]
        }
        
    async def discover_all_models(self) -> List[ModelInfo]:
        """Fetch and validate all available models"""
        # Check cache first
        if self._is_cache_valid():
            return self._load_from_cache()
        
        # Fetch from OpenRouter API
        models = await self._fetch_models_from_api()
        
        # Test and validate models in parallel
        validated_models = await self._validate_models_batch(models)
        
        # Categorize models
        categorized_models = self._categorize_models(validated_models)
        
        # Save to cache
        self._save_to_cache(categorized_models)
        
        return categorized_models
    
    async def _fetch_models_from_api(self) -> List[ModelInfo]:
        """Fetch models from OpenRouter API"""
        if not self.api_key:
            print("Warning: No OpenRouter API key found")
            return self._get_default_models()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code != 200:
                    print(f"Failed to fetch models: {response.status_code}")
                    return self._get_default_models()
                
                data = response.json()
                models = []
                
                for item in data.get("data", []):
                    model_id = item.get("id", "")
                    if not model_id:
                        continue
                    
                    # Parse provider from model ID
                    provider = model_id.split("/")[0] if "/" in model_id else "unknown"
                    provider_name = self.provider_mapping.get(provider, provider.title())
                    
                    # Parse pricing
                    pricing = {}
                    if item.get("pricing"):
                        pricing = {
                            "prompt": float(item["pricing"].get("prompt", 0)) * 1000000,  # Convert to per 1M tokens
                            "completion": float(item["pricing"].get("completion", 0)) * 1000000
                        }
                    
                    model = ModelInfo(
                        id=model_id,
                        name=item.get("name", model_id),
                        provider=provider_name,
                        description=item.get("description"),
                        context_window=item.get("context_length", 4096),
                        max_tokens=item.get("top_provider", {}).get("max_completion_tokens"),
                        pricing=pricing,
                        is_free=":free" in model_id.lower() or pricing.get("prompt", 1) == 0
                    )
                    
                    models.append(model)
                
                print(f"Discovered {len(models)} models from OpenRouter")
                return models
                
        except Exception as e:
            print(f"Error fetching models: {e}")
            return self._get_default_models()
    
    async def _validate_models_batch(self, models: List[ModelInfo], batch_size: int = 10) -> List[ModelInfo]:
        """Test models in batches to verify they work"""
        validated = []
        
        # Process in batches to avoid rate limiting
        for i in range(0, len(models), batch_size):
            batch = models[i:i+batch_size]
            tasks = [self._test_model(model) for model in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for model, result in zip(batch, results):
                if isinstance(result, Exception):
                    model.is_available = False
                    model.error_rate = 1.0
                else:
                    model.is_available = result.get("success", False)
                    model.test_score = result.get("score", 0.0)
                    model.response_time_ms = result.get("response_time", 0)
                    model.error_rate = result.get("error_rate", 0)
                
                model.last_tested = datetime.now().isoformat()
                validated.append(model)
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        return validated
    
    async def _test_model(self, model: ModelInfo) -> Dict[str, Any]:
        """Test a single model with a simple prompt"""
        test_prompt = "What is 2+2? Reply with just the number."
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model.id,
                        "messages": [{"role": "user", "content": test_prompt}],
                        "max_tokens": 10,
                        "temperature": 0
                    }
                )
                
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    # Basic validation - should contain "4"
                    is_correct = "4" in str(content)
                    
                    return {
                        "success": True,
                        "score": 1.0 if is_correct else 0.5,
                        "response_time": response_time,
                        "error_rate": 0
                    }
                else:
                    return {
                        "success": False,
                        "score": 0,
                        "response_time": response_time,
                        "error_rate": 1.0
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "score": 0,
                "response_time": 0,
                "error_rate": 1.0,
                "error": str(e)
            }
    
    def _categorize_models(self, models: List[ModelInfo]) -> List[ModelInfo]:
        """Categorize models by capabilities and performance"""
        for model in models:
            model_id_lower = model.id.lower()
            model_name_lower = model.name.lower()
            
            # Detect capabilities
            capabilities = []
            for capability, patterns in self.capability_patterns.items():
                if any(pattern in model_id_lower or pattern in model_name_lower 
                       for pattern in patterns):
                    capabilities.append(capability)
            
            # Default capability if none detected
            if not capabilities:
                capabilities.append("chat")
            
            model.capabilities = capabilities
            
            # Determine performance tier
            for tier, patterns in self.tier_rules.items():
                if any(pattern in model_id_lower or pattern in model_name_lower 
                       for pattern in patterns):
                    model.performance_tier = tier
                    break
            
            # Special handling for free models
            if model.is_free:
                model.performance_tier = "budget"
        
        return models
    
    def _is_cache_valid(self) -> bool:
        """Check if cache exists and is recent"""
        if not self.cache_file.exists():
            return False
        
        # Check cache age
        cache_age = datetime.now() - datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        return cache_age < self.cache_duration
    
    def _load_from_cache(self) -> List[ModelInfo]:
        """Load models from cache file"""
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
                return [ModelInfo(**item) for item in data]
        except Exception as e:
            print(f"Error loading cache: {e}")
            return []
    
    def _save_to_cache(self, models: List[ModelInfo]):
        """Save models to cache file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump([asdict(m) for m in models], f, indent=2)
            
            # Also save categorization metadata
            categories = self._generate_categories_metadata(models)
            with open(self.categories_file, 'w') as f:
                json.dump(categories, f, indent=2)
                
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def _generate_categories_metadata(self, models: List[ModelInfo]) -> Dict[str, Any]:
        """Generate metadata about model categories"""
        providers = {}
        capabilities = {}
        tiers = {}
        
        for model in models:
            # Count by provider
            if model.provider not in providers:
                providers[model.provider] = []
            providers[model.provider].append(model.id)
            
            # Count by capability
            for cap in model.capabilities:
                if cap not in capabilities:
                    capabilities[cap] = []
                capabilities[cap].append(model.id)
            
            # Count by tier
            if model.performance_tier not in tiers:
                tiers[model.performance_tier] = []
            tiers[model.performance_tier].append(model.id)
        
        return {
            "providers": providers,
            "capabilities": capabilities,
            "performance_tiers": tiers,
            "total_models": len(models),
            "free_models": [m.id for m in models if m.is_free],
            "available_models": [m.id for m in models if m.is_available],
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_default_models(self) -> List[ModelInfo]:
        """Return default models when API is unavailable"""
        return [
            ModelInfo(
                id="openai/gpt-4o",
                name="GPT-4o",
                provider="OpenAI",
                capabilities=["chat", "code", "reasoning"],
                performance_tier="premium",
                context_window=128000
            ),
            ModelInfo(
                id="anthropic/claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="Anthropic",
                capabilities=["chat", "code", "reasoning"],
                performance_tier="premium",
                context_window=200000
            ),
            ModelInfo(
                id="meta-llama/llama-3.3-70b-instruct",
                name="Llama 3.3 70B",
                provider="Meta",
                capabilities=["chat", "code"],
                performance_tier="balanced",
                context_window=8192
            ),
            ModelInfo(
                id="x-ai/grok-2-1212",
                name="Grok 2",
                provider="xAI",
                capabilities=["chat", "reasoning"],
                performance_tier="premium",
                context_window=131072
            ),
            ModelInfo(
                id="google/gemini-2.0-flash-exp",
                name="Gemini 2.0 Flash",
                provider="Google",
                capabilities=["chat", "fast"],
                performance_tier="budget",
                context_window=32768
            ),
            ModelInfo(
                id="deepseek/deepseek-chat",
                name="DeepSeek Chat",
                provider="DeepSeek",
                capabilities=["chat", "code"],
                performance_tier="balanced",
                context_window=32768
            )
        ]

# CLI for testing
if __name__ == "__main__":
    async def main():
        service = ModelDiscoveryService()
        models = await service.discover_all_models()
        
        print(f"\n{'='*80}")
        print(f"Discovered {len(models)} models")
        print(f"{'='*80}\n")
        
        # Group by provider
        by_provider = {}
        for model in models:
            if model.provider not in by_provider:
                by_provider[model.provider] = []
            by_provider[model.provider].append(model)
        
        for provider, provider_models in sorted(by_provider.items()):
            print(f"\n{provider} ({len(provider_models)} models):")
            for m in provider_models[:5]:  # Show first 5
                status = "✅" if m.is_available else "❌"
                free = "🆓" if m.is_free else "💰"
                print(f"  {status} {free} {m.name} - {', '.join(m.capabilities)}")
    
    asyncio.run(main())