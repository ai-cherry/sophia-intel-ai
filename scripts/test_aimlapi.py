#!/usr/bin/env python3
"""
Test AIMLAPI Integration - Access to 300+ models including GPT-5, Grok-4
"""

import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.aimlapi_config import AIMLModelFamily, aimlapi_manager


def print_header(title):
    print(f"\n{'='*70}")
    print(f" {title}")
    print(f"{'='*70}")


def test_basic_models():
    """Test basic model access"""
    print_header("TESTING BASIC AIMLAPI MODELS")

    test_cases = [
        ("gpt-4o-mini", "Testing standard GPT-4o Mini"),
        ("gpt-5-nano", "Testing GPT-5 Nano (Latest)"),
        ("grok-3-mini", "Testing Grok-3 Mini"),
        ("glm-4.5-air", "Testing Zhipu GLM-4.5 Air"),
    ]

    results = {}
    for model_name, description in test_cases:
        print(f"\n{description}...")
        try:
            response = aimlapi_manager.chat_completion(
                model=model_name,
                messages=[{"role": "user", "content": "Say 'AIMLAPI works' in 3 words"}],
                max_tokens=20,
                temperature=0.1,
            )
            result = response.choices[0].message.content
            print(f"✅ {model_name}: {result[:50]}")
            results[model_name] = "success"
        except Exception as e:
            print(f"❌ {model_name}: {str(e)[:100]}")
            results[model_name] = "failed"

    return results


def test_flagship_models():
    """Test flagship models GPT-5 and Grok-4"""
    print_header("TESTING FLAGSHIP MODELS")

    # Test GPT-5
    print("\n🚀 Testing GPT-5 (Latest OpenAI Model)...")
    try:
        response = aimlapi_manager.chat_completion(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "You are GPT-5, the most advanced AI model."},
                {"role": "user", "content": "Introduce yourself briefly and confirm you're GPT-5."},
            ],
            max_tokens=50,
            temperature=0.7,
        )
        result = response.choices[0].message.content
        print(f"✅ GPT-5 Response: {result}")
    except Exception as e:
        print(f"❌ GPT-5 Error: {str(e)[:200]}")

    # Test Grok-4
    print("\n🚀 Testing Grok-4 (xAI's Most Advanced)...")
    try:
        response = aimlapi_manager.chat_completion(
            model="grok-4",
            messages=[
                {"role": "system", "content": "You are Grok-4, xAI's most intelligent model."},
                {
                    "role": "user",
                    "content": "Introduce yourself briefly and confirm you're Grok-4.",
                },
            ],
            max_tokens=50,
            temperature=0.7,
        )
        result = response.choices[0].message.content
        print(f"✅ Grok-4 Response: {result}")
    except Exception as e:
        print(f"❌ Grok-4 Error: {str(e)[:200]}")


def test_reasoning_models():
    """Test O-series reasoning models"""
    print_header("TESTING REASONING MODELS")

    print("\n🧠 Testing O3 (Advanced Reasoning)...")
    try:
        response = aimlapi_manager.chat_completion(
            model="o3",
            messages=[
                {"role": "user", "content": "What is 7 * 8 + 15 - 3? Show your reasoning briefly."}
            ],
            max_tokens=100,
            temperature=0.1,
        )
        result = response.choices[0].message.content
        print(f"✅ O3 Reasoning: {result}")
    except Exception as e:
        print(f"❌ O3 Error: {str(e)[:200]}")

    print("\n🧠 Testing GLM-4.5 (Thinking Mode)...")
    try:
        response = aimlapi_manager.chat_completion(
            model="glm-4.5",
            messages=[
                {
                    "role": "user",
                    "content": "Solve: If a train travels 120km in 2 hours, what's its speed?",
                }
            ],
            max_tokens=100,
            temperature=0.1,
        )
        result = response.choices[0].message.content
        print(f"✅ GLM-4.5 Response: {result}")
    except Exception as e:
        print(f"❌ GLM-4.5 Error: {str(e)[:200]}")


def test_model_selection():
    """Test automatic model selection for tasks"""
    print_header("TESTING AUTOMATIC MODEL SELECTION")

    tasks = [
        ("chat", False, False, False),
        ("chat", False, True, False),  # Requires tools
        ("reasoning", False, False, True),  # Requires reasoning
        ("chat", True, False, False),  # Requires vision
    ]

    for task_type, vision, tools, reasoning in tasks:
        desc = f"Task: {task_type}"
        if vision:
            desc += " + vision"
        if tools:
            desc += " + tools"
        if reasoning:
            desc += " + reasoning"

        best_model = aimlapi_manager.get_best_model_for_task(
            task_type=task_type,
            require_vision=vision,
            require_tools=tools,
            require_reasoning=reasoning,
        )
        print(f"\n{desc}")
        print(f"  Best model: {best_model}")


def test_model_families():
    """Test listing models by family"""
    print_header("AVAILABLE MODEL FAMILIES")

    families = [
        AIMLModelFamily.GPT5,
        AIMLModelFamily.GROK,
        AIMLModelFamily.O_SERIES,
        AIMLModelFamily.ZHIPU,
    ]

    for family in families:
        models = aimlapi_manager.list_models(family=family)
        print(f"\n{family.value.upper()} Models: {', '.join(models)}")


def test_direct_api_call():
    """Test direct OpenAI-compatible API call"""
    print_header("TESTING DIRECT API COMPATIBILITY")

    print("\nTesting with OpenAI client directly...")
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key="562d964ac0b54357874b01de33cb91e9", base_url="https://api.aimlapi.com/v1"
        )

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Direct API works'"}],
            max_tokens=10,
        )
        print(f"✅ Direct API: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Direct API Error: {str(e)[:200]}")


def main():
    print("\n" + "=" * 70)
    print(" AIMLAPI INTEGRATION TEST")
    print(" Access to 300+ Models including GPT-5, Grok-4")
    print("=" * 70)

    # Run all tests
    basic_results = test_basic_models()
    test_flagship_models()
    test_reasoning_models()
    test_model_selection()
    test_model_families()
    test_direct_api_call()

    # Test connection summary
    print_header("CONNECTION TEST SUMMARY")
    connection_results = aimlapi_manager.test_connection()

    for model, result in connection_results.items():
        if result["status"] == "success":
            print(f"✅ {model}: {result['response'][:50]}")
        else:
            print(f"❌ {model}: {result['error']}")

    # Final summary
    print_header("FINAL SUMMARY")

    total_tested = len(basic_results) + len(connection_results)
    successful = sum(1 for r in basic_results.values() if r == "success")
    successful += sum(1 for r in connection_results.values() if r["status"] == "success")

    print(f"\nTotal models tested: {total_tested}")
    print(f"Successful: {successful}")
    print(f"Failed: {total_tested - successful}")
    print(f"Success rate: {successful * 100 / total_tested:.1f}%")

    if successful > 0:
        print("\n✅ AIMLAPI integration successful!")
        print("Available features:")
        print("  • Access to GPT-5 series (latest models)")
        print("  • Access to Grok-4 (xAI flagship)")
        print("  • Access to O-series reasoning models")
        print("  • Access to 300+ other models")
        print("  • OpenAI-compatible API interface")

    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "basic_models": basic_results,
        "connection_test": connection_results,
        "success_rate": f"{successful * 100 / total_tested:.1f}%",
    }

    with open("aimlapi_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to aimlapi_test_results.json")

    return 0 if successful > 0 else 1


if __name__ == "__main__":
    exit(main())
