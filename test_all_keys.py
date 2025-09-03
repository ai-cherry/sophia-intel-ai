#!/usr/bin/env python3
"""
Test all API keys and provide service information
"""

import asyncio
import httpx
import json
import os
from datetime import datetime

# Import the key manager
import sys
sys.path.insert(0, 'dev-mcp-unified')
from core.simple_key_manager import KeyProvider

# Recreate the simple key manager logic
class SimpleKeyManager:
    def __init__(self):
        self.keys = {
            KeyProvider.OPENAI: "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",
            KeyProvider.DEEPSEEK: "sk-c8a5f1725d7b4f96b29a3d041848cb74",
            KeyProvider.QWEN: "qwen-api-key-ad6c81",
            KeyProvider.ANTHROPIC: "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",
        }
        # Add additional providers
        self.additional_keys = {
            "LLAMA": "llx-MfsEhU0wHNL7PcRN4YEFM3eWcPQggq7edEr52IdnvkHZPPYj",
            "GROQ": "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",
            "XAI": "xai-4WmKCCbqXhuxL56tfrCxaqs3N84fcLVirQG0NIb0NB6ViDPnnvr3vsYOBwpPKpPMzW5UMuHqf1kv87m3",
            "OPENROUTER": "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",
            "PERPLEXITY": "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",
            "TOGETHER": "tgp_v1_HE_uluFh-fELZDmEP9xKZXuSBT4a8EHd6s9CmSe5WWo"
        }
    
    def get_key(self, provider):
        if provider in self.keys:
            return self.keys[provider]
        # Check additional keys by string name
        provider_str = str(provider).split('.')[-1].upper()
        return self.additional_keys.get(provider_str)

