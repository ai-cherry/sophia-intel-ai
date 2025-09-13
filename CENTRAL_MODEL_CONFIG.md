# 🎯 Central Model Configuration System

**Last Updated:** 2025-09-11  
**Daily Budget:** $1,000  
**Alert Threshold:** $100

## Overview

All three systems (LiteLLM Squad, Builder App, Sophia Intel App) are now controlled from a single configuration file that YOU manage:

**📁 Control File:** `config/user_models_config.yaml`

## 📊 Current Configuration

### Budget Settings
- **Daily Budget:** $1,000.00
- **Alert Threshold:** $100.00
- **Cost Tracking:** Enabled
- **Performance Tracking:** Enabled

### 🤖 Active Models (17 Total) - UPDATED 2025-09-11

| # | Model | Provider | Context | Priority | Use Case |
|---|-------|----------|---------|----------|----------|
| 1 | **Grok 4** ⭐ | X-AI | 256K | 1 | Latest & best reasoning |
| 2 | **GPT-5** | OpenAI | 256K | 1 | Complex reasoning, architecture |
| 3 | **Claude Sonnet 4** | Anthropic | 200K | 1 | Code generation, analysis |
| 4 | **Gemini 2.5 Pro** | Google | 2M | 1 | Research (massive context!) |
| 5 | **DeepSeek V3.1 FREE** 🎉 | DeepSeek | 128K | 2 | **$0 COST CODING!** |
| 6 | **DeepSeek V3 0324** | DeepSeek | 128K | 2 | Latest reasoning variant |
| 7 | **Qwen3 Coder** | Qwen | 128K | 2 | Specialized code generation |
| 8 | **Llama 4 Maverick** | Meta | 128K | 2 | Creative problem solving |
| 9 | **Grok Code Fast 1** | X-AI | 128K | 2 | Blazing fast code tasks |
| 10 | **Gemini 2.5 Flash** | Google | 1M | 2 | Speed + capability balance |
| 11 | **DeepSeek V3.1** | DeepSeek | 128K | 2 | Code review, debugging |
| 12 | **Llama 4 Scout** | Meta | 128K | 3 | Research & exploration |
| 13 | **Gemini 2.0 Flash** | Google | 1M | 3 | Even faster variant |
| 14 | **Qwen3 30B A3B** | Qwen | 32K | 4 | Multilingual |
| 15 | **GLM 4.5** | Z-AI | 128K | 4 | Research, academic |
| 16 | **GPT-4.1 Mini** | OpenAI | 128K | 5 | Quick tasks |
| 17 | **Gemini 2.5 Flash Lite** | Google | 1M | 5 | Ultra-fast simple tasks |

### 📋 Routing Policies (9 Total) - UPDATED 2025-09-11

| Policy | Description | Primary Models |
|--------|-------------|----------------|
| **my_default** | Your preferred models | Grok 4, Claude 4, GPT-5, Gemini 2.5 Pro |
| **quality_max** | Best possible output | Grok 4, GPT-5, Claude 4, Gemini 2.5 Pro |
| **speed_max** | Fastest response | Grok Code Fast, Gemini Flash |
| **coding** | Code-optimized | Qwen3 Coder, DeepSeek FREE, Grok Code Fast |
| **creative** | Creative tasks | Llama 4 Maverick, Claude 4, Grok 4 |
| **research** | Long context analysis | Gemini 2.5 Pro (2M!), Llama 4 Scout, GPT-5 |
| **balanced** | Good mix | Gemini Flash, Claude 4, GPT Mini |
| **free_tier** 🎉 | Zero cost! | DeepSeek V3.1 FREE ($0 cost!) |
| **specialists** | Purpose-built | Qwen3 Coder, Llama 4 Scout/Maverick |

## 🔧 How Each App Uses Central Config

### 1. Builder App
```python
from config.integration_adapter import builder_get_model

# Automatically selects based on your config:
planner_model = builder_get_model("planner")   # → Grok 4 or GPT-5
coder_model = builder_get_model("coder")       # → Qwen3 Coder or DeepSeek FREE
reviewer_model = builder_get_model("reviewer") # → Grok 4 or GPT-5
```

