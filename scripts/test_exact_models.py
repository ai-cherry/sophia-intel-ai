#!/usr/bin/env python3
"""
Test the EXACT models requested
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

from app.core.aimlapi_config import aimlapi_manager
from app.core.enhanced_llm_router import LLMProviderType, enhanced_router


def test_model(model_name, provider="AIMLAPI"):
    """Test a specific model"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")

    messages = [
        {
            "role": "user",
            "content": "Respond with 'I am [model name] and I am working!' where [model name] is your identity.",
        }
    ]

    # Try different model name formats
    variants = [
        model_name,
        f"x-ai/{model_name}",  # For Grok models
        f"google/{model_name}",  # For Gemini
        f"meta-llama/{model_name}",  # For Llama
        model_name.replace("-", "_"),
        model_name.replace(".", "-"),
        model_name.replace("2.5", "2-5"),
    ]

    for variant in variants:
        print(f"Trying variant: {variant}")
        try:
            if provider == "AIMLAPI":
                response = aimlapi_manager.chat_completion(
                    model=variant, messages=messages, temperature=0.1, max_tokens=100
                )
            else:
                response = enhanced_router.create_completion(
                    messages=messages,
                    model=variant,
                    provider_type=LLMProviderType.PORTKEY,
                    temperature=0.1,
                    max_tokens=100,
                )

            # Extract content
            if hasattr(response, "choices"):
                content = response.choices[0].message.content
            elif isinstance(response, dict) and "choices" in response:
                content = response["choices"][0]["message"]["content"]
            else:
                content = str(response)

            print(f"✅ SUCCESS with variant: {variant}")
            print(f"Response: {content}")
            return variant, content

        except Exception as e:
            error_str = str(e)
            if "400" in error_str:
                # Extract available models from error
                if "Expected" in error_str:
                    # Look for our model in the error
                    if "grok" in model_name.lower() and "grok" in error_str.lower():
                        import re

                        grok_models = re.findall(r"'([^']*grok[^']*)'", error_str)
                        if grok_models:
                            print(f"Found Grok models in error: {grok_models[:3]}")
                    elif "gemini" in model_name.lower() and "gemini" in error_str.lower():
                        import re

                        gemini_models = re.findall(r"'([^']*gemini[^']*)'", error_str)
                        if gemini_models:
                            print(f"Found Gemini models in error: {gemini_models[:3]}")
                    elif "llama" in model_name.lower() and "llama" in error_str.lower():
                        import re

                        llama_models = re.findall(r"'([^']*llama[^']*)'", error_str)
                        if llama_models:
                            print(f"Found Llama models in error: {llama_models[:3]}")
            print(f"❌ Failed: {error_str[:100]}")

    return None, None


# Test the EXACT models you requested
print("=" * 60)
print("TESTING YOUR REQUESTED MODELS")
print("=" * 60)

models_to_test = [
    ("grok-code-fast-1", "AIMLAPI"),
    ("gemini-2.5-flash", "AIMLAPI"),
    ("llama-4-scout", "AIMLAPI"),
]

working_models = {}

for model, provider in models_to_test:
    variant, response = test_model(model, provider)
    if variant:
        working_models[model] = variant

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)

if working_models:
    print("\n✅ WORKING MODEL NAMES:")
    for original, working in working_models.items():
        print(f"  {original} → {working}")
else:
    print("\n❌ None of the requested models worked with any variant tried")
