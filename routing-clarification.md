# Model Routing — One-True Policy

## Current Setup - You Have Multiple Routing Layers!

### 1. Direct API Keys (Environment Variables)
When Opencode sees `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. in environment, it connects DIRECTLY to those providers. No Portkey involved.

### 2. Portkey Virtual Keys
Your Portkey key `nYraiE8dOR9A1gDwaRNpSSXRkXBc` - we need to check what's configured in your Portkey dashboard:
- Does it have multiple providers linked?
- Is it set up for specific providers?
- What fallback rules are configured?

### 3. No local proxies
No alternate local proxies. No local OpenRouter. Portkey-only.

## How Opencode Decides Where to Route

**Currently in your Opencode:**

1. **If you DON'T specify provider:** Uses environment keys directly
   ```
   opencode run "prompt"  # Uses ANTHROPIC_API_KEY directly
   ```

2. **If you specify provider "portkey":** Routes through Portkey
   ```
   opencode run --provider portkey "prompt"  # Goes to Portkey
   ```

3. **Model names in Portkey:** Depends on your virtual key setup in dashboard

## To See What Models Work Through Your Portkey Key

Let's test what your Portkey virtual key actually supports:

```bash
# Test different model formats
curl https://api.portkey.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer nYraiE8dOR9A1gDwaRNpSSXRkXBc" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'

# Try OpenRouter format
curl https://api.portkey.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer nYraiE8dOR9A1gDwaRNpSSXRkXBc" \
  -H "x-portkey-provider": "openrouter" \
  -d '{
    "model": "mistralai/mistral-7b-instruct",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'
```

## The Real Answer - It's Confusing!

Portkey is the only gateway.

1. **No provider specified** → Uses raw API keys from environment
2. **Provider "portkey"** → Sends to Portkey, which decides routing based on:
   - Your virtual key configuration
   - Model name (if it recognizes it)
   - Headers (x-portkey-provider)
   - Fallback rules in your Portkey dashboard

## Recommended Setup for Clarity

### Option 1: Multiple Portkey Virtual Keys (Clearest)
Create separate virtual keys in Portkey dashboard:
- `pk-vk-openrouter-xxx` for OpenRouter
- `pk-vk-together-xxx` for Together
- `pk-vk-huggingface-xxx` for Hugging Face

Then add each to Opencode:
```bash
opencode auth login  # Add portkey-openrouter
opencode auth login  # Add portkey-together
opencode auth login  # Add portkey-huggingface
```

Use with:
```bash
opencode run --provider portkey-openrouter --model "mistralai/mistral-7b-instruct"
opencode run --provider portkey-together --model "meta-llama/Llama-3-70b-chat-hf"
```

### Option 2: Universal Virtual Key with Smart Routing
In Portkey dashboard, set up one virtual key with:
- Multiple providers linked
- Routing rules based on model prefix
- Fallbacks configured

Then let Portkey figure it out:
```bash
opencode run --provider portkey --model "gpt-4"  # Routes to OpenAI
opencode run --provider portkey --model "claude-3-opus"  # Routes to Anthropic
opencode run --provider portkey --model "mistralai/mistral-7b"  # Routes to OpenRouter/Together
```

### Option 3: (Removed)
Local proxy routing is not supported.

## To Check Your Current Portkey Configuration

Go to Portkey dashboard and check:
1. What providers are linked to your virtual key
2. What routing mode is set (loadbalance, fallback, etc.)
3. Any custom routes configured

That will tell us exactly how your models route!
