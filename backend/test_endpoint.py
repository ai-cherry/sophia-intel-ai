#!/usr/bin/env python3
"""
Test script to verify the enhanced chat endpoint works locally
"""

import asyncio
import json
from enhanced_orchestrator import get_orchestrator

async def test_chat_endpoint():
    """Test the enhanced orchestrator directly"""
    try:
        print("🧪 Testing Enhanced SOPHIA Orchestrator...")
        
        # Get orchestrator instance
        orchestrator = get_orchestrator()
        print("✅ Orchestrator instance created")
        
        # Test message processing
        test_message = "SOPHIA, please perform a complete ecosystem self-assessment"
        session_id = "test_session_123"
        user_context = {
            "user_id": "admin",
            "access_level": "admin",
            "auth_type": "api_key"
        }
        
        print(f"📤 Sending test message: {test_message}")
        
        # Process the message
        response = await orchestrator.process_chat_message(
            message=test_message,
            session_id=session_id,
            user_context=user_context
        )
        
        print("✅ Message processed successfully!")
        print(f"📥 Response: {response['response'][:200]}...")
        print(f"🔧 Metadata: {json.dumps(response['metadata'], indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_chat_endpoint())
    if success:
        print("\n🎉 Enhanced orchestrator is working correctly!")
    else:
        print("\n💥 Enhanced orchestrator has issues that need fixing")

