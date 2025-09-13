#!/usr/bin/env python3
"""Test Gemini access via OpenRouter (no direct Google API)."""

import os
import sys
import requests
from pathlib import Path

# Load environment
env_file = Path(__file__).parent / ".env.master"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    os.environ[key] = value

def test_gemini():
    """Test Gemini via OpenRouter."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return False
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://sophia-intel-ai.local",
        "X-Title": "Sophia Intel AI"
    }
    data = {
        "model": "google/gemini-1.5-flash",
        "messages": [{"role": "user", "content": "Say 'OpenRouter Gemini OK' and nothing else"}],
        "stream": False
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            text = result['choices'][0]['message']['content']
            print(f"✅ OpenRouter Gemini response: {text.strip()}")
            return True
        else:
            print(f"❌ OpenRouter error {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini()
    sys.exit(0 if success else 1)