async def test_anthropic(key):
    """Test Anthropic Claude API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_openai(key):
    """Test OpenAI API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_deepseek(key):
    """Test DeepSeek API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_qwen(key):
    """Test Qwen API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "qwen-turbo",
                    "input": {"messages": [{"role": "user", "content": "Hi"}]},
                    "parameters": {"max_tokens": 10}
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_openrouter(key):
    """Test OpenRouter API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "HTTP-Referer": "http://localhost:3333",
                    "X-Title": "MCP Test"
                },
                json={
                    "model": "openai/gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_xai(key):
    """Test X.AI (Grok) API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "grok-beta",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_perplexity(key):
    """Test Perplexity API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "pplx-70b-online",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_together(key):
    """Test Together AI API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.together.xyz/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "meta-llama/Llama-2-7b-chat-hf",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def test_groq(key):
    """Test Groq API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "model": "llama2-70b-4096",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10
                },
                timeout=10
            )
            return response.status_code == 200
    except:
        return False

async def main():
    print("🔑 Testing All API Keys and Service Information")
    print("=" * 60)
    
    # Initialize key manager
    km = SimpleKeyManager()
    
    # Service information
    services = {
        "CLAUDE (Anthropic)": {
            "provider": KeyProvider.ANTHROPIC,
            "test_func": test_anthropic,
            "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "pricing": "$15/1M input, $75/1M output (Opus)",
            "context": "200K tokens",
            "strengths": "Reasoning, refactoring, debugging, architecture",
            "cli_name": "claude"
        },
        "CODEX/GPT-4 (OpenAI)": {
            "provider": KeyProvider.OPENAI,
            "test_func": test_openai,
            "models": ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
            "pricing": "$10/1M input, $30/1M output (GPT-4)",
            "context": "128K tokens (turbo)",
            "strengths": "Code generation, completion, documentation",
            "cli_name": "codex or openai"
        },
        "DEEPSEEK": {
            "provider": KeyProvider.DEEPSEEK,
            "test_func": test_deepseek,
            "models": ["deepseek-coder-v3", "deepseek-chat"],
            "pricing": "$0.14/1M input, $0.28/1M output",
            "context": "16K tokens",
            "strengths": "Code review, security analysis, patterns",
            "cli_name": "deepseek or deep"
        },
        "QWEN (Alibaba)": {
            "provider": KeyProvider.QWEN,
            "test_func": test_qwen,
            "models": ["qwen2.5-coder-32b", "qwen-turbo", "qwen-plus"],
            "pricing": "~$0.20/1M tokens",
            "context": "32K tokens",
            "strengths": "Algorithms, optimization, multi-language",
            "cli_name": "qwen"
        },
        "OPENROUTER": {
            "provider": "OPENROUTER",
            "test_func": test_openrouter,
            "models": ["All models from multiple providers"],
            "pricing": "Varies by model + small markup",
            "context": "Model dependent",
            "strengths": "Model routing, fallback, access to many models",
            "cli_name": "openrouter"
        },
        "X.AI (Grok)": {
            "provider": "XAI",
            "test_func": test_xai,
            "models": ["grok-beta", "grok-2"],
            "pricing": "Beta pricing varies",
            "context": "8K tokens",
            "strengths": "Real-time info, humor, uncensored",
            "cli_name": "xai or grok"
        },
        "PERPLEXITY": {
            "provider": "PERPLEXITY",
            "test_func": test_perplexity,
            "models": ["pplx-70b-online", "pplx-7b-online"],
            "pricing": "$0.25/1K requests",
            "context": "4K tokens",
            "strengths": "Web search, real-time data, citations",
            "cli_name": "perplexity"
        },
        "TOGETHER AI": {
            "provider": "TOGETHER",
            "test_func": test_together,
            "models": ["Llama-2", "CodeLlama", "Mistral", "many others"],
            "pricing": "$0.20-0.90/1M tokens",
            "context": "Model dependent",
            "strengths": "Open models, embeddings, fine-tuning",
            "cli_name": "together"
        },
        "GROQ": {
            "provider": "GROQ",
            "test_func": test_groq,
            "models": ["Llama2-70b", "Mixtral-8x7b"],
            "pricing": "Free tier available",
            "context": "4K-32K tokens",
            "strengths": "Ultra-fast inference, low latency",
            "cli_name": "groq"
        }
    }
    
    print("\n📊 API Key Status and Service Information:\n")
    
    working_services = []
    failed_services = []
    
    for service_name, info in services.items():
        key = km.get_key(info["provider"])
        
        if not key:
            print(f"❌ {service_name}: No API key configured")
            failed_services.append(service_name)
            continue
        
        # Test the key
        is_working = await info["test_func"](key)
        status = "✅" if is_working else "❌"
        
        if is_working:
            working_services.append(service_name)
        else:
            failed_services.append(service_name)
        
        print(f"{status} {service_name}")
        print(f"   Key: {key[:8]}...{key[-4:]}")
        print(f"   CLI: mcp query --llm {info['cli_name']}")
        print(f"   Models: {', '.join(info['models'][:3])}")
        print(f"   Pricing: {info['pricing']}")
        print(f"   Context: {info['context']}")
        print(f"   Best for: {info['strengths']}")
        print()
    
    # Summary
    print("\n📈 SUMMARY")
    print("=" * 60)
    print(f"✅ Working: {len(working_services)}/{len(services)}")
    print(f"   Services: {', '.join([s.split()[0] for s in working_services])}")
    
    if failed_services:
        print(f"\n❌ Failed: {len(failed_services)}")
        print(f"   Services: {', '.join([s.split()[0] for s in failed_services])}")
    
    # MCP Setup Status
    print("\n🔧 MCP SETUP NOTES")
    print("=" * 60)
    
    if "XAI" in [info["provider"] for info in services.values()]:
        if km.get_key("XAI"):
            print("✅ X.AI (Grok) configured - use: mcp query --llm xai")
        else:
            print("⚠️  X.AI not in MCP adapters yet - need to add XAIAdapter")
    
    if "OPENROUTER" in [info["provider"] for info in services.values()]:
        if km.get_key("OPENROUTER"):
            print("✅ OpenRouter configured - can route to any model")
        else:
            print("⚠️  OpenRouter not in MCP adapters yet - need to add OpenRouterAdapter")
    
    print("\n💡 To use in your project:")
    print("   1. Start MCP: ./dev-mcp-unified/mcp start")
    print("   2. Query: mcp query --llm claude 'your question'")
    print("   3. Or use aliases: claude, codex, qwen, deep")

if __name__ == "__main__":
    asyncio.run(main())