#!/bin/bash
# Production Deployment Script for Sophia Intel AI
# Deploys all services with monitoring

set -e  # Exit on error

echo "========================================="
echo "🚀 SOPHIA INTEL AI PRODUCTION DEPLOYMENT"
echo "========================================="
echo "Timestamp: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Environment configuration (no secrets here). Use Fly secrets instead.
export LOCAL_DEV_MODE=false
export PRODUCTION_MODE=true

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start service
start_service() {
    local name=$1
    local port=$2
    local command=$3
    
    echo -e "${YELLOW}Starting $name on port $port...${NC}"
    
    # Check if already running
    if check_port $port; then
        echo -e "${GREEN}✅ $name already running on port $port${NC}"
    else
        # Start the service
        eval "$command" &
        sleep 3
        
        # Verify it started
        if check_port $port; then
            echo -e "${GREEN}✅ $name started successfully on port $port${NC}"
        else
            echo -e "${RED}❌ Failed to start $name on port $port${NC}"
            return 1
        fi
    fi
}

echo ""
echo "1️⃣ Configure secrets in Fly (one-time or when updating):"
echo "   fly secrets set OPENROUTER_API_KEY=*** PORTKEY_API_KEY=*** TOGETHER_API_KEY=*** --app sophia-api"
echo "   fly secrets set ... --app sophia-bridge"
echo "   fly secrets set ... --app sophia-mcp"
echo ""
echo "2️⃣ Deploy services to Fly.io (Fly-first):"
echo "   fly deploy --config fly-unified-api.toml"
echo "   fly deploy --config fly-agno-bridge.toml"
echo "   fly deploy --config fly-mcp-server.toml"
echo "   fly deploy --config fly-vector-store.toml"
echo "   fly deploy --config fly-agent-ui.toml"
echo ""
echo "3️⃣ Post-deploy health checks:"
echo "   curl -f https://sophia-api.fly.dev/healthz" 
echo "   curl -f https://sophia-bridge.fly.dev/healthz"
echo "   curl -f https://sophia-mcp.fly.dev/health"
echo "   curl -f https://sophia-vector.fly.dev/health"
echo ""
echo "Tip: For CI, call the above fly deploy commands per service after running tests."
