# 🔑 Portkey Virtual Keys Configuration - OpenRouter Strategy

## The Smart Approach: Use OpenRouter for Everything!

Since OpenRouter provides access to 300+ models from all providers (OpenAI, Anthropic, Google, Meta, etc.), you can use it as the single provider for all your virtual keys in Portkey. This gives you:

- ✅ Single API key to manage
- ✅ Access to ALL models
- ✅ Unified billing through OpenRouter
- ✅ No need for separate API keys for each provider

## Step-by-Step Virtual Key Setup in Portkey

### 1. Log into Portkey Dashboard
- Go to https://app.portkey.ai
- Navigate to **Virtual Keys** section

### 2. Create Virtual Keys (All Using OpenRouter)

Create these virtual keys, **ALL with the same configuration**:

**Base Configuration for ALL Virtual Keys:**
- **Provider**: OpenRouter
- **API Key**: `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`
- **Base URL**: `https://openrouter.ai/api/v1`

Now create these specific virtual keys:

#### Virtual Key 1: GPT Models
- **Name**: `gpt-models`
- **Provider**: OpenRouter
- **API Key**: (your OpenRouter key)
- **Default Model**: `openai/gpt-4o`
- **Description**: Access to GPT-4, GPT-4o, GPT-3.5

#### Virtual Key 2: Claude Models
- **Name**: `claude-models`
- **Provider**: OpenRouter
- **API Key**: (your OpenRouter key)
- **Default Model**: `anthropic/claude-3.5-sonnet`
- **Description**: Access to Claude 3.5, Claude 3 Opus, Haiku

#### Virtual Key 3: Coding Models
- **Name**: `coding-models`
- **Provider**: OpenRouter
- **API Key**: (your OpenRouter key)
- **Default Model**: `qwen/qwen-2.5-coder-32b-instruct`
- **Description**: Specialized coding models

#### Virtual Key 4: DeepSeek Models
- **Name**: `deepseek-models`
- **Provider**: OpenRouter
- **API Key**: (your OpenRouter key)
- **Default Model**: `deepseek/deepseek-coder-v2`
- **Description**: DeepSeek coding and reasoning models

#### Virtual Key 5: Fast/Cheap Models
- **Name**: `fast-models`
- **Provider**: OpenRouter
- **API Key**: (your OpenRouter key)
- **Default Model**: `meta-llama/llama-3.2-3b-instruct`
- **Description**: Fast, cost-effective models

#### Virtual Key 6: Large Context Models
- **Name**: `large-context`
- **Provider**: OpenRouter
- **API Key**: (your OpenRouter key)
- **Default Model**: `google/gemini-pro-1.5`
- **Description**: Models with large context windows

### 3. Model Routing Configuration

In Portkey, you can now route to specific models through OpenRouter:

```json
{
  "virtual_keys": {
    "gpt-models": {
      "provider": "openrouter",
      "models": [
        "openai/gpt-4o",
        "openai/gpt-4o-mini",
        "openai/gpt-3.5-turbo"
      ]
    },
    "claude-models": {
      "provider": "openrouter",
      "models": [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-opus",
        "anthropic/claude-3-haiku"
      ]
    },
    "coding-models": {
      "provider": "openrouter",
      "models": [
        "qwen/qwen-2.5-coder-32b-instruct",
        "deepseek/deepseek-coder-v2",
        "codellama/codellama-70b-instruct"
      ]
    }
  }
}
```

### 4. Headers Configuration

When making requests, include these headers:

```python
headers = {
    "x-portkey-api-key": "hPxFZGd8AN269n4bznDf2/Onbi8I",
    "x-portkey-virtual-key": "<your-virtual-key-id>",
    "HTTP-Referer": "http://localhost:3000",  # Required by OpenRouter
    "X-Title": "Sophia Intel AI"  # Required by OpenRouter
}
```

## Example Usage After Setup

### Using GPT-4 through Portkey → OpenRouter:
```python
from openai import OpenAI

client = OpenAI(
    api_key="<gpt-models-virtual-key-id>",  # Your Portkey virtual key
    base_url="https://api.portkey.ai/v1"
)

response = client.chat.completions.create(
    model="openai/gpt-4o",  # OpenRouter model format
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Using Claude through Portkey → OpenRouter:
```python
client = OpenAI(
    api_key="<claude-models-virtual-key-id>",
    base_url="https://api.portkey.ai/v1"
)

response = client.chat.completions.create(
    model="anthropic/claude-3.5-sonnet",  # OpenRouter model format
    messages=[{"role": "user", "content": "Hello"}]
)
```

## Benefits of This Approach

1. **Simplicity**: One API key (OpenRouter) for all models
2. **Cost Efficiency**: OpenRouter often has competitive pricing
3. **Reliability**: If a model is down on one provider, OpenRouter automatically routes to another
4. **No Multi-Provider Management**: Don't need separate keys for OpenAI, Anthropic, etc.
5. **Access to Everything**: 300+ models from dozens of providers

## Available Models via OpenRouter

Through your OpenRouter key, you have access to:

### OpenAI Models
- gpt-4o, gpt-4o-mini
- gpt-4-turbo, gpt-4
- gpt-3.5-turbo

### Anthropic Models  
- claude-3.5-sonnet
- claude-3-opus, claude-3-haiku

### Google Models
- gemini-pro, gemini-pro-vision
- gemini-1.5-pro, gemini-1.5-flash

### Meta Models
- llama-3.1-405b, llama-3.1-70b
- llama-3.2-90b-vision
- codellama-70b

### Specialized Coding Models
- qwen/qwen-2.5-coder-32b
- deepseek/deepseek-coder-v2
- phind/phind-codellama-34b

### And Many More!
- Mistral models
- Cohere models
- Perplexity models
- Together AI models
- 300+ total models

## Summary

**YES, you're absolutely right!** 

In Portkey, you should:
1. Set **OpenRouter** as the provider for ALL virtual keys
2. Use your **OpenRouter API key** for ALL virtual keys
3. Just specify different default models for each virtual key

This way, Portkey becomes a smart router on top of OpenRouter, giving you:
- Portkey's features (caching, fallbacks, observability)
- OpenRouter's access to all models
- Single API key management
- Maximum flexibility

No need for separate OpenAI, Anthropic, or other provider keys - OpenRouter handles it all!