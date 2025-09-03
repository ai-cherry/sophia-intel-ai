#!/usr/bin/env python3
"""
Test the 6 configured models
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

async def test_model(name, provider, model, api_key_env):
    """Test a single model connection"""
    print(f"\n{'='*50}")
    print(f"Testing {name}")
    print(f"Provider: {provider}")
    print(f"Model: {model}")
    print('-'*50)
    
    api_key = os.getenv(api_key_env)
    if not api_key:
        print(f"❌ No API key found for {api_key_env}")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    try:
        # Test based on provider
        if provider == 'openai':
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Say 'Hello from " + name + "' in 5 words or less"}],
                        "max_tokens": 20
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    data = response.json()
                    reply = data['choices'][0]['message']['content']
                    print(f"✅ Response: {reply}")
                    return True
                else:
                    print(f"❌ Error {response.status_code}: {response.text[:200]}")
                    return False
                    
        elif provider == 'claude':
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Say 'Hello from Claude' in 5 words or less"}],
                        "max_tokens": 20
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    data = response.json()
                    reply = data['content'][0]['text']
                    print(f"✅ Response: {reply}")
                    return True
                else:
                    print(f"❌ Error {response.status_code}: {response.text[:200]}")
                    return False
                    
        elif provider == 'openrouter':
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "HTTP-Referer": "http://localhost:3333",
                        "X-Title": "MCP Test"
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": f"Say 'Hello from {name}' in 5 words or less"}],
                        "max_tokens": 20
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    data = response.json()
                    reply = data['choices'][0]['message']['content']
                    print(f"✅ Response: {reply}")
                    return True
                else:
                    print(f"❌ Error {response.status_code}: {response.text[:200]}")
                    return False
                    
    except Exception as e:
        print(f"❌ Exception: {str(e)[:200]}")
        return False

async def main():
    print("\n" + "="*50)
    print("🧪 Testing 6 Model Configuration")
    print("="*50)
    
    # Test configurations matching the UI
    tests = [
        ("GPT-4o", "openai", "gpt-4o", "OPENAI_API_KEY"),
        ("Qwen 2.5 72B", "openrouter", "qwen/qwen-2.5-72b-instruct", "OPENROUTER_API_KEY"),
        ("DeepSeek Chat", "openrouter", "deepseek/deepseek-chat", "OPENROUTER_API_KEY"),
        ("Grok 2", "openrouter", "x-ai/grok-2-1212", "OPENROUTER_API_KEY"),
        ("Claude 3.5 Sonnet", "claude", "claude-3-5-sonnet-20241022", "ANTHROPIC_API_KEY"),
        ("Llama 3.1 405B", "openrouter", "meta-llama/llama-3.1-405b-instruct", "OPENROUTER_API_KEY")
    ]
    
    results = []
    for name, provider, model, api_key_env in tests:
        success = await test_model(name, provider, model, api_key_env)
        results.append((name, success))
        await asyncio.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Summary")
    print("="*50)
    
    working = []
    failed = []
    
    for name, success in results:
        if success:
            working.append(name)
            print(f"✅ {name}: WORKING")
        else:
            failed.append(name)
            print(f"❌ {name}: FAILED")
    
    print(f"\n✅ Working: {len(working)}/6")
    if working:
        print(f"   Models: {', '.join(working)}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}/6")
        print(f"   Models: {', '.join(failed)}")
        print("\n💡 To fix failed models:")
        print("   1. Check if the API keys are valid")
        print("   2. Verify the model names are correct")
        print("   3. Ensure you have access to these models")
    
    print("\n🚀 Your MCP server at http://localhost:3333 can now use these models!")

if __name__ == "__main__":
    asyncio.run(main()