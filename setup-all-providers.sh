#!/bin/bash

# Complete Multi-Provider Setup Script
# Sets up LiteLLM, updates Opencode auth, no conflicts

set -e

echo "🚀 Complete Multi-Provider Setup"
echo "================================"
echo ""

# Load environment
source ~/sophia-intel-ai/.env.master

# Step 1: Check/Install LiteLLM
echo "📦 [1/5] Checking LiteLLM..."
if ! command -v litellm &> /dev/null; then
    echo "Installing LiteLLM..."
    pip install litellm
else
    echo "✓ LiteLLM already installed"
fi

# Step 2: Stop existing LiteLLM if running
echo "🔄 [2/5] Stopping any existing LiteLLM..."
if [ -f ~/sophia-intel-ai/litellm.pid ]; then
    OLD_PID=$(cat ~/sophia-intel-ai/litellm.pid)
    kill $OLD_PID 2>/dev/null || true
    rm ~/sophia-intel-ai/litellm.pid
fi
pkill -f "litellm.*port 4000" 2>/dev/null || true
sleep 2

# Step 3: Create comprehensive LiteLLM config
echo "📝 [3/5] Creating LiteLLM configuration..."
cat > ~/sophia-intel-ai/litellm-complete.yaml << 'EOF'
model_list:
  # === DIRECT HIGH-PRIORITY MODELS ===
  
  # OpenAI Direct
  - model_name: gpt-4-turbo
    litellm_params:
      model: gpt-4-turbo-preview
      api_key: ${OPENAI_API_KEY}
  
  - model_name: gpt-4
    litellm_params:
      model: gpt-4
      api_key: ${OPENAI_API_KEY}
  
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo
      api_key: ${OPENAI_API_KEY}
  
  # Anthropic Direct
  - model_name: claude-3-opus
    litellm_params:
      model: claude-3-opus-20240229
      api_key: ${ANTHROPIC_API_KEY}
  
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: claude-3-5-sonnet-20241022
      api_key: ${ANTHROPIC_API_KEY}
  
  - model_name: claude-3-haiku
    litellm_params:
      model: claude-3-haiku-20240307
      api_key: ${ANTHROPIC_API_KEY}
  
  # DeepSeek Direct
  - model_name: deepseek-coder
    litellm_params:
      model: deepseek-coder
      api_key: ${DEEPSEEK_API_KEY}
      api_base: https://api.deepseek.com/v1
  
  - model_name: deepseek-chat
    litellm_params:
      model: deepseek-chat
      api_key: ${DEEPSEEK_API_KEY}
      api_base: https://api.deepseek.com/v1
  
  # Groq Direct (Fastest)
  - model_name: groq-llama3-70b
    litellm_params:
      model: groq/llama3-70b-8192
      api_key: ${GROQ_API_KEY}
  
  - model_name: groq-llama3-8b
    litellm_params:
      model: groq/llama3-8b-8192
      api_key: ${GROQ_API_KEY}
  
  - model_name: groq-mixtral
    litellm_params:
      model: groq/mixtral-8x7b-32768
      api_key: ${GROQ_API_KEY}
  
  - model_name: groq-gemma
    litellm_params:
      model: groq/gemma-7b-it
      api_key: ${GROQ_API_KEY}
  
  # Mistral Direct
  - model_name: mistral-large
    litellm_params:
      model: mistral-large-latest
      api_key: ${MISTRAL_API_KEY}
  
  - model_name: mistral-medium
    litellm_params:
      model: mistral-medium-latest
      api_key: ${MISTRAL_API_KEY}
  
  # Perplexity (With Internet)
  - model_name: perplexity-online
    litellm_params:
      model: perplexity/sonar-medium-online
      api_key: ${PERPLEXITY_API_KEY}
  
  # === OPENROUTER MODELS (100+) ===
  
  - model_name: or-auto
    litellm_params:
      model: openrouter/auto
      api_key: ${OPENROUTER_API_KEY}
  
  - model_name: or-claude-3-opus
    litellm_params:
      model: openrouter/anthropic/claude-3-opus
      api_key: ${OPENROUTER_API_KEY}
  
  - model_name: or-mistral-large
    litellm_params:
      model: openrouter/mistralai/mistral-large
      api_key: ${OPENROUTER_API_KEY}
  
  # === TOGETHER AI MODELS ===
  
  - model_name: together-llama3-70b
    litellm_params:
      model: together_ai/meta-llama/Llama-3-70b-chat-hf
      api_key: ${TOGETHER_API_KEY}
  
  - model_name: together-llama3-8b
    litellm_params:
      model: together_ai/meta-llama/Llama-3-8b-chat-hf
      api_key: ${TOGETHER_API_KEY}
  
  - model_name: together-mixtral-8x22b
    litellm_params:
      model: together_ai/mistralai/Mixtral-8x22B-Instruct-v0.1
      api_key: ${TOGETHER_API_KEY}
  
  - model_name: together-qwen-72b
    litellm_params:
      model: together_ai/Qwen/Qwen1.5-72B-Chat
      api_key: ${TOGETHER_API_KEY}

