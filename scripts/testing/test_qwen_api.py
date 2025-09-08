#!/usr/bin/env python3
"""
Test Qwen API Key
Qwen is Alibaba's LLM service
"""

import json
import os
import sys

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the Qwen API key
QWEN_API_KEY = "qwen-api-key-ad6c81"

print("=" * 60)
print(" TESTING QWEN API KEY")
print("=" * 60)


def test_qwen_dashscope():
    """Test Qwen using DashScope SDK (Alibaba's official SDK)"""
    print("\n[Method 1: DashScope SDK]")
    try:
        # Try to import dashscope
        import dashscope
        from dashscope import Generation

        dashscope.api_key = QWEN_API_KEY

        response = Generation.call(
            model="qwen-turbo", prompt='Say "Qwen is working"', max_tokens=10
        )

        if response.status_code == 200:
            print(f"✅ Qwen via DashScope: {response.output.text}")
            return True
        else:
            print(f"❌ Qwen via DashScope: Status {response.status_code} - {response.message}")
            return False

    except ImportError:
        print("❌ DashScope SDK not installed. Run: pip install dashscope")
        return False
    except Exception as e:
        print(f"❌ Qwen via DashScope failed: {str(e)[:200]}")
        return False


def test_qwen_http():
    """Test Qwen using direct HTTP API"""
    print("\n[Method 2: Direct HTTP API]")

    # Try different possible endpoints
    endpoints = [
        "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
        "https://api.qwen.ai/v1/chat/completions",
        "https://qwen-api.alibaba.com/v1/completions",
    ]

    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint[:50]}...")
        try:
            headers = {
                "Authorization": f"Bearer {QWEN_API_KEY}",
                "Content-Type": "application/json",
            }

            # Try OpenAI-compatible format first
            data = {
                "model": "qwen-turbo",
                "messages": [{"role": "user", "content": "Say 'Qwen works'"}],
                "max_tokens": 10,
            }

            response = requests.post(endpoint, headers=headers, json=data, timeout=10)

            print(f"  Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Qwen works via {endpoint[:30]}...")
                print(f"  Response: {json.dumps(result, indent=2)[:200]}")
                return True
            elif response.status_code == 401:
                print("❌ Authentication failed - key might be invalid")
            elif response.status_code == 404:
                print("  Endpoint not found")
            else:
                print(f"  Response: {response.text[:200]}")

        except requests.exceptions.ConnectionError:
            print("  Connection failed - endpoint might not exist")
        except requests.exceptions.Timeout:
            print("  Timeout - endpoint too slow")
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")

    return False


def test_qwen_openai_compatible():
    """Test if Qwen works with OpenAI client"""
    print("\n[Method 3: OpenAI-Compatible Client]")
    try:
        from openai import OpenAI

        # Try different base URLs
        base_urls = [
            "https://dashscope.aliyuncs.com/compatible-v1",
            "https://api.qwen.ai/v1",
            "https://qwen-api.alibaba.com/v1",
        ]

        for base_url in base_urls:
            print(f"\nTrying base URL: {base_url[:40]}...")
            try:
                client = OpenAI(api_key=QWEN_API_KEY, base_url=base_url)

                response = client.chat.completions.create(
                    model="qwen-turbo",
                    messages=[{"role": "user", "content": "Say 'Qwen works'"}],
                    max_tokens=10,
                )

                print(f"✅ Qwen works: {response.choices[0].message.content}")
                return True

            except Exception as e:
                error_msg = str(e)[:150]
                if "401" in error_msg or "Unauthorized" in error_msg:
                    print("❌ Authentication failed - key invalid or expired")
                elif "404" in error_msg:
                    print("  Endpoint not found")
                else:
                    print(f"  Error: {error_msg}")

    except ImportError:
        print("❌ OpenAI library not installed")
        return False

    return False


def check_key_format():
    """Analyze the key format"""
    print("\n[Key Format Analysis]")
    print(f"Key: {QWEN_API_KEY}")
    print(f"Length: {len(QWEN_API_KEY)} characters")
    print(
        f"Format: {'Looks like a placeholder' if 'api-key' in QWEN_API_KEY else 'Might be valid'}"
    )

    if QWEN_API_KEY == "qwen-api-key-ad6c81":
        print("\n⚠️  WARNING: This looks like a placeholder key!")
        print("Real Qwen/DashScope keys usually look like: 'sk-' followed by random characters")
        print("To get a real key:")
        print("1. Go to https://dashscope.console.aliyun.com/")
        print("2. Create an account (requires Alibaba Cloud account)")
        print("3. Generate an API key")
        return False
    return True


def main():
    # Check key format first
    key_looks_valid = check_key_format()

    if not key_looks_valid:
        print("\n" + "=" * 60)
        print(" KEY APPEARS TO BE A PLACEHOLDER")
        print("=" * 60)
        print("\n❌ The Qwen key 'qwen-api-key-ad6c81' is likely not a real API key")
        print("It looks like a placeholder that needs to be replaced with an actual key")
        return 1

    # Test the key
    results = []
    results.append(("DashScope SDK", test_qwen_dashscope()))
    results.append(("HTTP API", test_qwen_http()))
    results.append(("OpenAI Compatible", test_qwen_openai_compatible()))

    # Summary
    print("\n" + "=" * 60)
    print(" QWEN API KEY TEST RESULTS")
    print("=" * 60)

    working = any(result for _, result in results)

    if working:
        print("\n✅ QWEN API KEY IS WORKING!")
        for method, result in results:
            if result:
                print(f"  ✓ {method} works")
    else:
        print("\n❌ QWEN API KEY IS NOT WORKING")
        print("\nPossible reasons:")
        print("1. Key is invalid or placeholder")
        print("2. Account not activated")
        print("3. Service only available in certain regions")
        print("4. Need to install dashscope: pip install dashscope")

    return 0 if working else 1


if __name__ == "__main__":
    exit(main())
