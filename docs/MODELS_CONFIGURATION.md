# 🤖 Models Configuration Guide
**Last Updated: 2025-09-11**
**Version: 2.0.0**

## Overview

Sophia Intel AI uses a centralized model configuration system that controls model routing across all three applications (LiteLLM Squad, Builder App, and Sophia Intel App). All model configuration is managed through a single YAML file that YOU control.

## 📋 Active Models (17 Total)

### Premium Tier (Priority 1)
| Model | Provider | Context | Virtual Key | Best For |
|-------|----------|---------|-------------|----------|
| **Grok 4** | X-AI | 256K | `xai-vk-e65d0f` | Complex reasoning, humor |
| **GPT-5** | OpenAI | 256K | `openai-vk-190a60` | Architecture, planning |
| **Claude Sonnet 4** | Anthropic | 200K | `anthropic-vk-b42804` | Code generation, analysis |
| **Gemini 2.5 Pro** | Google | 2M | `google-vk-default` | Massive context research |

### Performance Tier (Priority 2)
| Model | Provider | Context | Virtual Key | Best For |
|-------|----------|---------|-------------|----------|
| **Grok Code Fast 1** | X-AI | 128K | `xai-vk-e65d0f` | Fast code generation |
| **DeepSeek V3.1** | DeepSeek | 128K | `deepseek-vk-24102f` | Code review, debugging |
| **DeepSeek V3.1 FREE** 🎉 | DeepSeek | 128K | Direct | **$0 cost coding!** |
| **DeepSeek V3 0324** | DeepSeek | 128K | `deepseek-vk-24102f` | Latest reasoning |
| **Qwen3 Coder** | Qwen | 128K | `qwen-vk-default` | Specialized coding |
| **Llama 4 Maverick** | Meta | 128K | `vkj-openrouter-cc4151` | Creative solutions |
| **Gemini 2.5 Flash** | Google | 1M | `google-vk-default` | Fast balanced tasks |

### Specialized Tier (Priority 3)
| Model | Provider | Context | Virtual Key | Best For |
|-------|----------|---------|-------------|----------|
| **Llama 4 Scout** | Meta | 128K | `vkj-openrouter-cc4151` | Research, exploration |
| **Gemini 2.0 Flash** | Google | 1M | `google-vk-default` | Ultra-fast responses |

### Research Tier (Priority 4)
| Model | Provider | Context | Virtual Key | Best For |
|-------|----------|---------|-------------|----------|
| **Qwen3 30B A3B** | Qwen | 32K | `qwen-vk-default` | Multilingual support |
| **GLM 4.5** | Z-AI | 128K | `zai-vk-default` | Academic research |

### Efficient Tier (Priority 5)
| Model | Provider | Context | Virtual Key | Best For |
|-------|----------|---------|-------------|----------|
| **GPT-4.1 Mini** | OpenAI | 128K | `openai-vk-190a60` | Quick simple tasks |
| **Gemini 2.5 Flash Lite** | Google | 1M | `google-vk-default` | Ultra-fast simple |

## 🎯 Routing Policies (9 Total)

### 1. **my_default**
Your preferred model selection for general use.
```yaml
models: [grok-4, claude-sonnet-4, gpt-5, gemini-2.5-pro]
fallback: [deepseek-chat-v3.1-free]  # FREE fallback!
```

### 2. **quality_max**
When only the best will do.
```yaml
models: [grok-4, gpt-5, claude-sonnet-4, gemini-2.5-pro]
```

### 3. **speed_max**
Fastest possible response.
```yaml
models: [grok-code-fast-1, gemini-2.5-flash, gemini-2.5-flash-lite]
```

### 4. **coding**
Optimized for code generation and review.
```yaml
models: [qwen3-coder, deepseek-chat-v3.1-free, grok-code-fast-1, claude-sonnet-4]
fallback: [deepseek-v3.1]
```

### 5. **creative**
For creative and narrative tasks.
```yaml
models: [llama-4-maverick, claude-sonnet-4, grok-4]
```

### 6. **research**
Long context and deep analysis.
```yaml
models: [gemini-2.5-pro, llama-4-scout, gpt-5, glm-4.5]
```

### 7. **balanced**
Good mix of speed and quality.
```yaml
models: [gemini-2.5-flash, claude-sonnet-4, gpt-4.1-mini]
```

### 8. **free_tier** 🎉
Zero cost models for routine tasks!
```yaml
models: [deepseek-chat-v3.1-free]
fallback: [deepseek-chat-v3-0324]
```

