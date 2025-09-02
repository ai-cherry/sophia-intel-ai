#!/bin/bash

# Sophia Intel AI - Swarm & MCP Deployment Script

echo "🚀 Deploying AI Agent Swarm & MCP Integration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found. Installing...${NC}"
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 18
    nvm use 18
fi
echo -e "${GREEN}✅ Node.js found${NC}"

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip3 install -q httpx redis prometheus-client

# Install Node.js dependencies
echo -e "${BLUE}Installing Node.js dependencies...${NC}"
npm install -q prom-client

# Start Redis if not running
echo -e "${BLUE}Checking Redis...${NC}"
if ! redis-cli ping &> /dev/null; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes
fi
echo -e "${GREEN}✅ Redis is running${NC}"

# Start MCP Server
echo -e "${BLUE}Starting MCP Server on port 8003...${NC}"
export AGENT_API_PORT=8003
export LOCAL_DEV_MODE=true
export OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-"your-key-here"}
export PORTKEY_API_KEY=${PORTKEY_API_KEY:-"your-key-here"}

# Kill any existing MCP server on port 8003
lsof -ti:8003 | xargs kill -9 2>/dev/null

# Start MCP server in background
nohup python3 -m app.api.unified_server > logs/mcp_server.log 2>&1 &
MCP_PID=$!
echo -e "${GREEN}✅ MCP Server started (PID: $MCP_PID)${NC}"

# Wait for MCP to be ready
echo -e "${BLUE}Waiting for MCP server to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8003/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ MCP Server is ready${NC}"
        break
    fi
    sleep 1
done

# Test MCP Bridge
echo -e "${BLUE}Testing MCP Bridge connectivity...${NC}"
python3 -m app.swarms.production_mcp_bridge

# Run automated tests
echo -e "${BLUE}Running automated tests...${NC}"
python3 -m pytest tests/api/test_mcp_endpoints.py -v

# Display status
echo -e "\n${GREEN}🎉 Deployment Complete!${NC}\n"
echo -e "Services Running:"
echo -e "  • MCP Server: ${GREEN}http://localhost:8003${NC}"
echo -e "  • Health Check: ${GREEN}http://localhost:8003/health${NC}"
echo -e "  • Hub Interface: ${GREEN}http://localhost:8005/hub${NC}"
echo -e "\nApproved LLM Models (non-RAG):"
echo -e "  • openai/gpt-5"
echo -e "  • x-ai/grok-4"
echo -e "  • anthropic/claude-sonnet-4"
echo -e "  • x-ai/grok-code-fast-1"
echo -e "  • google/gemini-2.5-flash"
echo -e "  • google/gemini-2.5-pro"
echo -e "  • deepseek/deepseek-chat-v3-0324"
echo -e "  • deepseek/deepseek-chat-v3.1"
echo -e "  • qwen/qwen3-30b-a3b"
echo -e "  • z-ai/glm-4.5-air"
echo -e "\nRAG-Only Models (Llama):"
echo -e "  • meta-llama/llama-3.3-70b-instruct (RAG reranking only)"
echo -e "  • meta-llama/llama-3.2-90b-vision-instruct (RAG only)"
echo -e "  • meta-llama/llama-3.1-405b-instruct (RAG only)"
echo -e "\n${YELLOW}Note: All other models have been removed from the system${NC}"