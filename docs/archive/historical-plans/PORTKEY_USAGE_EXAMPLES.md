# Portkey Configuration - Usage Examples

## Configuration Summary

- **Chat Models**: Portkey → OpenRouter (300+ models)
- **Embeddings**: Portkey → Together AI
- **Gateway**: All requests go through Portkey

## Code Examples

```python

# === CHAT COMPLETIONS (via Portkey → OpenRouter) ===

from openai import OpenAI
import json

# Method 1: Using Portkey config header
client = httpx.AsyncClient()
config = {
    "provider": "openrouter",
    "api_key": os.getenv("OPENROUTER_API_KEY"),
    "override_params": {
        "headers": {
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Sophia Intel AI"
        }
    }
}

response = await client.post(
    "https://api.portkey.ai/v1/chat/completions",
    headers={
        "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
        "x-portkey-config": json.dumps(config),
        "Content-Type": "application/json"
    },
    json={
        "model": "qwen/qwen-2.5-coder-32b-instruct",  # Any OpenRouter model
        "messages": [{"role": "user", "content": "Hello"}]
    }
)

# === EMBEDDINGS (via Portkey → Together AI) ===

config = {
    "provider": "together",
    "api_key": os.getenv("TOGETHER_API_KEY")
}

response = await client.post(
    "https://api.portkey.ai/v1/embeddings",
    headers={
        "x-portkey-api-key": os.getenv("PORTKEY_API_KEY"),
        "x-portkey-config": json.dumps(config),
        "Content-Type": "application/json"
    },
    json={
        "model": "togethercomputer/m2-bert-80M-8k-retrieval",
        "input": "Your text to embed"
    }
)

# === AVAILABLE MODELS ===

Via OpenRouter (300+ models):
- GPT-4: openai/gpt-4o, openai/gpt-4o-mini
- Claude: anthropic/claude-3.5-sonnet, anthropic/claude-3-opus
- Llama: meta-llama/llama-3.1-405b, meta-llama/llama-3.2-90b-vision
- Qwen: qwen/qwen-2.5-coder-32b-instruct, qwen/qwen-2.5-72b
- DeepSeek: deepseek/deepseek-coder-v2, deepseek/deepseek-reasoner
- Mistral: mistral/mistral-large, mistral/mixtral-8x22b
- Google: google/gemini-pro, google/gemini-1.5-pro

Via Together AI (Embeddings):
- togethercomputer/m2-bert-80M-8k-retrieval (768 dim)
- BAAI/bge-base-en-v1.5 (768 dim)
- BAAI/bge-large-en-v1.5 (1024 dim)
```
