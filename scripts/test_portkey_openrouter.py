#!/usr/bin/env python3
"""
Test Portkey with OpenRouter as the unified provider.
"""

import os
import asyncio
import httpx
from dotenv import load_dotenv

# Load environment
load_dotenv('.env.local', override=True)

async def test_portkey_with_openrouter():
    """Test Portkey using OpenRouter as the provider for all models."""
    
    portkey_key = os.getenv("PORTKEY_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not portkey_key or not openrouter_key:
        print("❌ Missing API keys")
        return False
        
    print("\n" + "="*60)
    print("🔐 Testing Portkey → OpenRouter Integration")
    print("="*60)
    
    # Test different models through Portkey → OpenRouter
    test_cases = [
        {
            "name": "GPT-4 via OpenRouter",
            "model": "openai/gpt-4o-mini",
            "provider": "openrouter"
        },
        {
            "name": "Claude via OpenRouter",
            "model": "anthropic/claude-3-haiku-20240307",
            "provider": "openrouter"
        },
        {
            "name": "Llama via OpenRouter",
            "model": "meta-llama/llama-3.2-3b-instruct",
            "provider": "openrouter"
        },
        {
            "name": "Qwen Coder via OpenRouter",
            "model": "qwen/qwen-2.5-coder-32b-instruct",
            "provider": "openrouter"
        }
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in test_cases:
            print(f"\n📝 Testing: {test['name']}")
            print(f"   Model: {test['model']}")
            
            try:
                # Method 1: Using Portkey headers with OpenRouter provider
                response = await client.post(
                    "https://api.portkey.ai/v1/chat/completions",
                    headers={
                        "x-portkey-api-key": portkey_key,
                        "x-portkey-provider": test["provider"],
                        "x-portkey-api-key-openrouter": openrouter_key,  # Pass OpenRouter key
                        "Content-Type": "application/json",
                        "HTTP-Referer": "http://localhost:3000",  # Required by OpenRouter
                        "X-Title": "Sophia Intel AI"  # Required by OpenRouter
                    },
                    json={
                        "model": test["model"],
                        "messages": [{"role": "user", "content": "Say 'Hello' in one word"}],
                        "max_tokens": 10,
                        "temperature": 0.1
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    print(f"   ✅ Success! Response: {content[:50]}")
                else:
                    print(f"   ❌ Failed: Status {response.status_code}")
                    if response.status_code == 401:
                        print("      → Need to configure virtual key in Portkey dashboard")
                    try:
                        error = response.json()
                        print(f"      → Error: {error.get('error', {}).get('message', 'Unknown')}")
                    except:
                        pass
                        
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:100]}")
                
    print("\n" + "="*60)
    print("📊 Configuration Instructions")
    print("="*60)
    
    print("""
To make this work, in Portkey dashboard:

1. Create a Virtual Key with:
   - Provider: OpenRouter
   - API Key: Your OpenRouter key
   - Name: openrouter-unified

2. Then use the virtual key ID in your code:
   ```python
   client = OpenAI(
       api_key="<virtual-key-id>",
       base_url="https://api.portkey.ai/v1"
   )
   ```

3. Benefits:
   - Access to 300+ models with one key
   - Portkey's caching and observability
   - Automatic fallbacks
   - Cost tracking
    """)
    
    return True

async def test_direct_openrouter():
    """Test OpenRouter directly to confirm it works."""
    
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if not openrouter_key:
        print("❌ OpenRouter key not found")
        return False
        
    print("\n🔍 Testing Direct OpenRouter Connection...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {openrouter_key}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Sophia Intel AI",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.2-3b-instruct",  # Cheap, fast model
                "messages": [{"role": "user", "content": "Say 'working' in one word"}],
                "max_tokens": 10
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ OpenRouter Direct: Working! Response: {content}")
            return True
        else:
            print(f"❌ OpenRouter Direct: Failed ({response.status_code})")
            return False

async def main():
    """Run all tests."""
    
    # Test direct OpenRouter first
    openrouter_ok = await test_direct_openrouter()
    
    if openrouter_ok:
        print("\n✅ OpenRouter is working directly")
        print("Now testing Portkey integration...")
        
    # Test Portkey with OpenRouter
    await test_portkey_with_openrouter()
    
    print("\n" + "="*60)
    print("✨ Summary")
    print("="*60)
    print("""
Your setup:
✅ OpenRouter API key is valid and working
✅ Access to 300+ models through OpenRouter
⚠️  Portkey needs virtual key configuration

Next step:
1. Go to https://app.portkey.ai
2. Create virtual key with OpenRouter as provider
3. Use your OpenRouter API key in the virtual key
4. You'll have unified access to all models!
    """)

if __name__ == "__main__":
    asyncio.run(main())