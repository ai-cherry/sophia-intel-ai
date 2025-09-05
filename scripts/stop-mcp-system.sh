#!/bin/bash

# Sophia MCP System Stop Script
# Stops all components of the MCP infrastructure

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🛑 Stopping Sophia MCP System${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Load PIDs if available
if [ -f /tmp/mcp-pids.sh ]; then
    source /tmp/mcp-pids.sh
fi

# Stop MCP Bridge Adapters
echo -e "\n${YELLOW}Stopping MCP Bridge Adapters...${NC}"
pkill -f "claude-adapter" || true
pkill -f "roo-adapter" || true
pkill -f "cline-adapter" || true
echo -e "${GREEN}✓ MCP Bridge adapters stopped${NC}"

# Stop MCP Server
echo -e "\n${YELLOW}Stopping MCP Server...${NC}"
pkill -f "app.mcp.server_v2" || true
if [ ! -z "$MCP_PID" ]; then
    kill $MCP_PID 2>/dev/null || true
fi
echo -e "${GREEN}✓ MCP Server stopped${NC}"

# Stop Monitoring Stack
echo -e "\n${YELLOW}Stopping Monitoring Stack...${NC}"
cd /Users/lynnmusil/sophia-intel-ai
docker-compose -f docker-compose.monitoring.yml down 2>/dev/null || true
echo -e "${GREEN}✓ Monitoring stack stopped${NC}"

# Optionally stop Weaviate
read -p "Stop Weaviate? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Stopping Weaviate...${NC}"
    docker stop weaviate 2>/dev/null || true
    docker rm weaviate 2>/dev/null || true
    echo -e "${GREEN}✓ Weaviate stopped${NC}"
fi

# Optionally stop Redis
read -p "Stop Redis? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Stopping Redis...${NC}"
    redis-cli shutdown 2>/dev/null || true
    echo -e "${GREEN}✓ Redis stopped${NC}"
fi

# Clean up PID file
rm -f /tmp/mcp-pids.sh

echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Sophia MCP System stopped${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