# Router configuration
router_settings:
  routing_strategy: "simple"  # simple, usage-based, latency-based
  
  # Fallback chain for reliability
  fallback_models:
    - claude-3-5-sonnet
    - gpt-4-turbo
    - groq-llama3-70b
    - together-llama3-70b
    - or-auto
  
  # Model aliases for convenience
  model_aliases:
    "claude": "claude-3-5-sonnet"
    "gpt4": "gpt-4-turbo"
    "llama": "groq-llama3-70b"
    "fast": "groq-mixtral"
    "cheap": "gpt-3.5-turbo"
    "online": "perplexity-online"
  
  # Timeouts per model
  model_timeouts:
    gpt-4: 120
    gpt-4-turbo: 120
    claude-3-opus: 120
    default: 60
  
  # Retry policy
  retry_policy:
    max_retries: 3
    retry_delay: 1
  
  # Caching
  cache: true
  cache_ttl: 3600
  cache_dir: ~/sophia-intel-ai/.litellm_cache

general_settings:
  master_key: sk-litellm-master-2025
  database_url: sqlite:///~/sophia-intel-ai/litellm.db
  max_parallel_requests: 100
  request_timeout: 120
  stream: true
  telemetry: false
  drop_params: false
  set_verbose: false
  json_logs: true
  log_file: ~/sophia-intel-ai/logs/litellm.log
EOF

echo "✓ Created litellm-complete.yaml"

# Step 4: Start LiteLLM proxy
echo "🚀 [4/5] Starting LiteLLM proxy..."
mkdir -p ~/sophia-intel-ai/logs
nohup litellm --config ~/sophia-intel-ai/litellm-complete.yaml --port 4000 > ~/sophia-intel-ai/logs/litellm.log 2>&1 &
LITELLM_PID=$!
echo $LITELLM_PID > ~/sophia-intel-ai/litellm.pid
echo "✓ LiteLLM started (PID: $LITELLM_PID)"
sleep 3

# Test LiteLLM is running
if curl -s http://localhost:4000/health > /dev/null; then
    echo "✓ LiteLLM proxy is healthy"
else
    echo "⚠️  LiteLLM may not be running properly. Check logs: tail -f ~/sophia-intel-ai/logs/litellm.log"
fi

