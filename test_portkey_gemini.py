#!/usr/bin/env python3
"""Test Gemini API via OpenRouter (Portkey/direct removed)."""

import os
import sys
import json
import requests
from pathlib import Path

# Load environment
env_file = Path(__file__).parent / ".env.master"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    os.environ[key] = value

def test_openrouter_gemini():
    """Test Gemini through OpenRouter."""
    print("\n🔄 Testing OpenRouter Gemini...")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://sophia-intel-ai.local",
        "X-Title": "Sophia Intel AI"
    }
    payload = {
        "model": "google/gemini-1.5-flash",
        "messages": [{"role": "user", "content": "Say 'OpenRouter Gemini OK' and nothing else"}],
        "max_tokens": 50
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            text = response.json()['choices'][0]['message']['content']
            print(f"✅ OpenRouter Gemini Response: {text.strip()}")
            return True
        else:
            print(f"❌ OpenRouter Error: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ OpenRouter Exception: {e}")
        return False

def test_litellm_gemini():
    """Test Gemini through LiteLLM (routed via OpenRouter)."""
    print("\n🚀 Testing LiteLLM with Gemini (OpenRouter routing)...")
    master_key = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-2025")
    url = "http://localhost:4000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {master_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gemini-1.5-flash",
        "messages": [{"role": "user", "content": "Say 'LiteLLM Gemini OK' and nothing else"}],
        "max_tokens": 50
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            text = response.json()['choices'][0]['message']['content']
            print(f"✅ LiteLLM Gemini Response: {text.strip()}")
            return True
        else:
            print(f"❌ LiteLLM Gemini Error: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ LiteLLM Gemini Exception: {e}")
        return False

def test_litellm_gemini():
    """Test Gemini through LiteLLM with Portkey fallback."""
    print("\n🚀 Testing LiteLLM with Gemini (Portkey routing)...")
    
    master_key = os.getenv("LITELLM_MASTER_KEY", "sk-litellm-master-2025")
    
    url = "http://localhost:4000/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {master_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gemini-1.5-flash",  # LiteLLM should use Portkey routing
        "messages": [{"role": "user", "content": "Say 'LiteLLM Gemini OK' and nothing else"}],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"✅ LiteLLM Gemini Response: {text.strip()}")
            return True
        else:
            print(f"❌ LiteLLM Gemini Error: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ LiteLLM Gemini Exception: {e}")
        return False

def main():
    """Run all Gemini tests."""
    print("=" * 60)
    print("🔮 GEMINI API ROUTING TEST")
    print("=" * 60)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"  OPENROUTER_API_KEY: {'✅ Set' if os.getenv('OPENROUTER_API_KEY') else '❌ Missing'}")
    results = []
    results.append(("OpenRouter Gemini", test_openrouter_gemini()))
    results.append(("LiteLLM Proxy", test_litellm_gemini()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 ALL GEMINI OPENROUTER TESTS PASSED!")
        print("✨ Gemini is now accessible via OpenRouter and LiteLLM proxy")
    else:
        print("\n⚠️ Some tests failed. Check configuration above.")
        print("\n💡 Troubleshooting:")
        print("   1. Ensure LiteLLM is running: ./sophia start")
        print("   2. Check Portkey virtual key is configured in dashboard")
        print("   3. Verify API keys are correct in .env.master")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
