# 🔮 Gemini API with Portkey Routing Setup

## Current Status

The Gemini API configuration has been updated to support Portkey routing, but requires additional setup in the Portkey dashboard.

## Configuration in `.env.master`

```bash
# Direct Gemini API key (fallback)
GEMINI_API_KEY_DIRECT="AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"

# Portkey Virtual Key for Gemini
GEMINI_API_KEY="gemini-vk-7c8d93"
PORTKEY_VK_GEMINI="gemini-vk-7c8d93"
```

## ⚠️ Important Notes

### 1. **Gemini Direct API Quota Issue**
The direct Gemini API key shows a 429 quota error. This could mean:
- Free tier quota exhausted
- Need to enable billing in Google Cloud Console
- Rate limiting due to too many requests

**Fix**: Visit https://console.cloud.google.com/apis/dashboard and check your Gemini API quotas

### 2. **Portkey Virtual Key Not Configured**
The virtual key `gemini-vk-7c8d93` needs to be created in your Portkey dashboard.

**To Configure Portkey for Gemini:**

1. Log into Portkey Dashboard: https://app.portkey.ai/
2. Go to Virtual Keys section
3. Create a new Virtual Key:
   - Name: `gemini-vk-7c8d93`
   - Provider: Google (Gemini)
   - API Key: Your Gemini API key
   - Model: gemini-1.5-flash (or your preferred model)
4. Save the configuration

### 3. **Temporary Workaround**

Until Portkey is configured, use the direct API key:

```bash
# In .env.master, temporarily use direct key
GEMINI_API_KEY="AIzaSyA0rewcfUHo87WMEz4a8Og1eAWTslxlgEE"
```

## Testing Gemini Configuration

```bash
# Test script available
python3 test_portkey_gemini.py

# Quick test via curl (direct API)
curl -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"contents": [{"parts": [{"text": "Hello"}]}]}'
```

## Benefits of Portkey Routing

When properly configured, Portkey provides:
- **Automatic fallback** to other models if Gemini fails
- **Load balancing** across multiple API keys
- **Unified logging** and monitoring
- **Cost tracking** across all providers
- **Rate limit management**

## All Configured Portkey Virtual Keys

```bash
anthropic-vk-b42804    # Claude models
deepseek-vk-24102f     # DeepSeek Coder
groq-vk-6b9b52         # Groq (fast inference)
openai-vk-190a60       # GPT models
perplexity-vk-56c172   # Perplexity (web search)
together-ai-670469     # Together AI (open models)
vkj-openrouter-cc4151  # OpenRouter (100+ models)
xai-vk-e65d0f          # xAI Grok
github-vk-a5b609       # GitHub Models
stability-vk-a575fb    # Stability AI (images)
gemini-vk-7c8d93       # Google Gemini (needs dashboard setup)
```

## Next Steps

1. **Fix Gemini Quota**: Check Google Cloud Console for billing/quota
2. **Configure Portkey**: Add virtual key in Portkey dashboard
3. **Update LiteLLM**: Add Gemini to `litellm-complete.yaml` if needed
4. **Test Again**: Run `python3 test_portkey_gemini.py`

## Alternative: Use Different Provider

If Gemini continues to have issues, these alternatives work immediately:

```python
# Claude (Anthropic) - Most capable
model = "claude-3-5-sonnet"

# GPT-4 (OpenAI) - Highly capable
model = "gpt-4-turbo"

# Groq - Ultra fast, free tier
model = "groq/llama-3.1-70b-versatile"

# DeepSeek - Great for code
model = "deepseek-chat"
```

---

**Status**: Configuration complete, awaiting Portkey dashboard setup
**Last Updated**: 2025-09-13