# Step 5: Update Opencode auth.json with ALL providers
echo "🔧 [5/5] Updating Opencode authentication..."
cat > ~/.local/share/opencode/auth.json << EOF
{
  "credentials": [
    {
      "provider": "litellm",
      "name": "LiteLLM Unified Router",
      "apiKey": "sk-litellm-master-2025",
      "baseURL": "http://localhost:4000",
      "description": "Local proxy with ALL models and fallbacks"
    },
    {
      "provider": "portkey",
      "name": "Portkey Cloud Router",
      "apiKey": "$PORTKEY_API_KEY",
      "baseURL": "https://api.portkey.ai/v1",
      "description": "Cloud routing with analytics"
    },
    {
      "provider": "openai-direct",
      "name": "OpenAI Direct",
      "apiKey": "$OPENAI_API_KEY",
      "baseURL": "https://api.openai.com/v1",
      "description": "Direct to OpenAI, no proxy"
    },
    {
      "provider": "anthropic-direct",
      "name": "Anthropic Direct",
      "apiKey": "$ANTHROPIC_API_KEY",
      "baseURL": "https://api.anthropic.com/v1",
      "description": "Direct to Anthropic, no proxy"
    },
    {
      "provider": "groq-direct",
      "name": "Groq Direct (Fastest)",
      "apiKey": "$GROQ_API_KEY",
      "baseURL": "https://api.groq.com/openai/v1",
      "description": "Direct to Groq, fastest inference"
    },
    {
      "provider": "deepseek-direct",
      "name": "DeepSeek Direct",
      "apiKey": "$DEEPSEEK_API_KEY",
      "baseURL": "https://api.deepseek.com/v1",
      "description": "Direct to DeepSeek for code"
    },
    {
      "provider": "mistral-direct",
      "name": "Mistral Direct",
      "apiKey": "$MISTRAL_API_KEY",
      "baseURL": "https://api.mistral.ai/v1",
      "description": "Direct to Mistral"
    },
    {
      "provider": "perplexity-direct",
      "name": "Perplexity Direct",
      "apiKey": "$PERPLEXITY_API_KEY",
      "baseURL": "https://api.perplexity.ai",
      "description": "Direct to Perplexity with web search"
    },
    {
      "provider": "openrouter-direct",
      "name": "OpenRouter Direct",
      "apiKey": "$OPENROUTER_API_KEY",
      "baseURL": "https://openrouter.ai/api/v1",
      "description": "Direct to OpenRouter, 100+ models"
    },
    {
      "provider": "together-direct",
      "name": "Together AI Direct",
      "apiKey": "$TOGETHER_API_KEY",
      "baseURL": "https://api.together.xyz/v1",
      "description": "Direct to Together, open models"
    }
  ]
}
EOF

echo "✓ Updated Opencode auth.json"

# Create helper scripts
echo ""
echo "📝 Creating helper scripts..."

# Multi-agent launcher
cat > ~/sophia-intel-ai/launch-multi-agent.sh << 'SCRIPT_EOF'
#!/bin/bash
# Launch multiple agents with different providers

echo "🤖 Launching Multi-Agent Swarm"
echo "=============================="

# Agent 1: Fast code generation (Groq)
echo "Agent 1: Groq Mixtral for fast code..."
opencode run --provider groq-direct --model mixtral-8x7b-32768 "Generate a Python web scraper" &

# Agent 2: Complex reasoning (Anthropic)
echo "Agent 2: Claude for analysis..."
opencode run --provider anthropic-direct --model claude-3-5-sonnet-20241022 "Analyze security vulnerabilities" &

# Agent 3: Cost-optimized (LiteLLM with fallbacks)
echo "Agent 3: LiteLLM with auto-fallback..."
opencode run --provider litellm --model cheap "Generate test cases" &

# Agent 4: Research with web (Perplexity)
echo "Agent 4: Perplexity for research..."
opencode run --provider perplexity-direct --model sonar-medium-online "Latest Python security best practices" &

echo ""
echo "All agents launched. Waiting for completion..."
wait
echo "✅ All agents completed"
SCRIPT_EOF
chmod +x ~/sophia-intel-ai/launch-multi-agent.sh

# Provider tester
cat > ~/sophia-intel-ai/test-all-providers.sh << 'SCRIPT_EOF'
#!/bin/bash
# Test all provider connections

echo "🧪 Testing All Providers"
echo "======================="

test_provider() {
    PROVIDER=$1
    MODEL=$2
    echo -n "Testing $PROVIDER... "
    
    RESPONSE=$(opencode run --provider "$PROVIDER" --model "$MODEL" "Say 'OK' if working" 2>&1)
    
    if echo "$RESPONSE" | grep -q "OK\|working"; then
        echo "✅ Working"
    else
        echo "❌ Failed"
        echo "  Error: ${RESPONSE:0:100}..."
    fi
}

# Test direct providers
test_provider "openai-direct" "gpt-3.5-turbo"
test_provider "anthropic-direct" "claude-3-haiku-20240307"
test_provider "groq-direct" "llama3-8b-8192"
test_provider "deepseek-direct" "deepseek-chat"
test_provider "mistral-direct" "mistral-medium"

