#!/usr/bin/env python3
"""
Debug model responses to see what's happening
"""
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.aimlapi_config import aimlapi_manager
def debug_model_response(model_name):
    """Debug a single model response"""
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")
    messages = [
        {"role": "user", "content": "Say 'Hello, I am working!' and nothing else."}
    ]
    try:
        response = aimlapi_manager.chat_completion(
            model=model_name, messages=messages, temperature=0.1, max_tokens=50
        )
        print(f"Raw response type: {type(response)}")
        print(
            f"Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}"
        )
        if isinstance(response, dict):
            print("\nFull response structure:")
            print(json.dumps(response, indent=2)[:1000])
            if "choices" in response:
                print(f"\nChoices count: {len(response['choices'])}")
                if response["choices"]:
                    choice = response["choices"][0]
                    print(f"First choice keys: {choice.keys()}")
                    if "message" in choice:
                        print(f"Message keys: {choice['message'].keys()}")
                        print(
                            f"Content: {choice['message'].get('content', 'NO CONTENT')}"
                        )
        return response
    except Exception as e:
        print(f"Error: {e}")
        return None
# Test the problematic models
models = [
    "zhipu/glm-4.5-air",
    "meta-llama/llama-4-scout",
    "glm-4.5-air",  # Try without prefix
    "llama-4-scout",  # Try without prefix
]
for model in models:
    debug_model_response(model)
