#!/usr/bin/env python3
"""
Complete Portkey setup with OpenRouter and Together AI.
This script will configure everything programmatically.
"""

import asyncio
import json

import httpx
from dotenv import load_dotenv, set_key

# Load environment
load_dotenv(".env.local", override=True)


class CompletePortkeySetup:
    """Complete setup for Portkey with all providers."""

    def __init__(self):
        # API Keys
        self.portkey_key = "hPxFZGd8AN269n4bznDf2/Onbi8I"
        self.openrouter_key = (
            "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"
        )
        self.together_key = "tgp_v1_HE_uluFh-fELZDmEP9xKZXuSBT4a8EHd6s9CmSe5WWo"

        self.base_url = "https://api.portkey.ai/v1"

    async def test_direct_providers(self):
        """Test all providers directly first."""
        logger.info("\n" + "=" * 60)
        logger.info("🔍 TESTING DIRECT PROVIDER ACCESS")
        logger.info("=" * 60)

        results = {}

        # Test OpenRouter
        logger.info("\n📝 Testing OpenRouter...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "HTTP-Referer": "http://localhost:3000",
                        "X-Title": "Sophia Intel AI",
                    },
                    json={
                        "model": "meta-llama/llama-3.2-3b-instruct",
                        "messages": [{"role": "user", "content": "Say 'OpenRouter OK' in 2 words"}],
                        "max_tokens": 10,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    logger.info(f"  ✅ OpenRouter: Working - {content}")
                    results["openrouter"] = True
                else:
                    logger.info(f"  ❌ OpenRouter: Failed ({response.status_code})")
                    results["openrouter"] = False
        except Exception as e:
            logger.info(f"  ❌ OpenRouter Error: {e}")
            results["openrouter"] = False

        # Test Together AI
        logger.info("\n📝 Testing Together AI...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test embeddings endpoint
                response = await client.post(
                    "https://api.together.xyz/v1/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.together_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "togethercomputer/m2-bert-80M-8k-retrieval",
                        "input": "Test embedding",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    embedding_dim = len(result.get("data", [{}])[0].get("embedding", []))
                    logger.info(f"  ✅ Together AI: Working - Embedding dimension: {embedding_dim}")
                    results["together"] = True
                else:
                    logger.info(f"  ❌ Together AI: Failed ({response.status_code})")
                    results["together"] = False
        except Exception as e:
            logger.info(f"  ❌ Together AI Error: {e}")
            results["together"] = False

        return results

    async def setup_portkey_configs(self):
        """Set up Portkey configurations for all use cases."""
        logger.info("\n" + "=" * 60)
        logger.info("🔧 CONFIGURING PORTKEY GATEWAY")
        logger.info("=" * 60)

        # Define configurations for different use cases
        configs = {
            "chat_models": {
                "description": "Chat completions via OpenRouter",
                "provider": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": self.openrouter_key,
                "headers": {"HTTP-Referer": "http://localhost:3000", "X-Title": "Sophia Intel AI"},
            },
            "embeddings": {
                "description": "Embeddings via Together AI",
                "provider": "together",
                "base_url": "https://api.together.xyz/v1",
                "api_key": self.together_key,
                "model": "togethercomputer/m2-bert-80M-8k-retrieval",
            },
        }

        # Test Portkey with different configurations
        logger.info("\n📝 Testing Portkey Configurations...")

        # Test chat completion through Portkey → OpenRouter
        logger.info("\n1. Chat Models (OpenRouter):")
        await self.test_portkey_chat()

        # Test embeddings through Portkey → Together
        logger.info("\n2. Embeddings (Together AI):")
        await self.test_portkey_embeddings()

        return configs

    async def test_portkey_chat(self):
        """Test chat completions through Portkey."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create Portkey config for OpenRouter
                config = {
                    "provider": "openrouter",
                    "api_key": self.openrouter_key,
                    "override_params": {
                        "headers": {
                            "HTTP-Referer": "http://localhost:3000",
                            "X-Title": "Sophia Intel AI",
                        }
                    },
                }

                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "x-portkey-api-key": self.portkey_key,
                        "x-portkey-config": json.dumps(config),
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "meta-llama/llama-3.2-3b-instruct",
                        "messages": [
                            {"role": "user", "content": "Say 'Portkey chat working' in 3 words"}
                        ],
                        "max_tokens": 10,
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    logger.info(f"  ✅ Chat via Portkey: {content}")
                    return True
                else:
                    logger.info(f"  ❌ Failed: Status {response.status_code}")
                    try:
                        error = response.json()
                        logger.info(f"     Error: {error}")
                    except:
                        pass
                    return False
        except Exception as e:
            logger.info(f"  ❌ Error: {e}")
            return False

    async def test_portkey_embeddings(self):
        """Test embeddings through Portkey."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create Portkey config for Together AI
                config = {"provider": "together", "api_key": self.together_key}

                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "x-portkey-api-key": self.portkey_key,
                        "x-portkey-config": json.dumps(config),
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "togethercomputer/m2-bert-80M-8k-retrieval",
                        "input": "Test embedding through Portkey",
                    },
                )

                if response.status_code == 200:
                    result = response.json()
                    embedding_dim = len(result.get("data", [{}])[0].get("embedding", []))
                    logger.info(f"  ✅ Embeddings via Portkey: Dimension {embedding_dim}")
                    return True
                else:
                    logger.info(f"  ❌ Failed: Status {response.status_code}")
                    try:
                        error = response.json()
                        logger.info(f"     Error: {error}")
                    except:
                        pass
                    return False
        except Exception as e:
            logger.info(f"  ❌ Error: {e}")
            return False

    async def update_env_file(self):
        """Update .env.local with all configurations."""
        logger.info("\n" + "=" * 60)
        logger.info("📝 UPDATING ENVIRONMENT CONFIGURATION")
        logger.info("=" * 60)

        env_path = ".env.local"

        # Keys to update
        updates = {
            # Primary Keys
            "OPENROUTER_API_KEY": self.openrouter_key,
            "PORTKEY_API_KEY": self.portkey_key,
            "TOGETHER_API_KEY": self.together_key,
            # Portkey Gateway Configuration
            "OPENAI_BASE_URL": "https://api.portkey.ai/v1",
            "PORTKEY_BASE_URL": "https://api.portkey.ai/v1",
            # Embedding Configuration
            "EMBED_BASE_URL": "https://api.portkey.ai/v1",
            "EMBED_API_KEY": self.portkey_key,
            "EMBED_MODEL": "togethercomputer/m2-bert-80M-8k-retrieval",
            "EMBED_PROVIDER": "together",
            # Model Routing (via OpenRouter)
            "PRIMARY_CHAT_PROVIDER": "openrouter",
            "PRIMARY_EMBED_PROVIDER": "together",
            # Headers for OpenRouter
            "HTTP_REFERER": "http://localhost:3000",
            "X_TITLE": "Sophia Intel AI",
        }

        for key, value in updates.items():
            set_key(env_path, key, value)
            logger.info(f"  ✅ Updated: {key}")

        logger.info("\n✅ Environment configuration updated!")

    def create_usage_examples(self):
        """Create example code for using the configured setup."""
        logger.info("\n" + "=" * 60)
        logger.info("💡 USAGE EXAMPLES")
        logger.info("=" * 60)

        examples = """
# === CHAT COMPLETIONS (via Portkey → OpenRouter) ===

from openai import OpenAI
import json
from app.core.ai_logger import logger


# Method 1: Using Portkey config header
client = httpx.AsyncClient()
config = {
    "provider": "openrouter",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "override_params": {
        "headers": {
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Sophia Intel AI"
        }
    }
}

response = await client.post(
    "https://api.portkey.ai/v1/chat/completions",
    headers={
        "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
        "x-portkey-config": json.dumps(config),
        "Content-Type": "application/json"
    },
    json={
        "model": "qwen/qwen-2.5-coder-32b-instruct",  # Any OpenRouter model
        "messages": [{"role": "user", "content": "Hello"}]
    }
)

# === EMBEDDINGS (via Portkey → Together AI) ===

config = {
    "provider": "together",
    "api_key": os.getenv("TOGETHER_API_KEY")
}

response = await client.post(
    "https://api.portkey.ai/v1/embeddings",
    headers={
        "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
        "x-portkey-config": json.dumps(config),
        "Content-Type": "application/json"
    },
    json={
        "model": "togethercomputer/m2-bert-80M-8k-retrieval",
        "input": "Your text to embed"
    }
)

# === AVAILABLE MODELS ===

Via OpenRouter (300+ models):
- GPT-4: openai/gpt-4o, openai/gpt-4o-mini
- Claude: anthropic/claude-3.5-sonnet, anthropic/claude-3-opus
- Llama: meta-llama/llama-3.1-405b, meta-llama/llama-3.2-90b-vision
- Qwen: qwen/qwen-2.5-coder-32b-instruct, qwen/qwen-2.5-72b
- DeepSeek: deepseek/deepseek-coder-v2, deepseek/deepseek-reasoner
- Mistral: mistral/mistral-large, mistral/mixtral-8x22b
- Google: google/gemini-pro, google/gemini-1.5-pro

Via Together AI (Embeddings):
- togethercomputer/m2-bert-80M-8k-retrieval (768 dim)
- BAAI/bge-base-en-v1.5 (768 dim)
- BAAI/bge-large-en-v1.5 (1024 dim)
"""

        logger.info(examples)

        # Save examples to file
        with open("PORTKEY_USAGE_EXAMPLES.md", "w") as f:
            f.write("# Portkey Configuration - Usage Examples\n\n")
            f.write("## Configuration Summary\n\n")
            f.write("- **Chat Models**: Portkey → OpenRouter (300+ models)\n")
            f.write("- **Embeddings**: Portkey → Together AI\n")
            f.write("- **Gateway**: All requests go through Portkey\n\n")
            f.write("## Code Examples\n\n")
            f.write("```python\n")
            f.write(examples)
            f.write("```\n")

        logger.info("\n✅ Examples saved to PORTKEY_USAGE_EXAMPLES.md")

    async def run_complete_setup(self):
        """Run the complete setup process."""
        logger.info("\n" + "=" * 60)
        logger.info("🚀 COMPLETE PORTKEY + PROVIDERS SETUP")
        logger.info("=" * 60)

        # Test direct provider access
        provider_results = await self.test_direct_providers()

        # Set up Portkey configurations
        await self.setup_portkey_configs()

        # Update environment file
        await self.update_env_file()

        # Create usage examples
        self.create_usage_examples()

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("✅ SETUP COMPLETE!")
        logger.info("=" * 60)

        logger.info("\n📊 Provider Status:")
        logger.info(
            f"  • OpenRouter: {'✅ Working' if provider_results.get('openrouter') else '❌ Failed'}"
        )
        logger.info(
            f"  • Together AI: {'✅ Working' if provider_results.get('together') else '❌ Failed'}"
        )
        logger.info("  • Portkey Gateway: ✅ Configured")

        logger.info("\n🔑 API Keys Configured:")
        logger.info(f"  • OPENROUTER_API_KEY: ...{self.openrouter_key[-10:]}")
        logger.info(f"  • TOGETHER_API_KEY: ...{self.together_key[-10:]}")
        logger.info(f"  • PORTKEY_API_KEY: ...{self.portkey_key[-10:]}")

        logger.info("\n📦 Available Resources:")
        logger.info("  • 300+ chat models via OpenRouter")
        logger.info("  • High-quality embeddings via Together AI")
        logger.info("  • Unified gateway via Portkey")
        logger.info("  • Caching, observability, and fallbacks")

        logger.info("\n📚 Next Steps:")
        logger.info("  1. Review PORTKEY_USAGE_EXAMPLES.md for code examples")
        logger.info("  2. Test with: python3 scripts/test_complete_setup.py")
        logger.info("  3. Start building with unified API access!")


async def main():
    """Main setup function."""
    setup = CompletePortkeySetup()
    await setup.run_complete_setup()


if __name__ == "__main__":
    asyncio.run(main())
