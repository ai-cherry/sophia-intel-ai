#!/bin/bash

# Sophia Intel AI - Smart Startup Script
# Ensures everything starts correctly on first try
# Enhanced with Vector Server support

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
WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8080}"
EOF
    # Expand variables
    envsubst < .env.master > .env.master.tmp
    mv .env.master.tmp .env.master
    chmod 600 .env.master
fi

# Source environment
source .env.master

# Check for Weaviate URL
if [ -z "$WEAVIATE_URL" ]; then
    echo -e "${YELLOW}   Warning: WEAVIATE_URL not set, Vector server may have limited functionality${NC}"
    export WEAVIATE_URL="http://localhost:8080"
fi

# 2. Start Redis (if needed)
echo -e "\n${YELLOW}2. Checking Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    echo "   Starting Redis..."
    redis-server --daemonize yes --dir ~/sophia-intel-ai --logfile logs/redis.log
    sleep 2
fi
echo -e "   ${GREEN}✅ Redis running${NC}"

# 3. Skipping local LLM proxies (Portkey-only policy)

# 4. Start MCP Servers
echo -e "\n${YELLOW}4. Starting MCP Servers...${NC}"

# Create logs and pids directories if they don't exist
mkdir -p logs .pids

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

# Start Vector Server
if ! curl -s http://localhost:8085/health >/dev/null 2>&1; then
    echo "   Starting Vector Server..."
    
    # Check if Weaviate is accessible
    if curl -s "$WEAVIATE_URL/v1/.well-known/ready" >/dev/null 2>&1; then
        echo -e "   ${GREEN}Weaviate detected at $WEAVIATE_URL${NC}"
    else
        echo -e "   ${YELLOW}Warning: Weaviate not accessible at $WEAVIATE_URL${NC}"
        echo -e "   ${YELLOW}Vector server will run in degraded mode${NC}"
    fi
    
    nohup python3 -m uvicorn mcp.vector.server:app \
        --host 0.0.0.0 --port 8085 \
        > logs/mcp-vector.log 2>&1 &
    echo $! > .pids/mcp-vector.pid
    sleep 2
fi
echo -e "   ${GREEN}✅ Vector Server on 8085${NC}"

# 5. Validation
echo -e "\n${YELLOW}5. Running validation tests...${NC}"

# Test MCP servers
for port in 8081 8082 8084 8085; do
    if curl -s http://localhost:$port/health | grep -q -E "(healthy|ok)" 2>/dev/null; then
        echo -e "   ${GREEN}✅ MCP on $port: Healthy${NC}"
    else
        # Check if it's Vector server in degraded mode
        if [ "$port" = "8085" ]; then
            response=$(curl -s http://localhost:$port/health 2>/dev/null || echo "{}")
            if echo "$response" | grep -q "degraded" 2>/dev/null; then
                echo -e "   ${YELLOW}⚠️ MCP on $port: Degraded (Weaviate unavailable)${NC}"
            else
                echo -e "   ${RED}❌ MCP on $port: Not healthy${NC}"
            fi
        else
            echo -e "   ${RED}❌ MCP on $port: Not healthy${NC}"
        fi
    fi
done

# 6. Summary
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}STARTUP COMPLETE${NC}"
echo -e "${BLUE}================================${NC}\n"

echo "Quick test commands:"
echo "  python3 scripts/validate_mcp_servers.py --quick"
echo "  python3 -m sophia_cli status"
echo "  ./dev check         - Run health check"
echo "  ./dev status        - Detailed status"
echo ""
echo "API Endpoints:"
echo "  Memory:      http://localhost:8081"
echo "  Filesystem:  http://localhost:8082"
echo "  Git:         http://localhost:8084"
echo "  Vector:      http://localhost:8085"
echo ""
echo "Logs location:"
echo "  tail -f logs/mcp-*.log"
echo ""