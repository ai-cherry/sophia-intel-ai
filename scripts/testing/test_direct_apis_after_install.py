#!/usr/bin/env python3
"""
Test Direct API Keys After Installing Libraries
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.unified_keys import unified_keys
def test_together_ai():
    """Test Together AI after install"""
    print("\n[Together AI]")
    try:
        from together import Together
        client = Together(api_key=unified_keys.direct_api_keys["TOGETHER_AI"].key)
        response = client.chat.completions.create(
            model="meta-llama/Llama-3.2-3B-Instruct-Turbo",
            messages=[{"role": "user", "content": "Say 'Together AI works'"}],
            max_tokens=10,
        )
        print(f"✅ Together AI: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Together AI: {str(e)[:100]}")
        return False
def test_groq():
    """Test Groq after install"""
    print("\n[Groq]")
    try:
        from groq import Groq
        client = Groq(api_key=unified_keys.direct_api_keys["GROQ"].key)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Say 'Groq works'"}],
            max_tokens=10,
        )
        print(f"✅ Groq: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Groq: {str(e)[:100]}")
        return False
def test_mistral():
    """Test Mistral after install"""
    print("\n[Mistral]")
    try:
        from mistralai import Mistral
        client = Mistral(api_key=unified_keys.direct_api_keys["MISTRAL"].key)
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": "Say 'Mistral works'"}],
        )
        print(f"✅ Mistral: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Mistral: {str(e)[:100]}")
        return False
def test_gemini_via_openrouter():
    """Test Gemini via OpenRouter (no direct Google)."""
    print("\n[Gemini via OpenRouter]")
    try:
        import requests
        key = os.getenv("OPENROUTER_API_KEY", "")
        if not key:
            print("❌ Missing OPENROUTER_API_KEY")
            return False
        r = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {key}"}, timeout=8
        )
        ok = r.status_code < 400
        print(f"{'✅' if ok else '❌'} OpenRouter models status: {r.status_code}")
        return ok
    except Exception as e:
        print(f"❌ Gemini via OpenRouter: {str(e)[:100]}")
        return False
def main():
    print("=" * 60)
    print(" TESTING DIRECT APIs AFTER LIBRARY INSTALLATION")
    print("=" * 60)
    results = []
    results.append(("Together AI", test_together_ai()))
    results.append(("Groq", test_groq()))
    results.append(("Mistral", test_mistral()))
    results.append(("Gemini via OpenRouter", test_gemini_via_openrouter()))
    print("\n" + "=" * 60)
    print(" RESULTS SUMMARY")
    print("=" * 60)
    working = sum(1 for _, status in results if status)
    total = len(results)
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"{icon} {name}: {'Working' if status else 'Failed'}")
    print(f"\nSuccess Rate: {working}/{total} ({working*100//total}%)")
    if working == total:
        print("\n🎉 ALL DIRECT APIs NOW WORKING!")
    elif working > 0:
        print(f"\n⚠️  {working} APIs working, {total-working} still need fixes")
    else:
        print("\n❌ No APIs working - check configurations")
    return 0 if working == total else 1
if __name__ == "__main__":
    exit(main())
