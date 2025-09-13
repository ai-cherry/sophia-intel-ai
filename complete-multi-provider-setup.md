# Complete Multi-Provider Setup Strategy

## 🎯 OPTIMAL ARCHITECTURE: 3-Layer Strategy

### Layer 1: Direct API Keys (Fast, No Middleman)
**For**: High-priority, production workloads
**Providers**: OpenAI, Anthropic, DeepSeek, Groq, Mistral
**Pros**: Fastest response, no proxy overhead, direct rate limits
**Cons**: No fallbacks, keys exposed in memory, no unified logging

### Layer 2: LiteLLM Proxy (Local Router, Full Control)  
**For**: Development, testing, unified interface
**Providers**: ALL providers through one endpoint
**Pros**: Local control, format translation, caching, fallbacks
**Cons**: Extra local process, memory usage, single point of failure

### Layer 3: Portkey Virtual Keys (Cloud Router, Enterprise)
**For**: Production with monitoring, team sharing, cost control
**Providers**: OpenRouter, Together, HuggingFace, + any custom
**Pros**: Cloud fallbacks, analytics, team management, no local keys
**Cons**: Internet dependency, potential latency, costs at scale

## 📦 COMPLETE SETUP SCRIPT

```bash
#!/bin/bash
# Save as: setup-all-providers.sh

echo "🚀 Complete Multi-Provider Setup"
echo "================================"

# Step 1: Install LiteLLM if needed
if ! command -v litellm &> /dev/null; then
    pip install litellm
fi

# Step 2: Create LiteLLM config with ALL providers
cat > ~/sophia-intel-ai/litellm-complete.yaml << 'EOF'
model_list:
  # Direct OpenAI Models
  - model_name: gpt-4-turbo
    litellm_params:
      model: gpt-4-turbo-preview
      api_key: ${OPENAI_API_KEY}
  
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
  
  # Direct Anthropic Models  
  - model_name: claude-3-opus
    litellm_params:
      model: claude-3-opus-20240229
      api_key: ${ANTHROPIC_API_KEY}
  
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: ${ANTHROPIC_API_KEY}
  
  # Direct DeepSeek
  - model_name: deepseek-coder
    litellm_params:
      model: deepseek-coder
      api_key: ${DEEPSEEK_API_KEY}
      api_base: https://api.deepseek.com/v1
  
  # Direct Groq
  - model_name: groq-llama3-70b
    litellm_params:
      model: groq/llama3-70b-8192
      api_key: ${GROQ_API_KEY}
  
  - model_name: groq-mixtral
    litellm_params:
      model: groq/mixtral-8x7b-32768
      api_key: ${GROQ_API_KEY}
  
  # Direct Mistral
  - model_name: mistral-large
    litellm_params:
      model: mistral-large-latest
      api_key: ${MISTRAL_API_KEY}
  
  # OpenRouter Models (100+ models)
  - model_name: openrouter-auto
    litellm_params:
      model: openrouter/auto
      api_key: ${OPENROUTER_API_KEY}
  
  - model_name: openrouter-claude-3-opus
    litellm_params:
      model: openrouter/anthropic/claude-3-opus
      api_key: ${OPENROUTER_API_KEY}
  
  # Together AI Models
  - model_name: together-llama3-70b
    litellm_params:
      model: together_ai/meta-llama/Llama-3-70b-chat-hf
      api_key: ${TOGETHER_API_KEY}
  
  - model_name: together-mixtral
    litellm_params:
      model: together_ai/mistralai/Mixtral-8x22B-Instruct-v0.1
      api_key: ${TOGETHER_API_KEY}
  
  # Perplexity
  - model_name: perplexity-sonar
    litellm_params:
      model: perplexity/sonar-medium-online
      api_key: ${PERPLEXITY_API_KEY}

router_settings:
  routing_strategy: "usage-based"  # or "latency-based"
  
  # Fallback chain for resilience
  fallback_models:
    - claude-3-5-sonnet
    - gpt-4-turbo
    - groq-llama3-70b
    - together-llama3-70b
  
  # Model-specific timeouts
  model_timeouts:
    gpt-4: 120
    claude-3-opus: 120
    default: 60
  
  # Caching
  cache: true
  cache_ttl: 3600

general_settings:
  master_key: sk-litellm-master-2025
  database_url: sqlite:///./litellm_db.sqlite
  max_parallel_requests: 100
  request_timeout: 120
  telemetry: false
EOF

# Step 3: Start LiteLLM in background
echo "Starting LiteLLM proxy..."
nohup litellm --config ~/sophia-intel-ai/litellm-complete.yaml --port 4000 > ~/sophia-intel-ai/litellm.log 2>&1 &
echo $! > ~/sophia-intel-ai/litellm.pid
sleep 3

# Step 4: Add ALL providers to Opencode auth.json
cat > ~/.local/share/opencode/auth.json << 'EOF'
{
  "credentials": [
    {
      "provider": "litellm",
      "name": "LiteLLM Unified Router",
      "apiKey": "sk-litellm-master-2025",
      "baseURL": "http://localhost:4000",
      "description": "Local proxy with ALL models"
    },
    {
      "provider": "portkey",
      "name": "Portkey Cloud Router",
      "apiKey": "nYraiE8dOR9A1gDwaRNpSSXRkXBc",
      "baseURL": "https://api.portkey.ai/v1",
      "description": "Cloud routing with analytics"
    },
    {
      "provider": "openai-direct",
      "name": "OpenAI Direct",
      "apiKey": "${OPENAI_API_KEY}",
      "baseURL": "https://api.openai.com/v1",
      "description": "Direct to OpenAI, no proxy"
    },
    {
      "provider": "anthropic-direct",
      "name": "Anthropic Direct",
      "apiKey": "${ANTHROPIC_API_KEY}",
      "baseURL": "https://api.anthropic.com/v1",
      "description": "Direct to Anthropic, no proxy"
    },
    {
      "provider": "groq-direct",
      "name": "Groq Direct",
      "apiKey": "${GROQ_API_KEY}",
      "baseURL": "https://api.groq.com/openai/v1",
      "description": "Direct to Groq, fastest inference"
    },
    {
      "provider": "deepseek-direct",
      "name": "DeepSeek Direct",
      "apiKey": "${DEEPSEEK_API_KEY}",
      "baseURL": "https://api.deepseek.com/v1",
      "description": "Direct to DeepSeek for code"
    },
    {
      "provider": "openrouter-direct",
      "name": "OpenRouter Direct",
      "apiKey": "${OPENROUTER_API_KEY}",
      "baseURL": "https://openrouter.ai/api/v1",
      "description": "Direct to OpenRouter, 100+ models"
    },
    {
      "provider": "together-direct",
      "name": "Together AI Direct",
      "apiKey": "${TOGETHER_API_KEY}",
      "baseURL": "https://api.together.xyz/v1",
      "description": "Direct to Together, open models"
    }
  ]
}
EOF

echo "✅ Setup complete!"
```

