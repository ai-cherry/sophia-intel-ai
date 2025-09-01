# 🎯 Exact Portkey Virtual Keys to Create

## Login to Portkey
1. Go to https://app.portkey.ai
2. Navigate to **Virtual Keys** section
3. Click **"+ Create Virtual Key"** for each one below

## Create These 7 Virtual Keys (ALL with OpenRouter)

### Virtual Key 1: `openrouter-main`
- **Name**: `openrouter-main`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Description**: Main OpenRouter access
- **Purpose**: General purpose, auto-routing

---

### Virtual Key 2: `gpt-models`
- **Name**: `gpt-models`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Default Model**: `openai/gpt-4o`
- **Description**: GPT-4 and GPT-3.5 models
- **Purpose**: For when you specifically want GPT models

---

### Virtual Key 3: `claude-models`
- **Name**: `claude-models`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Default Model**: `anthropic/claude-3.5-sonnet`
- **Description**: Claude models (Sonnet, Opus, Haiku)
- **Purpose**: For planning, analysis, complex reasoning

---

### Virtual Key 4: `qwen-coder`
- **Name**: `qwen-coder`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Default Model**: `qwen/qwen-2.5-coder-32b-instruct`
- **Description**: Qwen 2.5 Coder (best for coding)
- **Purpose**: Primary code generation

---

### Virtual Key 5: `deepseek-coder`
- **Name**: `deepseek-coder`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Default Model**: `deepseek/deepseek-coder-v2`
- **Description**: DeepSeek Coder v2
- **Purpose**: Alternative code generation approach

---

### Virtual Key 6: `fast-inference`
- **Name**: `fast-inference`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Default Model**: `meta-llama/llama-3.2-3b-instruct`
- **Description**: Fast, cheap models for quick tasks
- **Purpose**: Quick responses, low cost

---

### Virtual Key 7: `groq-speed`
- **Name**: `groq-speed`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Default Model**: `groq/llama-3.1-70b-versatile`
- **Description**: Groq for ultra-fast inference
- **Purpose**: When speed is critical

---

## After Creating Virtual Keys

Each virtual key will give you a **Virtual Key ID** that looks like:
```
vk_xxxxxxxxxxxxxxxxxxxxxx
```

Save these IDs! You'll use them in your code.

## Update Your .env.local

Add these lines to your `.env.local` file with the actual virtual key IDs:

```bash
# Portkey Virtual Key IDs (get these after creating in dashboard)
PORTKEY_VK_MAIN=vk_xxxxxxxxxxxxx          # openrouter-main
PORTKEY_VK_GPT=vk_xxxxxxxxxxxxx           # gpt-models
PORTKEY_VK_CLAUDE=vk_xxxxxxxxxxxxx        # claude-models
PORTKEY_VK_QWEN=vk_xxxxxxxxxxxxx          # qwen-coder
PORTKEY_VK_DEEPSEEK=vk_xxxxxxxxxxxxx      # deepseek-coder
PORTKEY_VK_FAST=vk_xxxxxxxxxxxxx          # fast-inference
PORTKEY_VK_GROQ=vk_xxxxxxxxxxxxx          # groq-speed
```

## How to Use in Code

### Option 1: Direct with Virtual Key ID
```python
from openai import OpenAI

# Use the virtual key ID as the API key
client = OpenAI(
    api_key="vk_xxxxxxxxxxxxx",  # Your virtual key ID
    base_url="https://api.portkey.ai/v1"
)

response = client.chat.completions.create(
    model="openai/gpt-4o",  # OpenRouter model format
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Option 2: With Portkey Headers
```python
import httpx

response = await client.post(
    "https://api.portkey.ai/v1/chat/completions",
    headers={
        "x-portkey-api-key": "hPxFZGd8AN269n4bznDf2/Onbi8I",  # Your Portkey API key
        "x-portkey-virtual-key": "vk_xxxxxxxxxxxxx",  # Virtual key ID
        "Content-Type": "application/json"
    },
    json={
        "model": "openai/gpt-4o",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
```

## Summary

**Create exactly 7 virtual keys**, all with:
- **Same Provider**: OpenRouter
- **Same API Key**: Your OpenRouter key
- **Different Names**: As listed above
- **Different Default Models**: For different use cases

This gives you organized access to all 300+ models through Portkey's gateway!

## Testing After Setup

Once you've created the virtual keys and added the IDs to `.env.local`, test with:

```bash
python3 scripts/test_portkey_virtual_keys.py
```

(I'll create this test script for you next)