### 2. LiteLLM Squad
```python
from config.integration_adapter import litellm_get_config

config = litellm_get_config()
# Returns all 17 models with routing policies
# Uses "balanced" policy by default
# Tests on FREE tier first to save costs!
```

### 3. Sophia Intel App
```python
from config.integration_adapter import sophia_get_model

chat_model = sophia_get_model("chat")       # → Gemini 2.5 Flash
reasoning_model = sophia_get_model("reasoning") # → Grok 4
creative_model = sophia_get_model("creative")   # → Llama 4 Maverick
routine_model = sophia_get_model("routine")     # → DeepSeek FREE ($0!)
```

## 🎮 How to Control Everything

### Change Models
Edit `config/user_models_config.yaml`:

```yaml
models:
  gpt-5:
    enabled: true    # Set to false to disable
    priority: 1      # Lower = higher priority (1-10)
```

### Change Routing Policies
```yaml
routing_policies:
  my_default:
    models:
      - claude-sonnet-4  # Your first choice
      - gpt-5           # Your second choice
      - gemini-2.5-pro  # Your third choice
```

### Change System Behavior
```yaml
system_overrides:
  builder_app:
    planner_policy: "quality_max"  # Change to any policy
    coder_policy: "coding"
    reviewer_policy: "quality_max"
```

### Adjust Budget
```yaml
monitoring:
  daily_budget: 1000.00    # Your $1,000 daily limit
  cost_alert_threshold: 100.00
```

## 🚀 Integration Status

| System | Status | Integration Method |
|--------|--------|-------------------|
| **Builder App** | ✅ Ready | Uses `integration_adapter.builder_get_model()` |
| **LiteLLM Squad** | ✅ Ready | Uses `integration_adapter.litellm_get_config()` |
| **Sophia Intel** | ✅ Ready | Uses `integration_adapter.sophia_get_model()` |

### Integration Adapter
All systems connect through `config/integration_adapter.py`:
- Single point of integration
- Reads from your `user_models_config.yaml`
- Provides system-specific interfaces
- Hot-reloads on config changes

## 📊 Automatic Task Routing

The system automatically selects models based on keywords:

| Keywords in Task | Selected Model |
|-----------------|----------------|
| "code", "debug", "fix" | Grok Code Fast 1 or DeepSeek |
| "creative", "story" | Sonoma Sky Alpha |
| "research", "analyze" | Gemini 2.5 Pro (2M context!) |
| "quick", "fast" | Gemini Flash variants |
| "best", "careful" | GPT-5 or Claude 4 |
| Context > 100K | Gemini models |
| Context > 500K | Gemini 2.5 Pro only |

## 🔍 Verification Commands

```bash
# Check configuration validity
python3 config/model_manager.py validate

# List all models
python3 config/model_manager.py models

# List all policies
python3 config/model_manager.py policies

# Test routing
python3 config/model_manager.py test

# View full summary
python3 config/model_manager.py

# Test integration
python3 config/integration_adapter.py
```

## 📝 Quick Reference

### Files You Control
- `config/user_models_config.yaml` - Your main control file
- Edit this ONE file to control ALL three systems

### Files That Read Your Config
- `config/model_manager.py` - Manages your configuration
- `config/integration_adapter.py` - Connects to all systems
- All systems automatically use these

### Key Features
- **13 Active Models** - Latest 2025 models only
- **7 Routing Policies** - Flexible selection strategies
- **$1,000 Daily Budget** - Generous limit for quality work
- **Quality & Performance Focus** - No compromises on output
- **Central Control** - One file controls everything
- **Hot Reload** - Changes take effect immediately

## 🎯 Summary

You now have complete control over all AI model routing across all three systems:

1. **Edit ONE file:** `config/user_models_config.yaml`
2. **All systems automatically use your settings**
3. **Latest 2025 models configured**
4. **$1,000 daily budget active**
5. **Quality and performance prioritized**

The integration is complete and all documentation is updated!