## 🎮 USAGE PATTERNS

### Pattern 1: Speed Priority (Direct)
```bash
opencode run --provider openai-direct --model gpt-4-turbo "Fast response needed"
opencode run --provider groq-direct --model llama3-70b-8192 "Code review"
```

### Pattern 2: Reliability Priority (LiteLLM)
```bash
opencode run --provider litellm --model claude-3-5-sonnet "Complex task"
# Automatically falls back if Claude is down
```

### Pattern 3: Cost Optimization (Portkey)
```bash
opencode run --provider portkey --model "cheapest-available" "Bulk processing"
# Routes to cheapest model based on Portkey config
```

### Pattern 4: Multi-Agent Parallel
```bash
# Different providers for different agents - no conflicts!
opencode run --provider groq-direct --model mixtral-8x7b "Agent 1 task" &
opencode run --provider litellm --model gpt-4 "Agent 2 task" &
opencode run --provider portkey --model claude-3-opus "Agent 3 task" &
wait
```

## ⚖️ PROS, CONS, RISKS & REWARDS

### DIRECT PROVIDERS
**Pros:**
- ⚡ Fastest (no proxy overhead)
- 🎯 Direct rate limits (know exactly what you get)
- 🔒 Provider-specific features available
- 💰 No middleman costs

**Cons:**
- ❌ No fallbacks (if API is down, you're down)
- 🔑 Keys in memory/disk (security risk)
- 📊 No unified logging/monitoring
- 🔄 Need to handle each API's quirks

**Risks:**
- API keys could leak via memory dumps
- No cost controls (can blow through credits)
- Single point of failure per provider

**Best For:** Production critical paths, speed-sensitive ops

### LITELLM PROXY
**Pros:**
- 🔄 Automatic fallbacks
- 📝 Unified interface (OpenAI format for all)
- 💾 Local caching (saves API calls)
- 🔧 Format translation (handles provider quirks)
- 📊 Local logging/metrics

**Cons:**
- 🖥️ Extra process running (RAM usage)
- 🔧 Another thing to maintain
- 🚧 Single local point of failure
- ⏱️ Adds 5-10ms latency

**Risks:**
- Proxy crash takes down all models
- Cache could serve stale responses
- Local disk could fill with logs/cache

**Best For:** Development, testing, experimentation

### PORTKEY VIRTUAL KEYS
**Pros:**
- ☁️ Cloud resilience (their infra, not yours)
- 📊 Beautiful analytics dashboard
- 👥 Team sharing without sharing keys
- 💰 Cost controls and alerts
- 🔄 Smart routing (cost/speed/quality)
- 🔐 Keys never on your machine

**Cons:**
- 🌐 Internet dependency
- 💵 Potential costs at scale
- ⏱️ Added latency (20-50ms)
- 🔒 Another service with your keys

**Risks:**
- Portkey outage affects all models
- Data flows through their servers
- Potential vendor lock-in

**Best For:** Teams, production with monitoring needs

## 🏆 RECOMMENDED SETUP

### For Maximum Reliability + Speed:
1. **Primary**: Direct providers for critical paths
2. **Fallback**: LiteLLM for automatic failover
3. **Analytics**: Portkey for non-critical + monitoring

### Configuration Priority:
```
1. Groq-direct (fastest for Llama/Mixtral)
2. Anthropic-direct (best for complex reasoning)  
3. LiteLLM (unified fallback for everything)
4. Portkey (monitoring + cost optimization)
5. OpenRouter-direct (access to rare models)
```

### Simultaneous Agents Strategy:
```bash
# Agent 1: Fast code generation (Groq)
opencode run --provider groq-direct --model mixtral-8x7b-32768 &

# Agent 2: Complex reasoning (Anthropic)
opencode run --provider anthropic-direct --model claude-3-5-sonnet &

# Agent 3: Cost-optimized research (Portkey routing)
opencode run --provider portkey --model "auto" &

# Agent 4: Fallback-protected critical task (LiteLLM)
opencode run --provider litellm --model gpt-4 &
```

## 🔒 SECURITY BEST PRACTICES

1. **Never commit .env.master** (it's in .gitignore right?)
2. **Rotate keys quarterly** (set calendar reminder)
3. **Use different keys for dev/prod** (isolate blast radius)
4. **Monitor usage** (Portkey dashboard or provider dashboards)
5. **Set spend limits** (all providers support this)

## 🚨 FAILURE MODES & MITIGATIONS

| Failure | Impact | Mitigation |
|---------|--------|------------|
| LiteLLM crashes | All LiteLLM routes fail | Auto-restart script, use direct providers |
| Portkey down | Portkey routes fail | Fallback to LiteLLM or direct |
| API key leaked | Potential abuse | Immediate key rotation, spend alerts |
| Rate limited | Requests fail | Use different provider/key |
| Model deprecated | Specific model fails | Update model names quarterly |

## 🎯 QUICK START COMMANDS

```bash
# 1. Set up everything
chmod +x setup-all-providers.sh && ./setup-all-providers.sh

# 2. Test each layer
opencode run --provider groq-direct --model llama3-70b-8192 "test direct"
opencode run --provider litellm --model gpt-4 "test litellm"  
opencode run --provider portkey --model gpt-4 "test portkey"

# 3. Launch multi-agent
./launch-multi-agent.sh
```

This gives you maximum flexibility with safety nets at every level!