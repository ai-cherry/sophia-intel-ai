#!/usr/bin/env python3
"""
Test connectivity for all swarm models
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router
from app.core.portkey_config import portkey_manager


def test_model_connectivity():
    """Test each model that the swarm needs"""

    models_to_test = [
        ("grok-code-fast-1", "AIMLAPI", aimlapi_manager),
        ("glm-4.5-air", "AIMLAPI", aimlapi_manager),
        ("llama-4-scout", "AIMLAPI", aimlapi_manager),
        ("gpt-4o-mini", "Portkey", None),
        ("claude-opus-4.1", "AIMLAPI", aimlapi_manager),
    ]

    simple_message = [
        {
            "role": "user",
            "content": "Say 'Hello from [model name]' where [model name] is your model ID.",
        }
    ]

    results = {}

    for model, provider, manager in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing: {model} via {provider}")
        print(f"{'='*60}")

        start_time = time.time()

        try:
            if provider == "AIMLAPI" and manager:
                # Test AIMLAPI models
                response = manager.chat_completion(
                    model=model, messages=simple_message, temperature=0.1, max_tokens=50
                )

                if response and "choices" in response:
                    content = response["choices"][0]["message"]["content"]
                    elapsed = time.time() - start_time
                    print(f"✅ SUCCESS in {elapsed:.2f}s")
                    print(f"Response: {content[:100]}")
                    results[model] = {
                        "status": "success",
                        "time": elapsed,
                        "response": content[:100],
                    }
                else:
                    print("❌ FAILED: Invalid response format")
                    results[model] = {"status": "failed", "error": "Invalid response"}

            elif provider == "Portkey":
                # Test via enhanced router
                response = enhanced_router.create_completion(
                    messages=simple_message,
                    model=model,
                    provider_type=LLMProviderType.PORTKEY,
                    temperature=0.1,
                    max_tokens=50,
                )

                if hasattr(response, "choices"):
                    content = response.choices[0].message.content
                    elapsed = time.time() - start_time
                    print(f"✅ SUCCESS in {elapsed:.2f}s")
                    print(f"Response: {content[:100]}")
                    results[model] = {
                        "status": "success",
                        "time": elapsed,
                        "response": content[:100],
                    }
                else:
                    print("❌ FAILED: Invalid response format")
                    results[model] = {"status": "failed", "error": "Invalid response"}

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)[:200]
            print(f"❌ FAILED in {elapsed:.2f}s")
            print(f"Error: {error_msg}")
            results[model] = {"status": "failed", "time": elapsed, "error": error_msg}

    # Summary
    print(f"\n{'='*60}")
    print("CONNECTIVITY TEST SUMMARY")
    print(f"{'='*60}")

    working_models = []
    failed_models = []

    for model, result in results.items():
        if result["status"] == "success":
            working_models.append(model)
            print(f"✅ {model}: Working ({result['time']:.2f}s)")
        else:
            failed_models.append(model)
            print(f"❌ {model}: Failed - {result.get('error', 'Unknown')[:50]}")

    print(f"\n📊 Results: {len(working_models)}/{len(models_to_test)} models working")
    print(f"Working models: {', '.join(working_models)}")

    return results


if __name__ == "__main__":
    print("🔌 Testing Swarm Model Connectivity...")
    results = test_model_connectivity()
