#!/usr/bin/env python3
"""
Test the complete Portkey setup with all providers and models.
Includes OpenRouter chat models, Together AI embeddings, and z-ai/glm-4.5.
"""

import asyncio
import json
import os

import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local', override=True)

class CompleteSetupTester:
    """Test all configured providers and models."""

    def __init__(self):
        self.portkey_key = os.getenv("PORTKEY_API_KEY")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")
        self.together_key = os.getenv("TOGETHER_API_KEY")

    async def test_chat_models(self):
        """Test various chat models through Portkey → OpenRouter."""
        print("\n" + "="*60)
        print("🤖 TESTING CHAT MODELS (Portkey → OpenRouter)")
        print("="*60)

        # Models to test
        models = [
            {
                "name": "GPT-4o Mini",
                "model": "openai/gpt-4o-mini",
                "prompt": "Say 'GPT working' in 2 words"
            },
            {
                "name": "Claude 3 Haiku",
                "model": "anthropic/claude-3-haiku-20240307",
                "prompt": "Say 'Claude working' in 2 words"
            },
            {
                "name": "Qwen 2.5 Coder",
                "model": "qwen/qwen-2.5-coder-32b-instruct",
                "prompt": "Write print('Hello') in Python"
            },
            {
                "name": "DeepSeek Coder",
                "model": "deepseek/deepseek-coder-v2",
                "prompt": "Write console.log('Hi') in JavaScript"
            },
            {
                "name": "Llama 3.2",
                "model": "meta-llama/llama-3.2-3b-instruct",
                "prompt": "Say 'Llama ready' in 2 words"
            },
            {
                "name": "GLM-4.5 (Z-AI)",
                "model": "z-ai/glm-4.5",
                "prompt": "Say 'GLM working' in 2 words"
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            for test in models:
                print(f"\n📝 Testing {test['name']}...")
                print(f"   Model: {test['model']}")

                # Portkey config for OpenRouter
                config = {
                    "provider": "openrouter",
                    "api_key": self.openrouter_key,
                    "override_params": {
                        "headers": {
                            "HTTP-Referer": "http://localhost:3000",
                            "X-Title": "Sophia Intel AI"
                        }
                    }
                }

                try:
                    response = await client.post(
                        "https://api.portkey.ai/v1/chat/completions",
                        headers={
                            "x-portkey-api-key": self.portkey_key,
                            "x-portkey-config": json.dumps(config),
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": test["model"],
                            "messages": [{"role": "user", "content": test["prompt"]}],
                            "max_tokens": 20,
                            "temperature": 0.1
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        print(f"   ✅ Success: {content[:50]}")
                    else:
                        print(f"   ❌ Failed: Status {response.status_code}")
                        if response.status_code == 404:
                            print("      Model might not be available")

                except Exception as e:
                    print(f"   ❌ Error: {str(e)[:100]}")

    async def test_embeddings(self):
        """Test embeddings through Portkey → Together AI."""
        print("\n" + "="*60)
        print("🔢 TESTING EMBEDDINGS (Portkey → Together AI)")
        print("="*60)

        # Fix: Use "together-ai" instead of "together"
        config = {
            "provider": "together-ai",  # Correct provider name
            "api_key": self.together_key
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.portkey.ai/v1/embeddings",
                    headers={
                        "x-portkey-api-key": self.portkey_key,
                        "x-portkey-config": json.dumps(config),
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "togethercomputer/m2-bert-80M-8k-retrieval",
                        "input": "Test embedding through Portkey gateway"
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    embedding_dim = len(result.get("data", [{}])[0].get("embedding", []))
                    print(f"✅ Embeddings working! Dimension: {embedding_dim}")
                else:
                    print(f"❌ Failed: Status {response.status_code}")
                    try:
                        error = response.json()
                        print(f"   Error: {error}")
                    except:
                        pass

        except Exception as e:
            print(f"❌ Error: {e}")

    async def test_direct_access(self):
        """Test direct access to providers (bypass Portkey)."""
        print("\n" + "="*60)
        print("🔍 TESTING DIRECT PROVIDER ACCESS")
        print("="*60)

        # Test OpenRouter directly
        print("\n1. OpenRouter Direct:")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "Sophia Intel AI"
                    },
                    json={
                        "model": "meta-llama/llama-3.2-3b-instruct",
                        "messages": [{"role": "user", "content": "Say 'Direct OK' in 2 words"}],
                        "max_tokens": 10
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"  ✅ OpenRouter: {content}")
                else:
                    print(f"  ❌ OpenRouter: Failed ({response.status_code})")
        except Exception as e:
            print(f"  ❌ OpenRouter Error: {e}")

        # Test Together AI directly
        print("\n2. Together AI Direct:")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Try chat endpoint
                response = await client.post(
                    "https://api.together.xyz/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.together_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                        "messages": [{"role": "user", "content": "Say 'Together OK' in 2 words"}],
                        "max_tokens": 10
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"  ✅ Together AI: {content}")
                else:
                    print(f"  ❌ Together AI: Failed ({response.status_code})")
        except Exception as e:
            print(f"  ❌ Together AI Error: {e}")

    def print_configuration_summary(self):
        """Print current configuration summary."""
        print("\n" + "="*60)
        print("📊 CONFIGURATION SUMMARY")
        print("="*60)

        print("\n🔑 API Keys:")
        print(f"  • PORTKEY_API_KEY: ...{self.portkey_key[-10:] if self.portkey_key else 'Not set'}")
        print(f"  • OPENROUTER_API_KEY: ...{self.openrouter_key[-10:] if self.openrouter_key else 'Not set'}")
        print(f"  • TOGETHER_API_KEY: ...{self.together_key[-10:] if self.together_key else 'Not set'}")

        print("\n📦 Available Resources:")
        print("  • Chat Models: 300+ via OpenRouter")
        print("    - GPT-4o, GPT-4o-mini")
        print("    - Claude 3.5 Sonnet, Opus, Haiku")
        print("    - Qwen 2.5 Coder (32B)")
        print("    - DeepSeek Coder v2")
        print("    - Llama 3.1/3.2 models")
        print("    - GLM-4.5 (Z-AI)")
        print("    - And 290+ more models")
        print("\n  • Embeddings: Via Together AI")
        print("    - togethercomputer/m2-bert-80M-8k-retrieval")
        print("    - BAAI/bge models")
        print("\n  • Gateway: Portkey")
        print("    - Caching & fallbacks")
        print("    - Observability")
        print("    - Cost tracking")

    async def run_all_tests(self):
        """Run all tests."""
        print("\n" + "="*60)
        print("🚀 COMPLETE SYSTEM TEST")
        print("="*60)

        # Test direct access first
        await self.test_direct_access()

        # Test chat models through Portkey
        await self.test_chat_models()

        # Test embeddings through Portkey
        await self.test_embeddings()

        # Print configuration summary
        self.print_configuration_summary()

        print("\n" + "="*60)
        print("✅ TESTING COMPLETE!")
        print("="*60)

        print("\n💡 Quick Start Examples:")
        print("""
# Chat completion (any OpenRouter model):
from openai import OpenAI
client = OpenAI(
    api_key=os.getenv("PORTKEY_API_KEY"),
    base_url="https://api.portkey.ai/v1",
    default_headers={
        "x-portkey-config": json.dumps({
            "provider": "openrouter",
            "api_key": os.getenv("OPENROUTER_API_KEY")
        })
    }
)

response = client.chat.completions.create(
    model="z-ai/glm-4.5",  # Or any model from OpenRouter
    messages=[{"role": "user", "content": "Hello"}]
)
        """)


async def main():
    """Main test function."""
    tester = CompleteSetupTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
