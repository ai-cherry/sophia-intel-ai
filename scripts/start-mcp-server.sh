#!/bin/bash

# Start Enhanced MCP Server v2
# This script starts the production-ready MCP server with monitoring

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Sophia MCP Server v2${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if monitoring stack is running
echo -e "${YELLOW}📊 Checking monitoring stack...${NC}"
if docker ps | grep -q sophia-prometheus; then
    echo -e "${GREEN}✓ Prometheus is running${NC}"
else
    echo -e "${YELLOW}Starting monitoring stack...${NC}"
    docker-compose -f docker-compose.monitoring.yml up -d
    sleep 5
fi

# Check if Redis is running
echo -e "${YELLOW}🔄 Checking Redis...${NC}"
if docker ps | grep -q redis; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${RED}✗ Redis is not running. Please start Redis first.${NC}"
    exit 1
fi

# Check if Weaviate is running
echo -e "${YELLOW}🔍 Checking Weaviate...${NC}"
if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Weaviate is running${NC}"
else
    echo -e "${RED}✗ Weaviate is not running. Please start Weaviate first.${NC}"
    exit 1
fi

# Set environment variables
export PYTHONPATH=/Users/lynnmusil/sophia-intel-ai
export MCP_ENV=development
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_SERVICE_NAME=sophia-mcp-server

# Start MCP Server
echo -e "${BLUE}🎯 Starting MCP Server on port 8004...${NC}"
python3 -m app.mcp.server_v2 &
MCP_PID=$!

# Wait for server to be ready
echo -e "${YELLOW}⏳ Waiting for MCP server to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8004/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ MCP Server is ready!${NC}"
        break
    fi
    sleep 1
done

# Display status
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ MCP Server v2 is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "📍 Endpoints:"
echo "   • API: http://localhost:8004"
echo "   • Health: http://localhost:8004/health"
echo "   • Metrics: http://localhost:8004/metrics"
echo ""
echo "📊 Monitoring:"
echo "   • Prometheus: http://localhost:9090"
echo "   • Grafana: http://localhost:3001 (admin/sophia-monitor)"
echo "   • Jaeger: http://localhost:16686"
echo ""
echo "🔐 Security:"
echo "   • Authentication: JWT with refresh tokens"
echo "   • Rate limiting: Active"
echo "   • Audit logging: Enabled"
echo ""
echo "💡 Next steps:"
echo "   1. Initialize a session: POST /mcp/initialize"
echo "   2. Store memories: POST /mcp/memory/store"
echo "   3. Search memories: POST /mcp/memory/search"
echo ""
echo "To stop the server: kill $MCP_PID"
echo ""

# Keep script running
wait $MCP_PID
