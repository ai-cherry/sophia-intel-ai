#!/usr/bin/env python3
"""
Reliable Provider Manager - Simple, Fast, Works
Only uses providers that actually work, with smart fallbacks
"""
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
from portkey_ai import Portkey
logger = logging.getLogger(__name__)
class RequirementType(Enum):
    """Types of requirements for provider selection"""
    REALTIME = "realtime"  # <1s response needed
    COMPLEX = "complex"  # Deep reasoning required
    CHEAP = "cheap"  # Minimize cost
    RELIABLE = "reliable"  # Maximum reliability
    DEFAULT = "default"  # No special requirements
@dataclass
class ProviderConfig:
    """Configuration for a single provider"""
    name: str
    virtual_key: str
    model: str
    max_tokens: int = 2000
    timeout: int = 30
    cost_per_1k_tokens: float = 0.01
    avg_latency_ms: int = 1000
    reliability_score: float = 0.95
class ReliableProviderManager:
    """
    Simple provider management - only reliable ones, smart routing
    Philosophy:
    - Use only providers that work 95%+ of the time
    - Simple fallback logic (primary -> backup)
    - Route based on actual requirements
    - Cache provider performance metrics
    """
    # Only the reliable providers (70% is not acceptable)
    PROVIDERS = {
        "openai": ProviderConfig(
            name="openai",
            virtual_key="openai-vk-190a60",
            model="gpt-3.5-turbo",
            cost_per_1k_tokens=0.002,
            avg_latency_ms=1200,
            reliability_score=0.98,
        ),
        "anthropic": ProviderConfig(
            name="anthropic",
            virtual_key="anthropic-vk-b42804",
            model="claude-3-haiku-20240307",
            cost_per_1k_tokens=0.00025,
            avg_latency_ms=700,
            reliability_score=0.97,
        ),
        "groq": ProviderConfig(
            name="groq",
            virtual_key="groq-vk-6b9b52",
            model="llama-3.1-8b-instant",
            cost_per_1k_tokens=0.00005,
            avg_latency_ms=500,
            reliability_score=0.95,
        ),
        "deepseek": ProviderConfig(
            name="deepseek",
            virtual_key="deepseek-vk-24102f",
            model="deepseek-chat",
            cost_per_1k_tokens=0.0001,
            avg_latency_ms=3500,
            reliability_score=0.96,
        ),
    }
    def __init__(self):
        """Initialize with Portkey API key"""
        self.api_key = os.environ.get("PORTKEY_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "PORTKEY_API_KEY is not set. Configure it via environment or ~/.config//env"
            )
        self.clients = {}
        self.performance_history = {}
        self.total_cost = 0.0
        self.request_count = 0
    def _get_client(self, provider_name: str) -> Portkey:
        """Get or create Portkey client for provider"""
        if provider_name not in self.clients:
            config = self.PROVIDERS[provider_name]
            self.clients[provider_name] = Portkey(
                api_key=self.api_key, virtual_key=config.virtual_key
            )
        return self.clients[provider_name]
    def select_provider(
        self, requirements: RequirementType = RequirementType.DEFAULT
    ) -> str:
        """
        Select best provider based on requirements
        Simple logic that actually works:
        - REALTIME -> Groq (fastest)
        - COMPLEX -> Anthropic (best reasoning)
        - CHEAP -> DeepSeek (lowest cost)
        - RELIABLE -> OpenAI (highest reliability)
        - DEFAULT -> OpenAI (balanced)
        """
        selection_map = {
            RequirementType.REALTIME: "groq",
            RequirementType.COMPLEX: "anthropic",
            RequirementType.CHEAP: "deepseek",
            RequirementType.RELIABLE: "openai",
            RequirementType.DEFAULT: "openai",
        }
        return selection_map[requirements]
    async def complete(
        self,
        prompt: str,
        requirements: RequirementType = RequirementType.DEFAULT,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_retries: int = 2,
    ) -> dict[str, Any]:
        """
        Complete a prompt with automatic provider selection and fallback
        Returns:
            Dict with 'response', 'provider', 'latency_ms', 'cost'
        """
        # Select primary provider
        primary_provider = self.select_provider(requirements)
        providers_to_try = [primary_provider]
        # Add fallback provider if not already selected
        if primary_provider != "openai":
            providers_to_try.append("openai")  # OpenAI as universal fallback
        last_error = None
        for provider_name in providers_to_try:
            for attempt in range(max_retries):
                try:
                    result = await self._execute_completion(
                        provider_name, prompt, system_prompt, temperature
                    )
                    # Track success
                    self._track_performance(provider_name, True, result["latency_ms"])
                    return result
                except Exception as e:
                    last_error = e
                    logger.warning(f"{provider_name} attempt {attempt + 1} failed: {e}")
                    # Track failure
                    self._track_performance(provider_name, False, 0)
                    if attempt < max_retries - 1:
                        await self._backoff(attempt)
        # All attempts failed
        raise Exception(f"All providers failed. Last error: {last_error}")
    async def _execute_completion(
        self,
        provider_name: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
    ) -> dict[str, Any]:
        """Execute completion with a specific provider"""
        config = self.PROVIDERS[provider_name]
        client = self._get_client(provider_name)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        start_time = time.time()
        # Simple synchronous call (Portkey doesn't have async)
        response = client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=config.max_tokens,
            temperature=temperature,
        )
        latency_ms = int((time.time() - start_time) * 1000)
        # Calculate cost
        total_tokens = 0
        if hasattr(response, "usage") and response.usage:
            total_tokens = response.usage.total_tokens
        cost = (total_tokens / 1000) * config.cost_per_1k_tokens
        self.total_cost += cost
        self.request_count += 1
        return {
            "response": response.choices[0].message.content,
            "provider": provider_name,
            "latency_ms": latency_ms,
            "cost": cost,
            "tokens": total_tokens,
        }
    def _track_performance(self, provider_name: str, success: bool, latency_ms: int):
        """Track provider performance for optimization"""
        if provider_name not in self.performance_history:
            self.performance_history[provider_name] = {
                "successes": 0,
                "failures": 0,
                "total_latency_ms": 0,
                "avg_latency_ms": 0,
            }
        history = self.performance_history[provider_name]
        if success:
            history["successes"] += 1
            history["total_latency_ms"] += latency_ms
            history["successes"] + history["failures"]
            history["avg_latency_ms"] = (
                history["total_latency_ms"] / history["successes"]
            )
        else:
            history["failures"] += 1
    async def _backoff(self, attempt: int):
        """Simple exponential backoff"""
        wait_time = 2**attempt
        await asyncio.sleep(wait_time)
    def get_stats(self) -> dict[str, Any]:
        """Get usage statistics"""
        stats = {
            "total_requests": self.request_count,
            "total_cost": round(self.total_cost, 4),
            "avg_cost_per_request": round(
                self.total_cost / max(self.request_count, 1), 4
            ),
            "provider_performance": {},
        }
        for provider, history in self.performance_history.items():
            total = history["successes"] + history["failures"]
            if total > 0:
                stats["provider_performance"][provider] = {
                    "success_rate": round(history["successes"] / total * 100, 1),
                    "avg_latency_ms": round(history["avg_latency_ms"], 0),
                    "total_requests": total,
                }
        return stats
    def get_cheapest_provider(self) -> str:
        """Get the cheapest available provider"""
        return min(self.PROVIDERS.items(), key=lambda x: x[1].cost_per_1k_tokens)[0]
    def get_fastest_provider(self) -> str:
        """Get the fastest available provider"""
        return min(self.PROVIDERS.items(), key=lambda x: x[1].avg_latency_ms)[0]
    def get_most_reliable_provider(self) -> str:
        """Get the most reliable provider"""
        return max(self.PROVIDERS.items(), key=lambda x: x[1].reliability_score)[0]
