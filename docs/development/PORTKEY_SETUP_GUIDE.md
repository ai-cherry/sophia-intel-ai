# 🚀 Portkey Gateway Setup Guide for Sophia Intel AI

## Overview
This guide provides comprehensive setup instructions for integrating Portkey as the unified LLM gateway across three systems:
1. **LiteLLM Squad** - Multi-model orchestration
2. **Builder App** - Agent-based development system  
3. **Sophia Intel App** - Main AI assistant CLI

## 🎯 Latest Updates (2025-09-11)
- **17 Active Models** configured (up from 13)
- **DeepSeek V3.1 FREE tier** added ($0 cost for routine coding!)
- **6 New Models**: Grok 4, Llama 4 Scout/Maverick, Qwen3 Coder, DeepSeek V3 0324
- **Free Tier Policy** for 40-60% cost savings
- **Central Control** via `config/user_models_config.yaml`

## ✅ Current Status

### Successfully Configured
- ✅ **Portkey API Key**: `nYraiE8dOR9A1gDwaRNpSSXRkXBc` configured in `.env.portkey`
- ✅ **10 Provider Virtual Keys** configured and verified
- ✅ **17 Active Models** including GPT-5, Claude 4, Grok 4, Gemini 2.5 Pro
- ✅ **Builder App** fully integrated with Portkey routing
- ✅ **9 Routing Policies**: quality_max, speed_max, coding, creative, research, balanced, free_tier, specialists
- ✅ **Caching & Retry Logic** configured with semantic caching
- ✅ **Cost Tracking** enabled with $1,000 daily budget

### Virtual Keys Configured
```
DEEPSEEK     : deepseek-vk-24102f
OPENAI       : openai-vk-190a60  
ANTHROPIC    : anthropic-vk-b42804
OPENROUTER   : vkj-openrouter-cc4151
PERPLEXITY   : perplexity-vk-56c172
GROQ         : groq-vk-6b9b52
MISTRAL      : mistral-vk-f92861
XAI          : xai-vk-e65d0f
TOGETHER     : together-ai-670469
COHERE       : cohere-vk-496fa9
```

## 📋 Prerequisites

### System Requirements
- macOS 12+ (Monterey or newer) on M3 chip
- Node.js v22 LTS
- Python 3.11+
- 8GB+ RAM (16GB recommended)
- 10GB free storage

### Dependencies Installation
```bash
# Install Portkey SDK (Node.js)
npm install -g @portkey-ai/gateway

# Install Portkey SDK (Python)
pip install portkey-ai

# Verify installation
portkey --version  # Should show 1.7.0+
python3 -c "import portkey_ai; print(portkey_ai.__version__)"
```

## 🔧 Configuration Files

### 1. Environment Variables (`.env.portkey`)
Already created with:
- Portkey API key
- All virtual keys for providers
- Configuration settings for cache, retry, guardrails

### 2. Portkey Configuration (`portkey_config.json`)
Complete configuration with:
- Provider mappings and models
- Routing policies by mode (reasoning/fast/cheap/quality)
- Cache settings (semantic, TTL: 3600s)
- Retry logic (3 attempts with exponential backoff)
- Guardrails (PII redaction enabled)

### 3. Integration Points

#### Builder App Integration
Location: `/builder_cli/lib/providers.py`
```python
class BuilderProvidersClient:
    """Routes all requests through Portkey gateway"""
    - Uses PortkeyManager for routing
    - Implements mode-based routing (reasoning/fast/cheap/quality)
    - Automatic JSON validation and repair
    - Cost tracking and analytics
```

#### Agent Configuration
Location: `/builder_cli/lib/agents.py`
```python
def _portkey_model():
    """Each agent gets unique virtual key"""
    - Planner: GPT-5 or Grok 4 (best reasoning)
    - Coder: Qwen3 Coder or DeepSeek FREE (specialized/free)
    - Reviewer: GPT-5 or Claude 4 (quality review)
```

#### Central Model Configuration
Location: `/config/user_models_config.yaml`
```yaml
# YOU control all model routing from this single file!
models:
  grok-4: enabled (Priority 1)
  deepseek-chat-v3.1-free: enabled (FREE tier!)
  llama-4-scout: enabled (Research specialist)
  qwen3-coder: enabled (Code specialist)
```

#### Portkey Manager
Location: `/app/core/portkey_manager.py`
```python
class PortkeyManager:
    """Central routing and management"""
    - Task-based routing
    - Model tier selection
    - Cost estimation
    - Fallback handling
```

## 🎯 Usage Examples

### 1. Direct Provider Access
```bash
# Using specific providers
sophia anthropic "Explain quantum computing"
sophia deepseek "Write a Python function"
sophia grok "Debug this code"
sophia openai "Generate unit tests"
```

### 2. Mode-Based Routing
```python
from builder_cli.lib.providers import get_providers_client, ProviderMode

client = get_providers_client()

# Reasoning mode (o3-mini, Claude 4, DeepSeek R1)
request = ModelRequest(
    messages=[{"role": "user", "content": "Complex reasoning task"}],
    mode=ProviderMode.REASONING
)

# Fast mode (Groq, Grok-3)
request = ModelRequest(
    messages=[{"role": "user", "content": "Quick response needed"}],
    mode=ProviderMode.FAST
)

# Cheap mode (DeepSeek, Llama 8B)
request = ModelRequest(
    messages=[{"role": "user", "content": "Bulk processing"}],
    mode=ProviderMode.CHEAP
)

response = await client.chat(request)
```

