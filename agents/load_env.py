#!/usr/bin/env python3
"""
Universal environment loader for ALL AI agents.
Ensures every agent gets the real API keys from repo-local .env.master
"""

import os
import sys
from pathlib import Path

def _find_repo_env_file(start: Path) -> Path | None:
    """Locate repo-local .env.master by walking up from a starting path.
    No fallbacks to XDG or home directories. Returns None if not found.
    """
    for p in [start, *start.parents]:
        candidate = p / ".env.master"
        if candidate.is_file():
            return candidate
    return None

def load_master_env() -> int:
    """Load environment from repo-local .env.master (single source of truth).
    Returns the count of keys/tokens loaded. Silent on import; no prompts.
    """
    here = Path(__file__).resolve()
    env_file = _find_repo_env_file(here.parent)
    if not env_file:
        # If called directly (__main__), we will print a clear instruction below.
        # When imported, remain silent.
        raise FileNotFoundError(".env.master not found")

    loaded_keys = 0
    with env_file.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                value = value.strip().strip('"').strip("'")
                os.environ[key] = value
                if 'API_KEY' in key or 'TOKEN' in key:
                    loaded_keys += 1
    return loaded_keys

def verify_critical_keys():
    """Verify critical API keys are loaded."""
    critical = {
        'ANTHROPIC_API_KEY': 'Claude API',
        'OPENAI_API_KEY': 'OpenAI GPT',
        'XAI_API_KEY': 'Grok API',
        'GROQ_API_KEY': 'Groq Fast Inference',
        'LITELLM_MASTER_KEY': 'LiteLLM Proxy'
    }
    
    missing = []
    for key, name in critical.items():
        if not os.getenv(key):
            missing.append(f"{name} ({key})")
    
    if missing:
        print("⚠️  Missing critical keys:")
        for m in missing:
            print(f"   - {m}")
        return False
    return True

def get_api_key(provider):
    """Get API key for a specific provider."""
    provider_map = {
        'anthropic': 'ANTHROPIC_API_KEY',
        'claude': 'ANTHROPIC_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'gpt': 'OPENAI_API_KEY',
        'xai': 'XAI_API_KEY',
        'grok': 'GROK_API_KEY',
        # Route Google/Gemini via gateways (no direct Google API)
        'gemini': 'OPENROUTER_API_KEY',
        'google': 'OPENROUTER_API_KEY',
        'groq': 'GROQ_API_KEY',
        'deepseek': 'DEEPSEEK_API_KEY',
        'mistral': 'MISTRAL_API_KEY',
        'perplexity': 'PERPLEXITY_API_KEY',
        'together': 'TOGETHER_API_KEY',
        'openrouter': 'OPENROUTER_API_KEY'
    }
    
    env_key = provider_map.get(provider.lower())
    if env_key:
        return os.getenv(env_key)
    return None

# Auto-load on import (silent; no spam)
if __name__ != "__main__":
    # Attempt silent load; ignore if missing
    try:
        load_master_env()
    except Exception:
        pass

if __name__ == "__main__":
    # Test/verification mode
    try:
        loaded = load_master_env()
        print("✅ Loaded environment from .env.master")
        print(f"✅ Loaded {loaded} API keys/tokens")
    except FileNotFoundError:
        # One clear line, as requested
        repo_root = Path(__file__).resolve().parents[1]
        print(f".env.master not found at {repo_root}/.env.master; cp .env.template .env.master && chmod 600 .env.master")
        sys.exit(1)
    
    if verify_critical_keys():
        print("✅ All critical keys present")
    
    # Show sample keys (truncated for security)
    print("\nSample keys loaded:")
    for key in ['ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GROQ_API_KEY']:
        value = os.getenv(key, 'NOT FOUND')
        if value != 'NOT FOUND':
            print(f"  {key}: {value[:20]}...")
        else:
            print(f"  {key}: ❌ NOT FOUND")