### 9. **specialists**
Purpose-built models for specific tasks.
```yaml
models: [qwen3-coder, llama-4-scout, llama-4-maverick, deepseek-chat-v3.1-free]
```

## ⚙️ Configuration File

All model configuration is controlled by a single file:
```
config/user_models_config.yaml
```

### Key Sections:

#### 1. Models Section
```yaml
models:
  grok-4:
    enabled: true        # Toggle on/off
    priority: 1          # Lower = higher priority
    provider: x-ai
    display_name: "Grok 4"
    context: 256000
    my_notes: "Latest Grok - excellent reasoning and humor"
    model_id: "x-ai/grok-4"
```

#### 2. Routing Policies
```yaml
routing_policies:
  coding:
    name: "Coding Tasks"
    description: "Optimized for code generation"
    models:
      - qwen3-coder
      - deepseek-chat-v3.1-free
    fallback:
      - gpt-5
```

#### 3. System Overrides
```yaml
system_overrides:
  builder_app:
    planner_policy: "quality_max"
    coder_policy: "coding"
    reviewer_policy: "quality_max"
    use_free_for_tests: true
```

#### 4. Task Rules
```yaml
task_rules:
  - condition: "code in task"
    use_policy: "coding"
  - condition: "free in task or test in task"
    use_policy: "free_tier"
```

## 🔧 How to Configure

### Enable/Disable Models
```yaml
models:
  grok-4:
    enabled: false  # Disable this model
```

### Change Priorities
```yaml
models:
  claude-sonnet-4:
    priority: 1  # Make this highest priority
```

### Create Custom Policy
```yaml
routing_policies:
  my_custom:
    name: "My Custom Policy"
    models:
      - deepseek-chat-v3.1-free  # Use FREE first
      - grok-4                   # Then premium
```

### Assign to System
```yaml
system_overrides:
  sophia_intel:
    default_policy: "my_custom"
```

## 💰 Cost Optimization

### FREE Tier Usage
The DeepSeek V3.1 FREE tier provides excellent coding capabilities at **$0 cost**. Route routine tasks here:

```yaml
# In task_rules:
- condition: "draft in task or test in task"
  use_policy: "free_tier"
```

### Expected Savings
- **40-60% cost reduction** by using FREE tier
- **$50-100/day saved** on routine coding
- **$0 cost** for all test iterations

## 🚀 API Access

### Get Current Model Configuration
```python
from config.model_manager import get_model_manager

manager = get_model_manager()
models = manager.get_active_models()
```

### Get Model for Task
```python
from config.integration_adapter import UnifiedModelRouter

router = UnifiedModelRouter()
model = router.get_builder_model("coder", "implement feature")
# Returns: {"model_id": "qwen3-coder", "virtual_key": "..."}
```

### Select Model by Policy
```python
model = manager.select_model_for_task(
    task="write unit tests",
    policy="coding",
    system="builder_app"
)
```

## 📊 Monitoring

### Daily Budget
```yaml
monitoring:
  daily_budget: 1000.00  # $1,000 daily limit
  track_costs: true
  cost_alert_threshold: 100.00
```

### Performance Tracking
```yaml
monitoring:
  track_performance: true
  log_slow_requests: true  # Log if > 2000ms
  log_failed_requests: true
```

## 🔍 Troubleshooting

### Model Not Available
Check if model is enabled:
```bash
grep "model-name" config/user_models_config.yaml
```

### Wrong Model Selected
1. Check task rules match
2. Verify policy assignment
3. Check system overrides

### High Costs
1. Enable free_tier policy
2. Check daily_budget setting
3. Review cost_alert_threshold

## 📈 Best Practices

1. **Always test on FREE tier first** before using premium models
2. **Use specialized models** for their intended purposes:
   - Qwen3 Coder for code generation
   - Llama 4 Scout for research
   - Llama 4 Maverick for creative problems
3. **Reserve premium models** (Grok 4, GPT-5) for critical tasks
4. **Monitor costs daily** through Portkey dashboard
5. **Adjust priorities** based on performance metrics

## 🔗 Related Documentation

- [Portkey Setup Guide](../PORTKEY_SETUP_GUIDE.md)
- [Central Model Configuration](../CENTRAL_MODEL_CONFIG.md)
- [Model Improvement Report](../MODEL_IMPROVEMENT_REPORT.md)
- [API Reference](./API_REFERENCE.md)

## 📝 Notes

- All changes to `user_models_config.yaml` take effect immediately
- No restart required after configuration changes
- Both Builder App and Sophia Intel App share the same model pool
- Virtual keys ensure provider isolation and parallel execution
- The FREE tier (DeepSeek V3.1) requires no API key