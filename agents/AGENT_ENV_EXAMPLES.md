# How AI Agents Access API Keys

## The Rule: ALL agents MUST load from `.env.master`

## Python Agent Example

```python
#!/usr/bin/env python3
"""Example AI agent that uses multiple providers."""

# Method 1: Use the universal loader
from agents.load_env import load_master_env, get_api_key

# Load all environment variables
load_master_env()

# Now use any provider
import openai
import anthropic

# Keys are automatically available
openai_client = openai.OpenAI()  # Uses OPENAI_API_KEY from env
claude_client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY from env

# Or get specific keys
groq_key = get_api_key('groq')
deepseek_key = get_api_key('deepseek')

# Method 2: Direct loading (if not using load_env.py)
import os
from pathlib import Path

env_file = Path.home() / "sophia-intel-ai" / ".env.master"
with open(env_file) as f:
    for line in f:
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.strip().split('=', 1)
            os.environ[key] = value.strip('"')
```

## Bash/Shell Agent Example

```bash
#!/bin/bash
# Shell-based agent script

# Load environment
source ~/sophia-intel-ai/.env.master

# Now all keys are available
echo "Using Claude API: ${ANTHROPIC_API_KEY:0:20}..."
echo "Using GPT API: ${OPENAI_API_KEY:0:20}..."

# Use with curl
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model": "claude-3-opus-20240229", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Node.js/TypeScript Agent Example

```javascript
// agent.js
const dotenv = require('dotenv');
const path = require('path');

// Load from absolute path
dotenv.config({ 
    path: '/Users/lynnmusil/sophia-intel-ai/.env.master' 
});

// Now use the keys
const { OpenAI } = require('openai');
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

// Or with fetch
async function callClaude(prompt) {
    const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: {
            'x-api-key': process.env.ANTHROPIC_API_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        body: JSON.stringify({
            model: 'claude-3-opus-20240229',
            messages: [{role: 'user', content: prompt}]
        })
    });
    return response.json();
}
```

## LangChain Agent Example

```python
from agents.load_env import load_master_env
load_master_env()

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

# All models automatically use keys from environment
gpt4 = ChatOpenAI(model="gpt-4-turbo")
claude = ChatAnthropic(model="claude-3-opus-20240229")
gemini = ChatGoogleGenerativeAI(model="gemini-pro")

# Multi-model chain
response_gpt = gpt4.invoke("Analyze this problem")
response_claude = claude.invoke("Verify this analysis: " + response_gpt.content)
```

## Using LiteLLM Proxy (Recommended)

```python
# No need to load individual keys - LiteLLM handles everything
import requests

def call_any_model(model, prompt):
    """Call any model through LiteLLM proxy."""
    response = requests.post(
        "http://localhost:4000/v1/chat/completions",
        headers={"Authorization": "Bearer sk-litellm-master-2025"},
        json={
            "model": model,  # e.g., "gpt-4", "claude-3-opus", "gemini-1.5-pro"
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    return response.json()

# Use any of the 25+ configured models
result = call_any_model("claude-3-5-sonnet", "Explain quantum computing")
```

## Available Models via LiteLLM
```bash
# Get list of all available models
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-master-2025" \
  | jq -r '.data[].id'

# Includes:
# - gpt-4-turbo, gpt-4, gpt-3.5-turbo
# - claude-3-opus, claude-3-5-sonnet, claude-3-5-haiku
# - gemini-1.5-pro, gemini-1.5-flash
# - groq-llama3-70b, groq-mixtral
# - deepseek-coder, deepseek-chat
# - mistral-large, mistral-medium
# - grok-2, grok-2-vision
# - And more...
```

## Testing Your Agent Has Access

```python
# test_agent_env.py
from agents.load_env import load_master_env, verify_critical_keys

# Load environment
loaded = load_master_env()
print(f"Loaded {loaded} API keys")

# Verify critical keys
if verify_critical_keys():
    print("✅ All critical keys available to agent")
else:
    print("❌ Some keys missing - check .env.master")

# Test specific provider
import os
for provider in ['ANTHROPIC', 'OPENAI', 'GROQ', 'GEMINI']:
    key = os.getenv(f'{provider}_API_KEY')
    if key:
        print(f"✅ {provider}: {key[:20]}...")
    else:
        print(f"❌ {provider}: NOT FOUND")
```

## Important Notes

1. **NEVER hardcode keys** - Always load from `.env.master`
2. **Git protected** - `.env.master` is in `.gitignore`
3. **Single source** - Don't create copies of keys elsewhere
4. **Auto-loaded** - When using `./sophia start`, all services get keys
5. **23 providers** - All major AI providers configured and ready

## Troubleshooting

If agent can't find keys:
```bash
# Check file exists and has correct permissions
ls -la ~/sophia-intel-ai/.env.master
# Should show: -rw------- (600)

# Test loading works
python3 ~/sophia-intel-ai/agents/load_env.py

# For shell scripts, source directly
source ~/sophia-intel-ai/.env.master
echo $ANTHROPIC_API_KEY  # Should show key
```

---
All agents can now access the real API keys locally while keeping them secure from Git.