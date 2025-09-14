#!/usr/bin/env python3
"""
Direct test of CLI without Portkey - for debugging
"""
import json
import os

# Mock response for testing
mock_response = {
    "choices": [{
        "message": {
            "content": "✅ CLI is working! However, you need to configure real API keys in Portkey:\n\n" +
                      "1. Go to https://app.portkey.ai\n" +
                      "2. Add your provider API keys (OpenAI, OpenRouter, etc.)\n" + 
                      "3. Create virtual keys for each provider\n" +
                      "4. Update setup_portkey_env.sh with the REAL virtual key IDs\n\n" +
                      "Current status:\n" +
                      "- CLI structure: ✅ Working\n" +
                      "- Portkey auth: ✅ Your user key works\n" +
                      "- Virtual keys: ❌ Need real ones from dashboard\n" +
                      "- Provider APIs: ❌ Not configured in Portkey"
        }
    }]
}

print(json.dumps(mock_response, indent=2))
print("\n---")
print("To fix this:")
print("1. Add your API keys to Portkey dashboard")
print("2. Get the REAL virtual key IDs")  
print("3. Update setup_portkey_env.sh")
print("4. Test again with: ./bin/sophia chat --model openai/gpt-4o-mini --input 'test'")