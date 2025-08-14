#!/usr/bin/env python3
"""
Test script to verify AI Router only allows approved models.
This script attempts to use an unapproved model and expects a hard failure.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_servers.ai_router import AIRouter, TaskType, TaskRequest
import asyncio


async def test_unapproved_model():
    """Test that unapproved models are rejected"""
    router = AIRouter()
    
    # Try to use an unapproved model by checking if it's in the registry
    unapproved_models = [
        "claude-3-sonnet",
        "gpt-3.5-turbo", 
        "llama-2-70b",
        "mistral-large",
        "gemini-pro"
    ]
    
    for model in unapproved_models:
        if model in router.models:
            print(f"❌ FAILURE: Unapproved model {model} found in registry")
            return False
        else:
            print(f"✅ SUCCESS: Unapproved model {model} correctly not in registry")
    
    # Test approved models are present
    approved_models = ["gpt-4o", "gpt-4o-mini"]
    
    for model in approved_models:
        if model not in router.models:
            print(f"❌ FAILURE: Approved model {model} missing from registry")
            return False
        else:
            print(f"✅ SUCCESS: Approved model {model} found in registry")
    
    # Test routing with approved model
    try:
        request = TaskRequest(
            prompt="test prompt",
            task_type=TaskType.REASONING
        )
        
        decision = await router.route_request(request)
        
        if decision.selected_model in approved_models:
            print(f"✅ SUCCESS: Router selected approved model {decision.selected_model}")
        else:
            print(f"❌ FAILURE: Router selected unapproved model {decision.selected_model}")
            return False
            
    except Exception as e:
        print(f"❌ FAILURE: Router failed with approved models: {e}")
        return False
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_unapproved_model())
    
    if result:
        print("\n✅ All allowlist tests passed")
        sys.exit(0)
    else:
        print("\n❌ Allowlist tests failed")
        sys.exit(1)

