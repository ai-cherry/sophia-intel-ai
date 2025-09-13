#!/bin/bash

# Sophia Intel AI - Smart Startup Script
# Ensures everything starts correctly on first try

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Sophia Intel AI - Smart Startup${NC}"
echo -e "${BLUE}================================${NC}\n"

# 1. Pre-flight checks
echo -e "${YELLOW}1. Running pre-flight checks...${NC}"

# Kill any zombie processes
echo "   Cleaning up zombie processes..."
pkill -f "litellm.*4000" 2>/dev/null || true
pkill -f "mcp.*server" 2>/dev/null || true
sleep 2

# Check environment
if [ ! -f .env.master ]; then
    echo -e "${RED}   ERROR: .env.master not found${NC}"
    echo "   Creating from environment..."
    cat > .env.master << 'EOF'
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
OPENAI_API_KEY="${OPENAI_API_KEY}"
XAI_API_KEY="${XAI_API_KEY}"
GROQ_API_KEY="${GROQ_API_KEY}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}"
MISTRAL_API_KEY="${MISTRAL_API_KEY}"
PERPLEXITY_API_KEY="${PERPLEXITY_API_KEY}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
TOGETHER_API_KEY="${TOGETHER_API_KEY}"
LITELLM_MASTER_KEY="sk-litellm-master-2025"
EOF
    # Expand variables
    envsubst < .env.master > .env.master.tmp
    mv .env.master.tmp .env.master
    chmod 600 .env.master
fi

# Source environment
source .env.master

# 2. Start Redis (if needed)
echo -e "\n${YELLOW}2. Checking Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    echo "   Starting Redis..."
    redis-server --daemonize yes --dir ~/sophia-intel-ai --logfile logs/redis.log
    sleep 2
fi
echo -e "   ${GREEN}✅ Redis running${NC}"

# 3. Start LiteLLM
echo -e "\n${YELLOW}3. Starting LiteLLM...${NC}"
if ! curl -s http://localhost:4000/health >/dev/null 2>&1; then
    # Use the system litellm
    nohup /opt/homebrew/bin/litellm \
        --config litellm-complete.yaml \
        --port 4000 \
        > logs/litellm.log 2>&1 &
    echo $! > .pids/litellm.pid
    
    # Wait for LiteLLM to be ready
    echo -n "   Waiting for LiteLLM"
    for i in {1..10}; do
        if curl -s http://localhost:4000/v1/models -H "Authorization: Bearer sk-litellm-master-2025" >/dev/null 2>&1; then
            echo -e "\n   ${GREEN}✅ LiteLLM ready (25 models)${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
else
    echo -e "   ${GREEN}✅ LiteLLM already running${NC}"
fi

# 4. Start MCP Servers
echo -e "\n${YELLOW}4. Starting MCP Servers...${NC}"

# Start Memory Server
if ! curl -s http://localhost:8081/health >/dev/null 2>&1; then
    echo "   Starting Memory Server..."
    nohup python3 -m uvicorn mcp.memory_server:app \
        --host 0.0.0.0 --port 8081 \
        > logs/mcp-memory.log 2>&1 &
    echo $! > .pids/mcp-memory.pid
    sleep 2
fi
echo -e "   ${GREEN}✅ Memory Server on 8081${NC}"

# Start Filesystem Server
if ! curl -s http://localhost:8082/health >/dev/null 2>&1; then
    echo "   Starting Filesystem Server..."
    nohup python3 -m uvicorn mcp.filesystem.server:app \
        --host 0.0.0.0 --port 8082 \
        > logs/mcp-filesystem.log 2>&1 &
    echo $! > .pids/mcp-filesystem.pid
    sleep 2
fi
echo -e "   ${GREEN}✅ Filesystem Server on 8082${NC}"

# Start Git Server
if ! curl -s http://localhost:8084/health >/dev/null 2>&1; then
    echo "   Starting Git Server..."
    nohup python3 -m uvicorn mcp.git.server:app \
        --host 0.0.0.0 --port 8084 \
        > logs/mcp-git.log 2>&1 &
    echo $! > .pids/mcp-git.pid
    sleep 2
fi
echo -e "   ${GREEN}✅ Git Server on 8084${NC}"

# 5. Validation
echo -e "\n${YELLOW}5. Running validation tests...${NC}"

# Test LiteLLM
if curl -s http://localhost:4000/v1/models \
    -H "Authorization: Bearer sk-litellm-master-2025" \
    | jq -r '.data | length' | grep -q "^[0-9]" 2>/dev/null; then
    MODEL_COUNT=$(curl -s http://localhost:4000/v1/models -H "Authorization: Bearer sk-litellm-master-2025" | jq -r '.data | length')
    echo -e "   ${GREEN}✅ LiteLLM: $MODEL_COUNT models available${NC}"
else
    echo -e "   ${RED}❌ LiteLLM: Not responding properly${NC}"
fi

# Test MCP servers
for port in 8081 8082 8084; do
    if curl -s http://localhost:$port/health | grep -q "healthy" 2>/dev/null; then
        echo -e "   ${GREEN}✅ MCP on $port: Healthy${NC}"
    else
        echo -e "   ${RED}❌ MCP on $port: Not healthy${NC}"
    fi
done

# 6. Summary
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}STARTUP COMPLETE${NC}"
echo -e "${BLUE}================================${NC}\n"

echo "Quick test commands:"
echo "  ./dev check         - Run health check"
echo "  ./dev status        - Detailed status"
echo "  litellm-cli chat    - Chat with AI"
echo "  opencode           - Launch Opencode"
echo ""
echo "API Endpoints:"
echo "  LiteLLM:     http://localhost:4000"
echo "  Memory:      http://localhost:8081"
echo "  Filesystem:  http://localhost:8082"
echo "  Git:         http://localhost:8084"
echo ""
echo "Auth: Bearer sk-litellm-master-2025"
