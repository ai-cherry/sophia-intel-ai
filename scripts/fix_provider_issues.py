#!/usr/bin/env python3
"""
Fix LLM Provider Issues - Get them ALL working
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["PORTKEY_API_KEY"] = "hPxFZGd8AN269n4bznDf2/Onbi8I"

from portkey_ai import Portkey

# Provider-specific fixes
PROVIDER_FIXES = {
    "xai": {
        "issue": "Invalid model format",
        "models_to_try": ["grok-beta", "grok-2", "grok-1", "grok"],
        "vk": "xai-vk-e65d0f",
    },
    "perplexity": {
        "issue": "Invalid model format",
        "models_to_try": [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-small-128k-chat",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-large-128k-chat",
            "sonar-small-online",
            "sonar-medium-online",
            "pplx-7b-online",
            "pplx-70b-online",
        ],
        "vk": "perplexity-vk-56c172",
    },
    "gemini": {
        "issue": "Quota exceeded",
        "models_to_try": [
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
            "gemini-1.5-pro",
            "gemini-pro",
        ],
        "vk": "gemini-vk-3d6108",
        "note": "May need billing setup or wait for quota reset",
    },
}


async def test_model(provider: str, model: str, vk: str) -> dict:
    """Test a specific model for a provider"""
    try:
        client = Portkey(api_key=os.environ["PORTKEY_API_KEY"], virtual_key=vk)

        # Minimal test message
        messages = [{"role": "user", "content": "Say 'OK'"}]

        # Try with minimal parameters
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=model, messages=messages, max_tokens=10
                ),
            ),
            timeout=15.0,
        )

        return {
            "success": True,
            "model": model,
            "response": (
                response.choices[0].message.content
                if response.choices
                else "No response"
            ),
        }

    except Exception as e:
        return {"success": False, "model": model, "error": str(e)[:200]}


async def fix_provider(provider: str, config: dict) -> dict:
    """Try to fix a specific provider"""
    print(f"\n🔧 Attempting to fix {provider}...")
    print(f"  Issue: {config['issue']}")

    if config.get("note"):
        print(f"  Note: {config['note']}")

    results = []
    working_model = None

    for model in config["models_to_try"]:
        print(f"  Trying model: {model}")
        result = await test_model(provider, model, config["vk"])
        results.append(result)

        if result["success"]:
            print(f"    ✅ SUCCESS with {model}!")
            working_model = model
            break
        else:
            print(f"    ❌ Failed: {result['error'][:100]}")

    return {
        "provider": provider,
        "working_model": working_model,
        "models_tested": len(results),
        "results": results,
    }


async def update_provider_config(fixes: list):
    """Update configuration with working models"""
    config_updates = {}

    for fix in fixes:
        if fix["working_model"]:
            config_updates[fix["provider"]] = {
                "model": fix["working_model"],
                "status": "fixed",
                "timestamp": datetime.now().isoformat(),
            }

    # Save to config file
    config_file = Path("provider_fixes.json")
    with open(config_file, "w") as f:
        json.dump(config_updates, f, indent=2)

    print(f"\n💾 Configuration updates saved to {config_file}")
    return config_updates


async def main():
    print("=" * 60)
    print("🚀 LLM PROVIDER FIX UTILITY")
    print("=" * 60)

    # Fix each provider
    fixes = []
    for provider, config in PROVIDER_FIXES.items():
        fix_result = await fix_provider(provider, config)
        fixes.append(fix_result)

    # Update configuration
    config_updates = await update_provider_config(fixes)

    # Summary
    print("\n" + "=" * 60)
    print("📊 FIX SUMMARY")
    print("=" * 60)

    fixed_count = sum(1 for f in fixes if f["working_model"])
    print(f"\n✅ Fixed: {fixed_count}/{len(fixes)} providers")

    for fix in fixes:
        if fix["working_model"]:
            print(f"  ✅ {fix['provider']}: Now using {fix['working_model']}")
        else:
            print(
                f"  ❌ {fix['provider']}: Still broken (tested {fix['models_tested']} models)"
            )

    # Additional diagnostics
    print("\n🔍 DIAGNOSTICS:")

    # Check if it's a Portkey issue
    print("\n1. Portkey Virtual Key Status:")
    for provider in PROVIDER_FIXES:
        vk = PROVIDER_FIXES[provider]["vk"]
        print(f"   {provider}: {vk} - Check in Portkey dashboard")

    print("\n2. Possible Solutions:")
    print("   - XAI: May need to use OpenRouter gateway instead")
    print("   - Perplexity: Check if API is enabled in Portkey")
    print("   - Gemini: Enable billing or wait for quota reset")

    print("\n3. Alternative Approach:")
    print("   - Use OpenRouter as a unified gateway for problematic providers")
    print("   - Switch to alternative models with similar capabilities")
    print("   - Implement provider-specific adapters")


if __name__ == "__main__":
    asyncio.run(main())
