#!/usr/bin/env python3
"""
Multi-transport LLM smoke test.
Tests direct provider connections and Portkey virtual keys.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.multi_transport import MultiTransportLLM


async def test_provider(
    provider: str,
    model: str,
    prompt: str = "Say 'ready' if you're online.",
    transport: str = None,
    max_tokens: int = 50,
    temperature: float = 0.0,
) -> None:
    """Test a single provider/model combination."""

    llm = MultiTransportLLM()
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Be concise."},
        {"role": "user", "content": prompt},
    ]

    try:
        print(f"\nTesting {provider}/{model} via {transport or 'auto'}...")
        response = await llm.complete(
            provider=provider,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            transport=transport,
        )

        result = {
            "success": True,
            "provider": response.provider,
            "model": response.model,
            "response": response.text[:200],
            "tokens": response.usage,
        }
        print(json.dumps(result, indent=2))

    except Exception as e:
        result = {
            "success": False,
            "provider": provider,
            "model": model,
            "error": str(e),
        }
        print(json.dumps(result, indent=2))


async def test_all_providers() -> None:
    """Test all configured providers with their common models."""

    # Test matrix - you can customize these models
    test_cases = [
        # OpenAI
        ("openai", "gpt-4o-mini", "direct"),
        ("openai", "gpt-4o-mini", "portkey"),
        # Anthropic
        ("anthropic", "claude-3-haiku-20240307", "direct"),
        ("anthropic", "claude-3-haiku-20240307", "portkey"),
        # OpenRouter (many models available)
        ("openrouter", "anthropic/claude-3.5-sonnet", "direct"),
        ("openrouter", "google/gemini-flash-1.5", "direct"),
        # Together AI
        ("together", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "direct"),
        ("together", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "portkey"),
        # Groq (fast inference)
        ("groq", "llama-3.1-8b-instant", "direct"),
        ("groq", "llama-3.1-8b-instant", "portkey"),
        # X.AI (Grok)
        ("xai", "grok-beta", "direct"),
        ("xai", "grok-beta", "portkey"),
        # DeepSeek
        ("deepseek", "deepseek-chat", "direct"),
        ("deepseek", "deepseek-chat", "portkey"),
        # Perplexity (with search)
        ("perplexity", "llama-3.1-sonar-small-128k-online", "direct"),
        ("perplexity", "llama-3.1-sonar-small-128k-online", "portkey"),
    ]

    for provider, model, transport in test_cases:
        await test_provider(provider, model, transport=transport)
        await asyncio.sleep(0.5)  # Rate limiting


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-transport LLM smoke test")
    parser.add_argument("--provider", help="Provider to test (e.g., openai, anthropic)")
    parser.add_argument("--model", help="Model ID for the provider")
    parser.add_argument(
        "--prompt", default="Say 'ready' if you're online.", help="Test prompt"
    )
    parser.add_argument(
        "--transport", choices=["direct", "portkey"], help="Force transport type"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=50, help="Max tokens to generate"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.0, help="Sampling temperature"
    )
    parser.add_argument(
        "--test-all", action="store_true", help="Test all configured providers"
    )

    args = parser.parse_args()

    if args.test_all:
        asyncio.run(test_all_providers())
    elif args.provider and args.model:
        asyncio.run(
            test_provider(
                args.provider,
                args.model,
                args.prompt,
                args.transport,
                args.max_tokens,
                args.temperature,
            )
        )
    else:
        print("Error: Specify --provider and --model, or use --test-all")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
