#!/usr/bin/env python3
"""
Hybrid Provider Manager - Direct API for speed, Portkey for convenience
Uses direct API connections where faster, Portkey where simpler
"""
import asyncio
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

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
    method: str  # 'direct' or 'portkey'
    virtual_key: Optional[str] = None
    api_key_env: Optional[str] = None
    model: str = None
    max_tokens: int = 2000
    timeout: int = 30
    cost_per_1k_tokens: float = 0.01
    avg_latency_ms: int = 1000
    reliability_score: float = 0.95


class HybridProviderManager:
    """
    Optimized provider management - Direct API where faster, Portkey where convenient

    Based on testing results:
    - OpenAI: Direct API (2x faster)
    - Anthropic: Direct API (20% faster)
    - Groq: Portkey (works great)
    - DeepSeek: Portkey (no direct SDK)
    - Together: Portkey (simpler)
    - Mistral: Portkey (simpler)
    - Cohere: Portkey (simpler)
    """

    # Configuration based on actual test results
    PROVIDERS = {
        "openai": ProviderConfig(
            name="openai",
            method="direct",  # 453ms vs 1099ms
            api_key_env="OPENAI_API_KEY",
            model="gpt-3.5-turbo",
            cost_per_1k_tokens=0.002,
            avg_latency_ms=450,
            reliability_score=0.99,
        ),
        "anthropic": ProviderConfig(
            name="anthropic",
            method="direct",  # 410ms vs 523ms
            api_key_env="ANTHROPIC_API_KEY",
            model="claude-3-haiku-20240307",
            cost_per_1k_tokens=0.00025,
            avg_latency_ms=410,
            reliability_score=0.98,
        ),
        "groq": ProviderConfig(
            name="groq",
            method="portkey",  # Works great at 425ms
            virtual_key="groq-vk-6b9b52",
            model="llama-3.1-8b-instant",
            cost_per_1k_tokens=0.00005,
            avg_latency_ms=425,
            reliability_score=0.97,
        ),
        "deepseek": ProviderConfig(
            name="deepseek",
            method="portkey",  # No direct SDK
            virtual_key="deepseek-vk-24102f",
            model="deepseek-chat",
            cost_per_1k_tokens=0.0001,
            avg_latency_ms=3691,
            reliability_score=0.96,
        ),
        "together": ProviderConfig(
            name="together",
            method="portkey",  # 627ms, simpler than direct
            virtual_key="together-ai-670469",
            model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            cost_per_1k_tokens=0.0002,
            avg_latency_ms=627,
            reliability_score=0.95,
        ),
        "mistral": ProviderConfig(
            name="mistral",
            method="portkey",  # 546ms, works well
            virtual_key="mistral-vk-f92861",
            model="mistral-small-latest",
            cost_per_1k_tokens=0.0002,
            avg_latency_ms=546,
            reliability_score=0.95,
        ),
        "cohere": ProviderConfig(
            name="cohere",
            method="portkey",  # 756ms, stable
            virtual_key="cohere-vk-496fa9",
            model="command-r",
            cost_per_1k_tokens=0.0003,
            avg_latency_ms=756,
            reliability_score=0.94,
        ),
    }

    def __init__(self):
        """Initialize with both Portkey and direct clients"""
        self.portkey_api_key = os.environ.get("PORTKEY_API_KEY")
        if not self.portkey_api_key:
            raise RuntimeError(
                "PORTKEY_API_KEY is not set. Configure it via environment or ~/.config/artemis/env"
            )
        self.clients = {}
        self.performance_history = {}
        self.total_cost = 0.0
        self.request_count = 0

        # Initialize direct API clients
        self._init_direct_clients()

    def _init_direct_clients(self):
        """Initialize direct API clients for providers that support them"""
        # OpenAI
        if os.environ.get("OPENAI_API_KEY"):
            try:
                import openai

                self.clients["openai_direct"] = openai.OpenAI(
                    api_key=os.environ["OPENAI_API_KEY"]
                )
                logger.info("✅ OpenAI direct client initialized")
            except ImportError:
                logger.warning("openai package not installed")

        # Anthropic
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                import anthropic

                self.clients["anthropic_direct"] = anthropic.Anthropic(
                    api_key=os.environ["ANTHROPIC_API_KEY"]
                )
                logger.info("✅ Anthropic direct client initialized")
            except ImportError:
                logger.warning("anthropic package not installed")

        # Groq (optional, but Portkey works fine)
        if os.environ.get("GROQ_API_KEY"):
            try:
                from groq import Groq

                self.clients["groq_direct"] = Groq(api_key=os.environ["GROQ_API_KEY"])
                logger.info("✅ Groq direct client initialized")
            except ImportError:
                logger.warning("groq package not installed")

    def _get_portkey_client(self, provider_name: str):
        """Get or create Portkey client for provider"""
        cache_key = f"{provider_name}_portkey"
        if cache_key not in self.clients:
            config = self.PROVIDERS[provider_name]
            if config.virtual_key:
                from portkey_ai import Portkey

                self.clients[cache_key] = Portkey(
                    api_key=self.portkey_api_key, virtual_key=config.virtual_key
                )
        return self.clients.get(cache_key)

    def select_provider(
        self, requirements: RequirementType = RequirementType.DEFAULT
    ) -> str:
        """
        Select best provider based on requirements

        Optimized selection based on real test results:
        - REALTIME -> Groq (425ms via Portkey)
        - COMPLEX -> Anthropic (410ms via Direct API)
        - CHEAP -> DeepSeek (3691ms but cheapest)
        - RELIABLE -> OpenAI (453ms via Direct API)
        - DEFAULT -> OpenAI (best balance)
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
            Dict with 'response', 'provider', 'method', 'latency_ms', 'cost'
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
        """Execute completion with a specific provider using best method"""
        config = self.PROVIDERS[provider_name]

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.time()

        # Use direct API for OpenAI and Anthropic
        if config.method == "direct":
            response = await self._execute_direct(
                provider_name, messages, config, temperature
            )
        else:
            response = await self._execute_portkey(
                provider_name, messages, config, temperature
            )

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract response text and calculate cost
        if provider_name == "anthropic" and config.method == "direct":
            response_text = response.content[0].text if response.content else ""
            total_tokens = (
                response.usage.input_tokens + response.usage.output_tokens
                if hasattr(response, "usage")
                else 0
            )
        else:
            response_text = (
                response.choices[0].message.content
                if hasattr(response, "choices")
                else ""
            )
            total_tokens = (
                response.usage.total_tokens if hasattr(response, "usage") else 0
            )

        cost = (total_tokens / 1000) * config.cost_per_1k_tokens
        self.total_cost += cost
        self.request_count += 1

        return {
            "response": response_text,
            "provider": provider_name,
            "method": config.method,
            "latency_ms": latency_ms,
            "cost": cost,
            "tokens": total_tokens,
        }

    async def _execute_direct(
        self,
        provider_name: str,
        messages: list[dict],
        config: ProviderConfig,
        temperature: float,
    ) -> Any:
        """Execute using direct API"""
        loop = asyncio.get_event_loop()

        if provider_name == "openai":
            client = self.clients.get("openai_direct")
            if not client:
                raise Exception("OpenAI direct client not initialized")

            return await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    max_tokens=config.max_tokens,
                    temperature=temperature,
                ),
            )

        elif provider_name == "anthropic":
            client = self.clients.get("anthropic_direct")
            if not client:
                raise Exception("Anthropic direct client not initialized")

            return await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    model=config.model,
                    messages=messages,
                    max_tokens=config.max_tokens,
                    temperature=temperature,
                ),
            )

        elif provider_name == "groq" and "groq_direct" in self.clients:
            client = self.clients.get("groq_direct")
            return await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=config.model,
                    messages=messages,
                    max_tokens=config.max_tokens,
                    temperature=temperature,
                ),
            )

        else:
            raise Exception(f"Direct API not implemented for {provider_name}")

    async def _execute_portkey(
        self,
        provider_name: str,
        messages: list[dict],
        config: ProviderConfig,
        temperature: float,
    ) -> Any:
        """Execute using Portkey"""
        loop = asyncio.get_event_loop()
        client = self._get_portkey_client(provider_name)

        if not client:
            raise Exception(f"Portkey client not initialized for {provider_name}")

        return await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=temperature,
            ),
        )

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
                config = self.PROVIDERS[provider]
                stats["provider_performance"][provider] = {
                    "method": config.method,
                    "success_rate": round(history["successes"] / total * 100, 1),
                    "avg_latency_ms": round(history["avg_latency_ms"], 0),
                    "total_requests": total,
                }

        return stats

    def get_provider_summary(self) -> str:
        """Get a summary of provider configuration"""
        lines = ["Provider Configuration:"]
        lines.append("-" * 50)

        for name, config in self.PROVIDERS.items():
            status = (
                "✅"
                if config.method == "direct" and f"{name}_direct" in self.clients
                else "📡"
            )
            lines.append(
                f"{status} {name}: {config.method} ({config.avg_latency_ms}ms)"
            )

        return "\n".join(lines)


if __name__ == "__main__":
    # Test the hybrid provider manager
    import asyncio

    async def test():
        provider = HybridProviderManager()

        # Show configuration
        print(provider.get_provider_summary())
        print("\n" + "=" * 50)

        # Test different requirement types
        tests = [
            ("What is 2+2?", RequirementType.REALTIME),
            ("Explain quantum computing", RequirementType.COMPLEX),
            ("Hello", RequirementType.CHEAP),
            ("Write a sorting function", RequirementType.DEFAULT),
        ]

        for prompt, req_type in tests:
            print(f"\nTesting: {prompt[:30]}... [{req_type.value}]")
            try:
                result = await provider.complete(prompt, req_type)
                print(f"✅ Provider: {result['provider']} ({result['method']})")
                print(f"   Latency: {result['latency_ms']}ms")
                print(f"   Cost: ${result['cost']:.5f}")
                print(f"   Response: {result['response'][:50]}...")
            except Exception as e:
                print(f"❌ Error: {e}")

        # Show stats
        print("\n" + "=" * 50)
        print("Statistics:")
        stats = provider.get_stats()
        print(f"Total requests: {stats['total_requests']}")
        print(f"Total cost: ${stats['total_cost']}")
        print("\nProvider Performance:")
        for provider, perf in stats["provider_performance"].items():
            print(
                f"  {provider} ({perf['method']}): {perf['success_rate']}% success, {perf['avg_latency_ms']}ms avg"
            )

    asyncio.run(test())
