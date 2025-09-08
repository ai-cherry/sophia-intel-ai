#!/usr/bin/env python3
"""
Test connectivity to each provider for military swarm
"""

import os
import sys

import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.aimlapi_config import aimlapi_manager


def test_providers():
    """Test each provider"""

    print("=" * 60)
    print("TESTING MILITARY SWARM PROVIDERS")
    print("=" * 60)

    # 1. Test AIMLAPI for GLM-4.5-Air
    print("\n1. Testing AIMLAPI (GLM-4.5-Air)...")
    try:
        response = aimlapi_manager.chat_completion(
            model="zhipu/glm-4.5-air",
            messages=[{"role": "user", "content": "Say 'GLM operational'"}],
            temperature=0.1,
            max_tokens=20,
        )
        if hasattr(response, "choices"):
            print(f"✅ AIMLAPI GLM-4.5-Air: {response.choices[0].message.content}")
        else:
            print("✅ AIMLAPI GLM-4.5-Air: Response received")
    except Exception as e:
        print(f"❌ AIMLAPI GLM-4.5-Air failed: {str(e)[:100]}")

    # 2. Test AIMLAPI for Llama-4-Scout
    print("\n2. Testing AIMLAPI (Llama-4-Scout)...")
    try:
        response = aimlapi_manager.chat_completion(
            model="meta-llama/llama-4-scout",
            messages=[{"role": "user", "content": "Say 'Scout operational'"}],
            temperature=0.1,
            max_tokens=20,
        )
        if hasattr(response, "choices"):
            print(f"✅ AIMLAPI Llama-4-Scout: {response.choices[0].message.content}")
        else:
            print("✅ AIMLAPI Llama-4-Scout: Response received")
    except Exception as e:
        print(f"❌ AIMLAPI Llama-4-Scout failed: {str(e)[:100]}")

    # 3. Test OpenRouter availability
    print("\n3. Testing OpenRouter (Grok Code Fast)...")
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "")
    if openrouter_key and not openrouter_key.startswith("sk-or-v1-YOUR"):
        try:
            client = httpx.Client()
            response = client.post(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {openrouter_key}"},
                timeout=10.0,
            )
            if response.status_code == 200:
                models = response.json().get("data", [])
                grok_models = [m for m in models if "grok" in m.get("id", "").lower()]
                if grok_models:
                    print(f"✅ OpenRouter connected. Found {len(grok_models)} Grok models")
                    for model in grok_models[:3]:
                        print(f"   - {model.get('id')}")
                else:
                    print("⚠️ OpenRouter connected but no Grok models found")
            else:
                print(f"❌ OpenRouter error: {response.status_code}")
        except Exception as e:
            print(f"❌ OpenRouter failed: {str(e)[:100]}")
    else:
        print("❌ No valid OpenRouter API key found")

    # 4. Check for Google/Gemini
    print("\n4. Testing Google/Gemini availability...")
    google_key = os.getenv("GOOGLE_API_KEY", "")
    if google_key and not google_key.startswith("AIzaSy_YOUR"):
        print("✅ Google API key found (not tested to avoid quota)")
    else:
        print("❌ No valid Google API key found")
        print("   Fallback: Will use Portkey for Gemini")

    # 5. Check HuggingFace
    print("\n5. Testing HuggingFace availability...")
    hf_key = os.getenv("HUGGINGFACE_API_KEY", "")
    if hf_key:
        print("✅ HuggingFace API key found")
    else:
        print("⚠️ No HuggingFace key, will use AIMLAPI for Llama-4-Scout")

    print("\n" + "=" * 60)
    print("PROVIDER TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_providers()
