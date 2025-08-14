#!/usr/bin/env python3
"""
Test OpenRouter migration and optimization
"""
import asyncio
import os
import sys
sys.path.append('.')

from services.openrouter_client import OpenRouterClient, quick_chat, get_available_models

async def test_openrouter_migration():
    """Test the OpenRouter migration"""
    print("🧪 Testing OpenRouter Migration...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    try:
        # Test model listing
        print("\n📋 Testing model listing...")
        models = await get_available_models()
        print(f"✅ Found {len(models)} available models")
        
        # Test quick chat
        print("\n💬 Testing quick chat...")
        response = await quick_chat("Say 'Hello from Sophia AI!' in exactly those words.")
        print(f"✅ Quick chat response: {response[:100]}...")
        
        # Test full client
        print("\n🔧 Testing full client features...")
        async with OpenRouterClient() as client:
            # Test model recommendations
            recommendations = client.get_recommended_models()
            print(f"✅ Model recommendations: {len(recommendations)} categories")
            
            # Test cost estimation
            messages = [{"role": "user", "content": "Hello!"}]
            cost = await client.estimate_cost(messages, "anthropic/claude-3.5-sonnet")
            print(f"✅ Cost estimation: ${cost['estimated_cost']:.6f}")
            
            # Test chat completion
            response = await client.chat_completion(messages)
            print(f"✅ Chat completion successful")
        
        print("\n🎉 All tests passed! OpenRouter migration successful!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_openrouter_migration())
    sys.exit(0 if success else 1)