# Simple async wrapper since Portkey is sync
import asyncio
class AsyncReliableProvider(ReliableProviderManager):
    """Async wrapper for the provider manager"""
    async def _execute_completion(
        self,
        provider_name: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
    ) -> dict[str, Any]:
        """Execute completion in thread pool"""
        loop = asyncio.get_event_loop()
        # Run the synchronous method in executor
        config = self.PROVIDERS[provider_name]
        client = self._get_client(provider_name)
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        start_time = time.time()
        # Run in executor
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=temperature,
            ),
        )
        latency_ms = int((time.time() - start_time) * 1000)
        total_tokens = 0
        if hasattr(response, "usage") and response.usage:
            total_tokens = response.usage.total_tokens
        cost = (total_tokens / 1000) * config.cost_per_1k_tokens
        self.total_cost += cost
        self.request_count += 1
        return {
            "response": response.choices[0].message.content,
            "provider": provider_name,
            "latency_ms": latency_ms,
            "cost": cost,
            "tokens": total_tokens,
        }
if __name__ == "__main__":
    # Test the provider manager
    import asyncio
    async def test():
        provider = HybridProviderManager()
        # Test different requirement types
        tests = [
            ("What is 2+2?", RequirementType.REALTIME),
            ("Explain quantum computing in simple terms", RequirementType.COMPLEX),
            ("Hello", RequirementType.CHEAP),
            ("Write a Python function for sorting", RequirementType.DEFAULT),
        ]
        for prompt, req_type in tests:
            print(f"\nTesting: {prompt[:30]}... with {req_type.value}")
            try:
                result = await provider.complete(prompt, req_type)
                print(f"Provider: {result['provider']}")
                print(f"Latency: {result['latency_ms']}ms")
                print(f"Cost: ${result['cost']:.4f}")
                print(f"Response: {result['response'][:100]}...")
            except Exception as e:
                print(f"Error: {e}")
        # Show stats
        print("\n" + "=" * 50)
        print("Statistics:")
        stats = provider.get_stats()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Total cost: ${stats['total_cost']}")
        print(f"Provider performance: {stats['provider_performance']}")
    asyncio.run(test())