# Test routers
test_provider "litellm" "gpt-3.5-turbo"
test_provider "portkey" "gpt-3.5-turbo"
test_provider "openrouter-direct" "openai/gpt-3.5-turbo"
test_provider "together-direct" "meta-llama/Llama-3-8b-chat-hf"
SCRIPT_EOF
chmod +x ~/sophia-intel-ai/test-all-providers.sh

# LiteLLM manager
cat > ~/sophia-intel-ai/litellm-manager.sh << 'SCRIPT_EOF'
#!/bin/bash
# Manage LiteLLM proxy

case "$1" in
    start)
        if [ -f ~/sophia-intel-ai/litellm.pid ]; then
            echo "LiteLLM already running"
        else
            echo "Starting LiteLLM..."
            nohup litellm --config ~/sophia-intel-ai/litellm-complete.yaml --port 4000 > ~/sophia-intel-ai/logs/litellm.log 2>&1 &
            echo $! > ~/sophia-intel-ai/litellm.pid
            echo "Started with PID: $(cat ~/sophia-intel-ai/litellm.pid)"
        fi
        ;;
    stop)
        if [ -f ~/sophia-intel-ai/litellm.pid ]; then
            kill $(cat ~/sophia-intel-ai/litellm.pid)
            rm ~/sophia-intel-ai/litellm.pid
            echo "LiteLLM stopped"
        else
            echo "LiteLLM not running"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if [ -f ~/sophia-intel-ai/litellm.pid ]; then
            PID=$(cat ~/sophia-intel-ai/litellm.pid)
            if ps -p $PID > /dev/null; then
                echo "LiteLLM running (PID: $PID)"
                echo "Health: $(curl -s http://localhost:4000/health)"
            else
                echo "LiteLLM PID file exists but process not running"
            fi
        else
            echo "LiteLLM not running"
        fi
        ;;
    logs)
        tail -f ~/sophia-intel-ai/logs/litellm.log
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        ;;
esac
SCRIPT_EOF
chmod +x ~/sophia-intel-ai/litellm-manager.sh

echo "✓ Created helper scripts"

# Final summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ COMPLETE MULTI-PROVIDER SETUP SUCCESSFUL!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 Available Providers in Opencode:"
echo "  • litellm          - Unified router with fallbacks (RECOMMENDED)"
echo "  • portkey          - Cloud router with analytics"
echo "  • openai-direct    - Direct to OpenAI"
echo "  • anthropic-direct - Direct to Anthropic"
echo "  • groq-direct      - Direct to Groq (FASTEST)"
echo "  • deepseek-direct  - Direct to DeepSeek"
echo "  • mistral-direct   - Direct to Mistral"
echo "  • perplexity-direct- Direct with web search"
echo "  • openrouter-direct- 100+ models"
echo "  • together-direct  - Open source models"
echo ""
echo "🎯 Quick Usage Examples:"
echo ""
echo "  # Fast inference (Groq)"
echo "  opencode run --provider groq-direct --model llama3-70b-8192 'Generate code'"
echo ""
echo "  # Reliable with fallbacks (LiteLLM)"
echo "  opencode run --provider litellm --model claude-3-5-sonnet 'Complex task'"
echo ""
echo "  # Cost optimized (LiteLLM aliases)"
echo "  opencode run --provider litellm --model cheap 'Simple task'"
echo ""
echo "  # With web search (Perplexity)"
echo "  opencode run --provider perplexity-direct --model sonar-medium-online 'Latest news'"
echo ""
echo "🛠️ Helper Commands:"
echo "  ./litellm-manager.sh status    - Check LiteLLM status"
echo "  ./test-all-providers.sh        - Test all connections"
echo "  ./launch-multi-agent.sh        - Launch parallel agents"
echo ""
echo "📝 Next Steps:"
echo "  1. Test providers: ./test-all-providers.sh"
echo "  2. Launch Opencode: cd ~/sophia-intel-ai && opencode"
echo "  3. Try different providers in TUI"
echo ""
echo "⚠️  Important Notes:"
echo "  - LiteLLM is running on port 4000"
echo "  - Logs: tail -f ~/sophia-intel-ai/logs/litellm.log"
echo "  - Stop LiteLLM: ./litellm-manager.sh stop"
echo "  - All API keys loaded from .env.master"
SCRIPT_EOF