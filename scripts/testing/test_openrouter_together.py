#!/usr/bin/env python3
"""
Test OpenRouter and Together AI Virtual Keys
"""
import json
import os
import time
from datetime import datetime
if not os.environ.get("PORTKEY_API_KEY"):
    raise RuntimeError("PORTKEY_API_KEY is required for this test.")
from portkey_ai import Portkey
# Virtual keys we have
VIRTUAL_KEYS = {
    "openrouter": {
        "vk": "vkj-openrouter-cc4151",
        "models": [
            "openai/gpt-3.5-turbo",
            "anthropic/claude-instant-v1",
            "google/palm-2-chat-bison",
            "meta-llama/llama-2-70b-chat",
            "gryphe/mythomax-l2-13b",
        ],
    },
    "together": {
        "vk": "together-ai-670469",
        "models": [
            "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
            "meta-llama/Llama-3.2-3B-Instruct-Turbo",
            "meta-llama/Llama-2-7b-chat-hf",
            "mistralai/Mistral-7B-Instruct-v0.1",
            "togethercomputer/RedPajama-INCITE-7B-Chat",
        ],
    },
}
def test_provider(provider_name, config):
    """Test a provider with multiple models"""
    print(f"\n{'='*60}")
    print(f"Testing {provider_name.upper()}")
    print(f"Virtual Key: {config['vk']}")
    print(f"{'='*60}")
    results = []
    for model in config["models"]:
        print(f"\n🧪 Testing model: {model}")
        try:
            client = Portkey(
                api_key=os.environ["PORTKEY_API_KEY"], virtual_key=config["vk"]
            )
            start_time = time.time()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Say 'OK' if you're working"}],
                max_tokens=10,
                temperature=0,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            result = {
                "provider": provider_name,
                "model": model,
                "status": "success",
                "response": (
                    response.choices[0].message.content
                    if response.choices
                    else "No response"
                ),
                "latency_ms": latency_ms,
            }
            print(f"  ✅ SUCCESS ({latency_ms}ms): {result['response'][:50]}")
            results.append(result)
        except Exception as e:
            error_msg = str(e)[:200]
            result = {
                "provider": provider_name,
                "model": model,
                "status": "failed",
                "error": error_msg,
            }
            print(f"  ❌ FAILED: {error_msg[:100]}")
            results.append(result)
    return results
def main():
    print("=" * 60)
    print("OPENROUTER & TOGETHER AI VIRTUAL KEY TEST")
    print("=" * 60)
    all_results = {}
    # Test each provider
    for provider_name, config in VIRTUAL_KEYS.items():
        results = test_provider(provider_name, config)
        all_results[provider_name] = results
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    for provider, results in all_results.items():
        working = sum(1 for r in results if r["status"] == "success")
        total = len(results)
        print(f"\n{provider.upper()}:")
        print(f"  Working Models: {working}/{total}")
        if working > 0:
            print("  ✅ Working:")
            for r in results:
                if r["status"] == "success":
                    print(f"    - {r['model']} ({r['latency_ms']}ms)")
        failed = [r for r in results if r["status"] == "failed"]
        if failed:
            print("  ❌ Failed:")
            for r in failed:
                print(f"    - {r['model']}")
    # Save results
    output_file = (
        f"openrouter_together_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")
if __name__ == "__main__":
    main()
