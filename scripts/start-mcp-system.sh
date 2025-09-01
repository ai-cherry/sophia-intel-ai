#!/bin/bash

# Sophia MCP System Startup Script
# Starts all components of the MCP infrastructure

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Sophia MCP System${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Function to check if service is running
check_service() {
    local service=$1
    local port=$2
    local url=$3
    
    echo -e "${YELLOW}Checking ${service}...${NC}"
    
    if curl -s ${url} > /dev/null 2>&1; then
        echo -e "${GREEN}✓ ${service} is running on port ${port}${NC}"
        return 0
    else
        echo -e "${RED}✗ ${service} is not running${NC}"
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo -e "${YELLOW}Waiting for ${service} to be ready...${NC}"
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s ${url} > /dev/null 2>&1; then
            echo -e "${GREEN}✓ ${service} is ready${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${RED}✗ ${service} failed to start${NC}"
    return 1
}

# 1. Check Redis
echo -e "\n${BLUE}1. Checking Redis...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
fi
echo -e "${GREEN}✓ Redis is running${NC}"

# 2. Check Weaviate
echo -e "\n${BLUE}2. Checking Weaviate...${NC}"
if ! check_service "Weaviate" 8080 "http://localhost:8080/v1/.well-known/ready"; then
    echo -e "${YELLOW}Starting Weaviate...${NC}"
    docker run -d \
        --name weaviate \
        -p 8080:8080 \
        -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
        -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
        -e DEFAULT_VECTORIZER_MODULE=text2vec-transformers \
        -e ENABLE_MODULES=text2vec-transformers \
        -e TRANSFORMERS_INFERENCE_API=http://t2v-transformers:8080 \
        --restart unless-stopped \
        semitechnologies/weaviate:latest
    
    wait_for_service "Weaviate" "http://localhost:8080/v1/.well-known/ready"
fi

# 3. Start Monitoring Stack
echo -e "\n${BLUE}3. Starting Monitoring Stack...${NC}"
cd /Users/lynnmusil/sophia-intel-ai

if ! docker ps | grep -q sophia-prometheus; then
    echo -e "${YELLOW}Starting monitoring services...${NC}"
    docker-compose -f docker-compose.monitoring.yml up -d
    sleep 5
fi
echo -e "${GREEN}✓ Monitoring stack is running${NC}"

# 4. Start MCP Server v2
echo -e "\n${BLUE}4. Starting MCP Server v2...${NC}"
export PYTHONPATH=/Users/lynnmusil/sophia-intel-ai
export MCP_ENV=production
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=sophia-mcp-server

# Kill any existing MCP server
pkill -f "app.mcp.server_v2" || true
sleep 1

# Start MCP Server
python3 -m app.mcp.server_v2 > /tmp/mcp-server.log 2>&1 &
MCP_PID=$!
echo "MCP Server PID: $MCP_PID"

# Wait for MCP server
wait_for_service "MCP Server" "http://localhost:8004/health"

# 5. Build MCP Bridge
echo -e "\n${BLUE}5. Building MCP Bridge...${NC}"
cd /Users/lynnmusil/sophia-intel-ai/mcp-bridge

if [ ! -d "dist" ]; then
    echo -e "${YELLOW}Compiling TypeScript...${NC}"
    npm run build
fi
echo -e "${GREEN}✓ MCP Bridge compiled${NC}"

# 6. Start MCP Bridge Adapters
echo -e "\n${BLUE}6. Starting MCP Bridge Adapters...${NC}"

# Kill any existing adapters
pkill -f "claude-adapter" || true
pkill -f "roo-adapter" || true
pkill -f "cline-adapter" || true
sleep 1

# Start adapters in background
echo -e "${YELLOW}Starting Claude adapter...${NC}"
node dist/claude-adapter.js > /tmp/claude-adapter.log 2>&1 &
CLAUDE_PID=$!

echo -e "${YELLOW}Starting Roo/Cursor adapter...${NC}"
node dist/roo-adapter.js > /tmp/roo-adapter.log 2>&1 &
ROO_PID=$!

echo -e "${YELLOW}Starting Cline adapter...${NC}"
node dist/cline-adapter.js > /tmp/cline-adapter.log 2>&1 &
CLINE_PID=$!

sleep 3

# 7. Display Status
echo -e "\n${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Sophia MCP System is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📍 Service Endpoints:"
echo "   • MCP Server: http://localhost:8004"
echo "   • Weaviate: http://localhost:8080"
echo "   • Redis: redis://localhost:6379"
echo ""
echo "📊 Monitoring:"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana: http://localhost:3001"
echo "   • Jaeger: http://localhost:16686"
echo ""
echo "🔧 MCP Adapters:"
echo "   • Claude Desktop: PID $CLAUDE_PID"
echo "   • Roo/Cursor: PID $ROO_PID"
echo "   • Cline: PID $CLINE_PID"
echo ""
echo "📝 Log Files:"
echo "   • MCP Server: /tmp/mcp-server.log"
echo "   • Claude Adapter: /tmp/claude-adapter.log"
echo "   • Roo Adapter: /tmp/roo-adapter.log"
echo "   • Cline Adapter: /tmp/cline-adapter.log"
echo ""
echo "🛑 To stop all services:"
echo "   ./scripts/stop-mcp-system.sh"
echo ""

# Save PIDs for stop script
echo "MCP_PID=$MCP_PID" > /tmp/mcp-pids.sh
echo "CLAUDE_PID=$CLAUDE_PID" >> /tmp/mcp-pids.sh
echo "ROO_PID=$ROO_PID" >> /tmp/mcp-pids.sh
echo "CLINE_PID=$CLINE_PID" >> /tmp/mcp-pids.sh

# Keep script running
echo "Press Ctrl+C to stop all services..."
trap "echo 'Stopping services...'; kill $MCP_PID $CLAUDE_PID $ROO_PID $CLINE_PID 2>/dev/null; exit" INT
wait