# Portkey Troubleshooting Guide

## Current Status (September 14, 2025)

### ✅ Working Components
- Portkey API authentication (service key: `nYraiE8dOR9A1gDwaRNpSSXRkXBc`)
- Virtual key format and headers
- CLI integration with Portkey

### ❌ Issue Identified
**Invalid OpenAI API Key in Portkey Dashboard**

The OpenAI API key configured in your Portkey dashboard is invalid or expired:
- Virtual Key: `openai-vk-190a60`
- Associated API Key: `sk-svcac...dtUA` (invalid)

## Fix Instructions

### Step 1: Update OpenAI API Key in Portkey
1. Go to [Portkey Dashboard](https://app.portkey.ai)
2. Navigate to Virtual Keys section
3. Find the virtual key `openai-vk-190a60`
4. Update the associated OpenAI API key with a valid one from [OpenAI Platform](https://platform.openai.com/account/api-keys)

### Step 2: Verify Other Provider Keys
Check all virtual keys are properly configured:

| Provider | Virtual Key | Status | Action Required |
|----------|------------|--------|-----------------|
| OpenAI | openai-vk-190a60 | ❌ Invalid | Update API key |
| Anthropic | anthropic-vk-6c26 | ⚠️ Untested | Verify in dashboard |
| X-AI/Grok | x-ai-vk-4dc29a | ⚠️ Untested | Verify in dashboard |
| Mistral | mistralai-vk-7fa8 | ⚠️ Untested | Verify in dashboard |
| DeepSeek | deepseek-vk-a931 | ⚠️ Untested | Verify in dashboard |
| Google | google-vk-88c2 | ⚠️ Untested | Verify in dashboard |
| OpenRouter | openrouter-vk-f5e3 | ⚠️ Untested | Verify in dashboard |

### Step 3: Test Configuration
After updating the API keys in Portkey dashboard, test with:

```bash
# Source the environment
source setup_portkey_env.sh

# Test OpenAI
./bin/sophia chat --model openai/gpt-4o-mini --input "Hello"

# Test plan command
./bin/sophia plan --model openai/gpt-4o-mini --task "Add a simple endpoint"

# Test other providers
./bin/sophia chat --model anthropic/claude-3-opus --input "Hello"
./bin/sophia chat --model mistralai/mistral-large --input "Hello"
```

## Common Issues

### 1. 401 Unauthorized
- **Cause**: Invalid Portkey API key
- **Fix**: Verify `PORTKEY_API_KEY` environment variable

### 2. Invalid API Key Error
- **Cause**: Provider API key in Portkey dashboard is invalid
- **Fix**: Update the provider's API key in Portkey dashboard

### 3. Model Not Found
- **Cause**: Model name mismatch or not available
- **Fix**: Check model aliases in `config/model_aliases.json`

### 4. Virtual Key Not Working
- **Cause**: Virtual key not properly linked to provider API key
- **Fix**: Re-link in Portkey dashboard

## Quick Debug Commands

```bash
# Test Portkey authentication
curl -X GET https://api.portkey.ai/v1/models \
  -H "Authorization: Bearer $PORTKEY_API_KEY"

# Test specific provider
curl -X POST https://api.portkey.ai/v1/chat/completions \
  -H "Authorization: Bearer $PORTKEY_API_KEY" \
  -H "x-portkey-provider: openai" \
  -H "x-portkey-virtual-key: openai-vk-190a60" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "test"}],
    "max_tokens": 10
  }'
```

## Environment Setup Checklist

- [ ] Valid Portkey API key set
- [ ] All virtual keys created in dashboard
- [ ] Provider API keys linked to virtual keys
- [ ] Environment variables sourced
- [ ] Model aliases configured
- [ ] CLI working with at least one provider

## Support Resources

- [Portkey Documentation](https://docs.portkey.ai)
- [Virtual Keys Guide](https://docs.portkey.ai/docs/product/ai-gateway/virtual-keys)
- [Provider Setup](https://docs.portkey.ai/docs/integrations/llms)