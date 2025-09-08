#!/usr/bin/env python3
"""
Test Portkey virtual keys after they're created.
Run this AFTER you've created the virtual keys in Portkey dashboard.
"""

import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

# Load environment
load_dotenv(".env.local", override=True)


async def test_virtual_key(name: str, env_var: str, test_model: str, test_prompt: str):
    """Test a single virtual key."""

    vk_id = os.getenv(env_var)

    if not vk_id or vk_id.startswith("vk_xxx"):
        logger.info(f"  ⚠️  {name}: Not configured (set {env_var} in .env.local)")
        return False

    try:
        # Use the virtual key ID as the API key
        client = AsyncOpenAI(api_key=vk_id, base_url="https://api.portkey.ai/v1")

        response = await client.chat.completions.create(
            model=test_model,
            messages=[{"role": "user", "content": test_prompt}],
            max_tokens=20,
            temperature=0.1,
        )

        content = response.choices[0].message.content
        logger.info(f"  ✅ {name}: Working!")
        logger.info(f"     Model: {test_model}")
        logger.info(f"     Response: {content[:50]}")
        return True

    except Exception as e:
        logger.info(f"  ❌ {name}: Failed")
        logger.info(f"     Error: {str(e)[:100]}")
        return False


async def main():
    """Test all virtual keys."""

    logger.info("\n" + "=" * 60)
    logger.info("🔑 PORTKEY VIRTUAL KEYS TEST")
    logger.info("=" * 60)

    # Check if Portkey API key is set
    portkey_key = os.getenv("PORTKEY_API_KEY")
    if not portkey_key:
        logger.info("❌ PORTKEY_API_KEY not found in .env.local")
        return

    logger.info(f"✅ Portkey API Key: {portkey_key[:10]}...")

    # Virtual keys to test
    tests = [
        {
            "name": "Main OpenRouter",
            "env_var": "PORTKEY_VK_MAIN",
            "model": "openrouter/auto",
            "prompt": "Say 'Main working' in 2 words",
        },
        {
            "name": "GPT Models",
            "env_var": "PORTKEY_VK_GPT",
            "model": "openai/gpt-4o-mini",
            "prompt": "Say 'GPT working' in 2 words",
        },
        {
            "name": "Claude Models",
            "env_var": "PORTKEY_VK_CLAUDE",
            "model": "anthropic/claude-3-haiku-20240307",
            "prompt": "Say 'Claude working' in 2 words",
        },
        {
            "name": "Qwen Coder",
            "env_var": "PORTKEY_VK_QWEN",
            "model": "qwen/qwen-2.5-coder-32b-instruct",
            "prompt": "Write 'logger.info(1+1)' in Python",
        },
        {
            "name": "DeepSeek Coder",
            "env_var": "PORTKEY_VK_DEEPSEEK",
            "model": "deepseek/deepseek-coder-v2",
            "prompt": "Write 'console.log(1+1)' in JavaScript",
        },
        {
            "name": "Fast Inference",
            "env_var": "PORTKEY_VK_FAST",
            "model": "meta-llama/llama-3.2-3b-instruct",
            "prompt": "Say 'Fast' in one word",
        },
        {
            "name": "Groq Speed",
            "env_var": "PORTKEY_VK_GROQ",
            "model": "groq/llama-3.1-70b-versatile",
            "prompt": "Say 'Groq' in one word",
        },
    ]

    logger.info("\nTesting Virtual Keys:")
    logger.info("-" * 40)

    results = []
    for test in tests:
        result = await test_virtual_key(
            test["name"], test["env_var"], test["model"], test["prompt"]
        )
        results.append((test["name"], result))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 SUMMARY")
    logger.info("=" * 60)

    working = sum(1 for _, success in results if success)
    total = len(results)

    logger.info(f"\n✅ Working: {working}/{total}")

    if working == total:
        logger.info("\n🎉 All virtual keys are working!")
        logger.info("\nYour Portkey setup is complete. You can now:")
        logger.info("  • Use any of the 300+ OpenRouter models")
        logger.info("  • Get caching and observability from Portkey")
        logger.info("  • Switch models easily by changing virtual keys")
    elif working == 0:
        logger.info("\n⚠️  No virtual keys configured yet")
        logger.info("\nNext steps:")
        logger.info("  1. Go to https://app.portkey.ai")
        logger.info(
            "  2. Create the 7 virtual keys as described in PORTKEY_EXACT_SETUP.md"
        )
        logger.info("  3. Add the virtual key IDs to .env.local")
        logger.info("  4. Run this test again")
    else:
        logger.info(f"\n⚠️  {total - working} virtual keys need configuration")
        logger.info("\nCheck which ones failed above and:")
        logger.info("  1. Create them in Portkey dashboard")
        logger.info("  2. Add their IDs to .env.local")

    # Show example usage
    if working > 0:
        logger.info("\n" + "=" * 60)
        logger.info("💡 EXAMPLE USAGE")
        logger.info("=" * 60)

        print(
            """
# In your code, use it like this:

from openai import OpenAI
from app.core.ai_logger import logger


# For GPT models
client = OpenAI(
    api_key=os.getenv("PORTKEY_VK_GPT"),
    base_url="https://api.portkey.ai/v1"
)

response = client.chat.completions.create(
    model="openai/gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)

# For Claude models
client = OpenAI(
    api_key=os.getenv("PORTKEY_VK_CLAUDE"),
    base_url="https://api.portkey.ai/v1"
)

response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",
    messages=[{"role": "user", "content": "Hello"}]
)
        """
        )


if __name__ == "__main__":
    asyncio.run(main())
