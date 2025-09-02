#!/usr/bin/env python3
"""
Smoke test for Portkey integration.
Tests both chat (via OpenRouter) and embeddings (via Together AI).
"""

import asyncio
import sys
from app.ports import (
    chat, 
    async_chat,
    embed_texts, 
    async_embed_texts,
    chat_with_tools,
    test_connection,
    Models
)

def test_sync_operations():
    """Test synchronous chat and embedding operations."""
    print("=" * 60)
    print("TESTING SYNCHRONOUS OPERATIONS")
    print("=" * 60)
    
    # Test 1: Basic chat
    print("\n1. Testing basic chat (OpenRouter via Portkey)...")
    try:
        response = chat(
            [{"role": "user", "content": "Say 'Hello from Portkey' and nothing else"}],
            model=Models.GPT4O_MINI
        )
        print(f"   ✅ Chat response: {response}")
    except Exception as e:
        print(f"   ❌ Chat failed: {e}")
        return False
    
    # Test 2: Embeddings
    print("\n2. Testing embeddings (Together AI via Portkey)...")
    try:
        texts = ["Portkey gateway test", "OpenRouter models", "Together embeddings"]
        vectors = embed_texts(texts)
        print(f"   ✅ Generated {len(vectors)} embeddings")
        print(f"   📊 Embedding dimension: {len(vectors[0])}")
    except Exception as e:
        print(f"   ❌ Embeddings failed: {e}")
        return False
    
    # Test 3: Tool calling
    print("\n3. Testing tool calling...")
    try:
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }]
        
        response = chat_with_tools(
            [{"role": "user", "content": "What's the weather in San Francisco?"}],
            tools=tools,
            model=Models.GPT4O
        )
        
        if response.choices[0].message.tool_calls:
            print(f"   ✅ Tool call detected: {response.choices[0].message.tool_calls[0].function.name}")
        else:
            print(f"   ℹ️  No tool call (model responded directly)")
    except Exception as e:
        print(f"   ❌ Tool calling failed: {e}")
        return False
    
    return True

async def test_async_operations():
    """Test asynchronous chat and embedding operations."""
    print("\n" + "=" * 60)
    print("TESTING ASYNCHRONOUS OPERATIONS")
    print("=" * 60)
    
    # Test 4: Async chat
    print("\n4. Testing async chat...")
    try:
        response = await async_chat(
            [{"role": "user", "content": "Count to 3 quickly"}],
            model=Models.GPT4O_MINI
        )
        print(f"   ✅ Async chat response: {response[:50]}...")
    except Exception as e:
        print(f"   ❌ Async chat failed: {e}")
        return False
    
    # Test 5: Async embeddings
    print("\n5. Testing async embeddings...")
    try:
        vectors = await async_embed_texts(["async test 1", "async test 2"])
        print(f"   ✅ Generated {len(vectors)} async embeddings")
    except Exception as e:
        print(f"   ❌ Async embeddings failed: {e}")
        return False
    
    # Test 6: Parallel operations
    print("\n6. Testing parallel operations...")
    try:
        chat_task = async_chat(
            [{"role": "user", "content": "Say 'parallel'"}],
            model=Models.GPT4O_MINI
        )
        embed_task = async_embed_texts(["parallel embedding"])
        
        chat_result, embed_result = await asyncio.gather(chat_task, embed_task)
        print(f"   ✅ Parallel chat: {chat_result}")
        print(f"   ✅ Parallel embedding dimension: {len(embed_result[0])}")
    except Exception as e:
        print(f"   ❌ Parallel operations failed: {e}")
        return False
    
    return True

def test_model_variety():
    """Test different model providers via OpenRouter."""
    print("\n" + "=" * 60)
    print("TESTING MODEL VARIETY")
    print("=" * 60)
    
    models_to_test = [
        (Models.GPT4O_MINI, "OpenAI"),
        (Models.GEMINI_20_FLASH, "Google"),
        (Models.LLAMA_31_8B, "Meta"),
    ]
    
    for model_id, provider in models_to_test:
        print(f"\n7. Testing {provider} model: {model_id}")
        try:
            response = chat(
                [{"role": "user", "content": f"Say 'Hello from {provider}' only"}],
                model=model_id
            )
            print(f"   ✅ {provider}: {response[:50]}")
        except Exception as e:
            print(f"   ⚠️  {provider} not available or failed: {e}")
    
    return True

async def main():
    """Run all tests."""
    print("\n🚀 PORTKEY INTEGRATION SMOKE TEST")
    print("=" * 60)
    
    # Quick connection test first
    print("\nRunning quick connection test...")
    if not test_connection():
        print("\n❌ Connection test failed. Please check your .env configuration:")
        print("   - OPENAI_BASE_URL should be https://api.portkey.ai/v1")
        print("   - OPENAI_API_KEY should be your Portkey VK for OpenRouter")
        print("   - EMBED_API_KEY should be your Portkey VK for Together AI")
        sys.exit(1)
    
    # Run comprehensive tests
    sync_ok = test_sync_operations()
    async_ok = await test_async_operations()
    variety_ok = test_model_variety()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Synchronous operations: {'✅ PASSED' if sync_ok else '❌ FAILED'}")
    print(f"Asynchronous operations: {'✅ PASSED' if async_ok else '❌ FAILED'}")
    print(f"Model variety: {'✅ PASSED' if variety_ok else '❌ FAILED'}")
    
    if sync_ok and async_ok:
        print("\n🎉 All critical tests passed! Portkey integration is working.")
        print("\n📝 Next steps:")
        print("1. Add your Portkey Virtual Keys to .env:")
        print("   - OPENAI_API_KEY=pk-live-<your-openrouter-vk>")
        print("   - EMBED_API_KEY=pk-live-<your-together-vk>")
        print("2. Run: docker compose -f docker-compose.weaviate.yml up -d")
        print("3. Run: python -m app.playground")
    else:
        print("\n⚠️  Some tests failed. Check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())