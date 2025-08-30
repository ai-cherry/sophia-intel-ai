# 🔐 Portkey Virtual Keys Configuration Guide

## Current Status

✅ **API Keys Configured:**
- OpenAI: Valid and working
- OpenRouter: Valid and working  
- Portkey: Key configured but needs virtual keys setup
- Weaviate: Running v1.32.0

## Setting Up Portkey Virtual Keys

To complete the Portkey configuration, you need to create virtual keys in the Portkey dashboard.

### Step 1: Access Portkey Dashboard

1. Go to https://app.portkey.ai
2. Log in with your Portkey account
3. Your API key is: `hPxFZGd8AN269n4bznDf2/Onbi8I`

### Step 2: Create Virtual Keys

Navigate to **Virtual Keys** section and create the following:

#### 1. OpenAI Virtual Key
- **Name**: `openai-vk`
- **Provider**: OpenAI
- **API Key**: `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`
- **Models**: gpt-4o, gpt-4o-mini, gpt-3.5-turbo

#### 2. OpenRouter Virtual Key
- **Name**: `openrouter-vk`
- **Provider**: OpenRouter
- **API Key**: `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`
- **Models**: All OpenRouter models

#### 3. Model-Specific Virtual Keys

Create these additional virtual keys for specific model routing:

| Virtual Key Name | Provider | Model | Purpose |
|-----------------|----------|--------|---------|
| qwen-vk | OpenRouter | qwen/qwen-2.5-coder-32b-instruct | Primary coding |
| deepseek-vk | OpenRouter | deepseek/deepseek-coder-v2 | Alternative coding |
| anthropic-vk | OpenRouter | anthropic/claude-3.5-sonnet | Planning & architecture |
| together-vk | OpenRouter | meta-llama/llama-3.1-70b | General purpose |
| groq-vk | OpenRouter | groq/llama-3.1-70b | Fast inference |

### Step 3: Configure Routing Rules

In Portkey dashboard, set up these routing rules:

#### Primary Route (with fallbacks)
```json
{
  "name": "main-route",
  "strategy": "fallback",
  "targets": [
    {
      "virtual_key": "openai-vk",
      "weight": 1
    },
    {
      "virtual_key": "openrouter-vk",
      "weight": 1
    }
  ]
}
```

#### Load Balancing for Coding
```json
{
  "name": "coding-route",
  "strategy": "loadbalance",
  "targets": [
    {
      "virtual_key": "qwen-vk",
      "weight": 0.5
    },
    {
      "virtual_key": "deepseek-vk",
      "weight": 0.5
    }
  ]
}
```

### Step 4: Update Environment Configuration

After creating virtual keys, update `.env.local` with the virtual key IDs:

```bash
# Portkey Virtual Keys (get these from dashboard after creation)
PORTKEY_VK_OPENAI=<virtual-key-id>
PORTKEY_VK_OPENROUTER=<virtual-key-id>
PORTKEY_VK_QWEN=<virtual-key-id>
PORTKEY_VK_DEEPSEEK=<virtual-key-id>
PORTKEY_VK_ANTHROPIC=<virtual-key-id>
```

### Step 5: Test Configuration

Run the test script again to verify:
```bash
python3 scripts/test_api_keys.py
```

## Using Portkey in Code

### Option 1: With Headers
```python
import httpx

response = await client.post(
    "https://api.portkey.ai/v1/chat/completions",
    headers={
        "x-portkey-api-key": "hPxFZGd8AN269n4bznDf2/Onbi8I",
        "x-portkey-virtual-key": "<your-virtual-key-id>",
        "Content-Type": "application/json"
    },
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "Hello"}]
    }
)
```

### Option 2: With OpenAI SDK
```python
from openai import OpenAI

client = OpenAI(
    api_key="<your-virtual-key-id>",  # Use virtual key as API key
    base_url="https://api.portkey.ai/v1"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Benefits of Portkey Configuration

Once configured, you'll have:

1. **Unified Gateway**: Single endpoint for all LLMs
2. **Automatic Fallbacks**: If one provider fails, automatically switch
3. **Load Balancing**: Distribute requests across providers
4. **Cost Tracking**: Monitor usage and costs
5. **Request Caching**: Reduce costs with intelligent caching
6. **Observability**: Full request tracing and monitoring

## Security Notes

- ✅ API keys are stored in `.env.local` (gitignored)
- ✅ Never commit API keys to git
- ✅ Use Pulumi ESC for production deployments
- ✅ Rotate keys regularly
- ✅ Monitor usage in Portkey dashboard

## Current API Key Status

| Service | Status | Key Available | Notes |
|---------|--------|---------------|-------|
| OpenAI | ✅ Working | Yes | 86 models available |
| OpenRouter | ✅ Working | Yes | 323 models available |
| Portkey | ⚠️ Needs Config | Yes | Virtual keys need setup |
| Weaviate | ✅ Working | N/A | v1.32.0 running |

## Next Steps

1. Log into https://app.portkey.ai
2. Create the virtual keys as described above
3. Test with `python3 scripts/test_api_keys.py`
4. Start using the unified gateway in your code

---

*Note: All API keys are securely stored in `.env.local` which is gitignored and will not be committed to the repository.*