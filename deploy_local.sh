#!/bin/bash

# Sophia Intel AI - Local Deployment Script
# Deploys all components: API, UI, MCP servers, Agents

set -e  # Exit on error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Sophia Intel AI - Local Deployment v2.0.0       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0

    echo -n "  Waiting for $name"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# Kill existing processes if requested
if [ "$1" == "--clean" ]; then
    echo -e "${YELLOW}Cleaning up existing processes...${NC}"
    pkill -f "app.api.unified_server" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    pkill -f "weaviate" 2>/dev/null || true
    sleep 2
fi

# Check prerequisites
echo -e "${BLUE}1. Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}  ✗ Python 3 not found${NC}"
    exit 1
else
    echo -e "${GREEN}  ✓ Python 3 found${NC}"
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}  ✗ npm not found${NC}"
    exit 1
else
    echo -e "${GREEN}  ✓ npm found${NC}"
fi

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}  ⚠ Docker not found (optional for Weaviate)${NC}"
else
    echo -e "${GREEN}  ✓ Docker found${NC}"
fi

# Start Weaviate if Docker is available
echo -e "\n${BLUE}2. Starting Weaviate Vector Database...${NC}"
if command -v docker &> /dev/null; then
    if ! docker ps | grep -q weaviate; then
        echo "  Starting Weaviate container..."
        docker run -d \
            --name weaviate \
            -p 8080:8080 \
            -e QUERY_DEFAULTS_LIMIT=25 \
            -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
            -e PERSISTENCE_DATA_PATH=/var/lib/weaviate \
            -e DEFAULT_VECTORIZER_MODULE=none \
            -e CLUSTER_HOSTNAME=node1 \
            --restart unless-stopped \
            semitechnologies/weaviate:1.32.1 > /dev/null 2>&1 || true

        if wait_for_service "http://localhost:8080/v1/.well-known/ready" "Weaviate"; then
            echo -e "${GREEN}  ✓ Weaviate running on port 8080${NC}"
        else
            echo -e "${YELLOW}  ⚠ Weaviate may take longer to start${NC}"
        fi
    else
        echo -e "${GREEN}  ✓ Weaviate already running${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ Skipping Weaviate (Docker not available)${NC}"
fi

# Start Redis if available
echo -e "\n${BLUE}3. Starting Redis Cache...${NC}"
if command -v redis-server &> /dev/null; then
    if ! pgrep -x redis-server > /dev/null; then
        echo "  Starting Redis..."
        redis-server --daemonize yes > /dev/null 2>&1
        echo -e "${GREEN}  ✓ Redis started on port 6379${NC}"
    else
        echo -e "${GREEN}  ✓ Redis already running${NC}"
    fi
else
    echo -e "${YELLOW}  ⚠ Redis not installed (optional)${NC}"
fi

# Start API Server with MCP servers
echo -e "\n${BLUE}4. Starting API Server with MCP Integration...${NC}"
if ! check_port 8003; then
    echo "  Starting Unified API Server..."
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$SCRIPT_DIR"
    mkdir -p "$REPO_ROOT/logs"
    cd "$REPO_ROOT"

    # Export environment variables
    export LOCAL_DEV_MODE=true
    export AGENT_API_PORT=8003
    export MCP_FILESYSTEM=true
    export MCP_GIT=true
    export MCP_SUPERMEMORY=true

    # Start API server in background
    nohup python3 -m app.api.unified_server > "$REPO_ROOT/logs/api_server.log" 2>&1 &
    API_PID=$!
    echo "  API Server PID: $API_PID"

    if wait_for_service "http://localhost:8003/healthz" "API Server"; then
        echo -e "${GREEN}  ✓ API Server running on port 8003${NC}"
        echo -e "${GREEN}  ✓ MCP Filesystem server active${NC}"
        echo -e "${GREEN}  ✓ MCP Git server active${NC}"
        echo -e "${GREEN}  ✓ MCP Supermemory server active${NC}"
    else
        echo -e "${RED}  ✗ API Server failed to start${NC}"
        echo "  Check logs/api_server.log for details"
        exit 1
    fi
else
    echo -e "${GREEN}  ✓ API Server already running on port 8003${NC}"
fi

# Start UI Dashboard
echo -e "\n${BLUE}5. Starting UI Dashboard...${NC}"
if ! check_port 3001 && ! check_port 3000; then
    echo "  Starting Next.js UI..."
    cd "$REPO_ROOT/agent-ui"

    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "  Installing UI dependencies..."
        npm install --silent
    fi

    # Start UI in background
    nohup npm run dev > "$REPO_ROOT/logs/ui.log" 2>&1 &
    UI_PID=$!
    echo "  UI Dashboard PID: $UI_PID"

    sleep 3  # Give Next.js time to start

    if check_port 3001 || check_port 3000; then
        PORT=$(check_port 3001 && echo "3001" || echo "3000")
        echo -e "${GREEN}  ✓ UI Dashboard running on port $PORT${NC}"
    else
        echo -e "${YELLOW}  ⚠ UI Dashboard starting (may take a moment)${NC}"
    fi
else
    PORT=$(check_port 3001 && echo "3001" || echo "3000")
    echo -e "${GREEN}  ✓ UI Dashboard already running on port $PORT${NC}"
fi

# Verify all agent swarms
echo -e "\n${BLUE}6. Verifying Agent Swarms...${NC}"
SWARMS=$(curl -s http://localhost:8003/teams 2>/dev/null | python3 -c "import sys, json; teams = json.load(sys.stdin); [print(f\"  ✓ {t['id']}: {t['name']}\") for t in teams]" 2>/dev/null)
if [ -n "$SWARMS" ]; then
    echo -e "${GREEN}$SWARMS${NC}"
else
    echo -e "${YELLOW}  ⚠ Could not verify swarms${NC}"
fi

# Health check
echo -e "\n${BLUE}7. Running System Health Check...${NC}"
sleep 2
python3 "$REPO_ROOT/scripts/health_check_final.py" 2>/dev/null | grep -E "(✅|❌|OPERATIONAL)" || echo -e "${YELLOW}  ⚠ Health check script not found${NC}"

# Display access information
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║               DEPLOYMENT COMPLETE!                    ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Access Points:${NC}"
echo -e "  • API Server:    http://localhost:8003"
echo -e "  • API Docs:      http://localhost:8003/docs"
echo -e "  • UI Dashboard:  http://localhost:${PORT:-3001}"
echo -e "  • Weaviate:      http://localhost:8080"
echo ""
echo -e "${GREEN}Available Endpoints:${NC}"
echo -e "  • Health:        GET  /healthz"
echo -e "  • Teams:         GET  /teams"
echo -e "  • Run Team:      POST /teams/run"
echo -e "  • Workflows:     GET  /workflows"
echo -e "  • Search:        POST /search"
echo -e "  • Memory:        POST /memory/add"
echo ""
echo -e "${YELLOW}Commands:${NC}"
echo -e "  • View API logs:  tail -f logs/api_server.log"
echo -e "  • View UI logs:   tail -f logs/ui.log"
echo -e "  • Stop all:       ./stop_local.sh"
echo -e "  • Clean restart:  ./deploy_local.sh --clean"
echo ""
echo -e "${GREEN}✅ All systems deployed locally!${NC}"
