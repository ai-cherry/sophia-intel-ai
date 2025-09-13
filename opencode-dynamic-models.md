# Dynamic Model List for Opencode via Portkey

## The Problem
Opencode shows generic models from hardcoded providers (OpenAI, Anthropic, etc.) based on environment API keys. It doesn't know about your Portkey virtual keys that route to OpenRouter, Together AI, Hugging Face, etc.

## Solution 1: Portkey as Custom Provider (Manual)

Add Portkey to Opencode auth with model routing:

```bash
opencode auth login
# Select "Other"
# Name: portkey-openrouter
# API Key: pk-vk-your-key
# Base URL: https://api.portkey.ai/v1
```

Then manually specify models:
```bash
opencode run --model "openrouter/mistralai/mistral-7b-instruct" "prompt"
opencode run --model "together/meta-llama/Llama-3-70b-chat-hf" "prompt"
```

## Solution 2: Dynamic Model Discovery Script

Create a script that queries Portkey/OpenRouter for available models:

```javascript
// fetch-models.js
const PORTKEY_API_KEY = process.env.PORTKEY_API_KEY;
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;

async function fetchOpenRouterModels() {
  const response = await fetch('https://openrouter.ai/api/v1/models', {
    headers: {
      'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
      'HTTP-Referer': 'https://localhost',
      'X-Title': 'Opencode'
    }
  });
  const data = await response.json();
  return data.data.map(m => ({
    id: `openrouter/${m.id}`,
    name: m.name,
    context: m.context_length,
    pricing: m.pricing
  }));
}

async function fetchTogetherModels() {
  const response = await fetch('https://api.together.xyz/models', {
    headers: {
      'Authorization': `Bearer ${TOGETHER_API_KEY}`
    }
  });
  const data = await response.json();
  return data.map(m => ({
    id: `together/${m.name}`,
    name: m.display_name,
    context: m.context_window
  }));
}

// Save to opencode-models.json
const models = [
  ...await fetchOpenRouterModels(),
  ...await fetchTogetherModels()
];

fs.writeFileSync('~/.config/opencode/models.json', JSON.stringify(models));
```

## Solution 3: MCP Model Registry

Use MCP server to maintain model list:

```bash
curl -X POST http://localhost:8081/memory \
  -H "Content-Type: application/json" \
  -d '{
    "key": "available_models",
    "value": {
      "openrouter": [
        "mistralai/mistral-7b-instruct",
        "meta-llama/llama-3-70b-instruct",
        "anthropic/claude-3-opus"
      ],
      "together": [
        "meta-llama/Llama-3-70b-chat-hf",
        "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO"
      ],
      "huggingface": [
        "bigscience/bloom",
        "google/flan-t5-xxl"
      ]
    }
  }'
```

Then query from Opencode:
```bash
curl http://localhost:8081/memory/available_models
```

## Solution 4: Opencode Config Override

Create `~/.config/opencode/providers.json`:

```json
{
  "providers": {
    "portkey-openrouter": {
      "baseURL": "https://api.portkey.ai/v1",
      "headers": {
        "x-portkey-provider": "openrouter",
        "x-portkey-virtual-key": "pk-vk-xxx"
      },
      "models": [
        {
          "id": "mistralai/mistral-7b-instruct",
          "name": "Mistral 7B Instruct",
          "context": 32768
        },
        {
          "id": "meta-llama/llama-3-70b-instruct", 
          "name": "Llama 3 70B",
          "context": 8192
        },
        {
          "id": "anthropic/claude-3-opus",
          "name": "Claude 3 Opus (OpenRouter)",
          "context": 200000
        }
      ]
    },
    "portkey-together": {
      "baseURL": "https://api.portkey.ai/v1",
      "headers": {
        "x-portkey-provider": "together-ai"
      },
      "models": [
        {
          "id": "meta-llama/Llama-3-70b-chat-hf",
          "name": "Llama 3 70B Chat",
          "context": 8192
        }
      ]
    }
  }
}
```

## Best Practice: Hybrid Approach

1. **Set up Portkey virtual keys** for each provider (OpenRouter, Together, HuggingFace)
2. **Create provider configs** in Opencode for each virtual key
3. **Run daily model sync** to update available models
4. **Use MCP memory** to cache model list

### Quick Setup Commands:

```bash
# 1. Add Portkey-OpenRouter to Opencode
opencode auth login
# Other → portkey-openrouter → pk-vk-openrouter-key → https://api.portkey.ai/v1

# 2. Add Portkey-Together
opencode auth login  
# Other → portkey-together → pk-vk-together-key → https://api.portkey.ai/v1

# 3. Add Portkey-HuggingFace
opencode auth login
# Other → portkey-huggingface → pk-vk-huggingface-key → https://api.portkey.ai/v1
```

### Usage:

```bash
# Use specific provider models
opencode run --provider portkey-openrouter --model "mistralai/mistral-7b-instruct" "prompt"
opencode run --provider portkey-together --model "meta-llama/Llama-3-70b-chat-hf" "prompt"

# Or in TUI
/switch portkey-openrouter
/model mistralai/mistral-7b-instruct
```

## The Real Issue

Opencode doesn't have a built-in way to dynamically fetch models from gateways. It expects static provider definitions. The workarounds above let you:

1. Manually specify any model via Portkey routing
2. Maintain your own model list
3. Use multiple Portkey virtual keys for different providers

The models will work through Portkey, you just won't see them in the model list UI unless you manually configure them.