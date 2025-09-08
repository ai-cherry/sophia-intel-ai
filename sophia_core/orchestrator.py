#!/usr/bin/env python3
"""Simple working orchestrator"""

import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def run_simple_test():
    """Run a simple test that actually works"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "google/gemini-flash-1.5",
        "messages": [{"role": "user", "content": "Say SOPHIA IS WORKING"}],
        "max_tokens": 50
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"Error: {resp.status}"

if __name__ == "__main__":
    result = asyncio.run(run_simple_test())
    print(f"✅ Result: {result}")