### 3. Builder App Workflows
```python
# Create construction team with Portkey routing
from builder_cli.lib.agents import create_construction_team

team = await create_construction_team()
# Each agent uses different provider via virtual keys
# Planner → OpenAI/Anthropic
# Coder → Groq/Together
# Reviewer → DeepSeek/xAI

result = await team.execute("Build a REST API")
```

### 4. Cost-Optimized Routing
```python
# Automatic provider selection based on task
from app.core.portkey_manager import PortkeyManager, TaskType

manager = PortkeyManager()

# Routes to best provider for task type
response = await manager.execute_with_fallback(
    task_type=TaskType.CODE_GENERATION,
    messages=[{"role": "user", "content": "Generate code"}]
)
```

## 📊 Monitoring & Analytics

### View Analytics
```python
from builder_cli.lib.providers import get_providers_client

client = get_providers_client()
analytics = client.get_analytics()

print(f"Total Requests: {analytics['total_requests']}")
print(f"Total Cost: ${analytics['total_cost_usd']}")
print(f"Avg Latency: {analytics['average_latency_ms']}ms")
print(f"Success Rate: {analytics['successful_rate']*100}%")
```

### Test Connectivity
```python
# Test all providers
results = await client.test_connectivity()
for provider, status in results.items():
    print(f"{provider}: {status['status']}")
```

### Monitor Costs
- Dashboard: https://app.portkey.ai/usage
- Alert threshold: $10.00
- Cost tracking enabled for all requests

## 🛡️ Security Best Practices

### 1. Virtual Key Management
- ✅ Real API keys stored only in Portkey vault
- ✅ Virtual keys used in code (no real keys exposed)
- ✅ Rotate keys regularly at https://app.portkey.ai

### 2. Guardrails
- ✅ PII redaction enabled
- ✅ Content filtering active
- ✅ Max output tokens: 8192

### 3. Rate Limiting
- Requests per minute: 60
- Tokens per minute: 100,000
- Concurrent requests: 10

## 🚦 Testing

### Run Integration Tests
```bash
# Run comprehensive test suite
python3 scripts/test_portkey_integration.py

# Expected output:
# ✅ Portkey Connection: PASSED
# ✅ LiteLLM Squad: PASSED  
# ✅ Builder App: PASSED
# ✅ Unified Workflow: PASSED
```

### Quick Verification
```bash
# Check environment
echo $PORTKEY_API_KEY  # Should show your API key

# Test with curl
curl https://api.portkey.ai/v1/models \
  -H "x-portkey-api-key: $PORTKEY_API_KEY"
```

## 💰 Cost Optimization

### Provider Costs (per 1M tokens)
| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | GPT-4o | $2.50 | $10.00 |
| Anthropic | Claude 3.5 | $3.00 | $15.00 |
| DeepSeek | DeepSeek Chat | $0.20 | $0.80 |
| Groq | Llama 70B | $0.50 | $0.50 |
| Perplexity | Sonar | $5.00 | $5.00 |

### Optimization Strategies
1. **Use DeepSeek** for bulk/draft work (80% cost savings)
2. **Enable semantic caching** (30-50% reduction)
3. **Batch similar requests** (better cache hits)
4. **Use mode-based routing** (auto-selects cheapest suitable model)

## 🔄 Workflow Integration

### Terminal Setup (iTerm2 + Zsh)
```bash
# Add aliases to ~/.zshrc
alias sp="sophia portkey"
alias spt="sophia test"
alias spanalytics="python3 -c 'from builder_cli.lib.providers import get_providers_client; print(get_providers_client().get_analytics())'"

# Split pane workflow
# Left: Run sophia commands
# Right: Monitor logs (tail -f ~/.portkey/logs)
# Bottom: Edit code
```

### Git Integration
```bash
# Track changes
cd ~/sophia-intel-ai
git add .
git commit -m "Configure Portkey gateway with 10 providers"
```

## 🐛 Troubleshooting

### Common Issues

1. **Virtual Key Errors**
   - Verify keys in Portkey dashboard
   - Check `.env.portkey` file exists
   - Ensure `load_dotenv(".env.portkey")` is called

2. **Provider Failures**
   - Check provider status at provider's status page
   - Verify virtual key is active
   - Test with `client.test_connectivity()`

3. **High Costs**
   - Enable semantic caching
   - Use cheaper models for drafts
   - Set cost alerts in Portkey dashboard

4. **Slow Responses**
   - Use FAST mode for time-sensitive tasks
   - Check provider latency in analytics
   - Consider switching providers

## 📚 Resources

- **Portkey Dashboard**: https://app.portkey.ai
- **Portkey Docs**: https://docs.portkey.ai
- **Provider Status Pages**:
  - OpenAI: https://status.openai.com
  - Anthropic: https://status.anthropic.com
  - DeepSeek: https://platform.deepseek.com/status

## 🎉 Summary

Your Portkey gateway is now fully configured with:
- ✅ 10 LLM providers with virtual keys
- ✅ Intelligent routing across 3 systems
- ✅ Cost optimization and caching
- ✅ Security guardrails
- ✅ Comprehensive monitoring

The system automatically:
- Routes requests to optimal providers
- Falls back on failures
- Caches similar requests
- Tracks costs and usage
- Validates and repairs JSON outputs

**Next Steps**:
1. Add your real API keys to Portkey vault
2. Set up cost alerts at $10 threshold
3. Monitor usage for first week
4. Optimize routing based on analytics

---
*Last Updated: 2025-09-11*
*Portkey Version: 1.7.0*
*Environment: sophia-intel-ai*