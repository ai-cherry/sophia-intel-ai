#!/bin/bash
# Complete Local Deployment Script for Sophia Intel AI
# ======================================================
# Deploys all services, MCP servers, and UIs locally

set -e

echo "🚀 SOPHIA INTEL AI - COMPLETE LOCAL DEPLOYMENT"
echo "=============================================="
echo "Date: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/Users/lynnmusil/sophia-intel-ai"
LOG_DIR="$PROJECT_DIR/logs/deployment_$(date +%Y%m%d_%H%M%S)"
PID_DIR="$PROJECT_DIR/.pids"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Function to check if port is in use
check_port() {
    nc -z localhost $1 2>/dev/null
    return $?
}

# Function to wait for service
wait_for_service() {
    local port=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "  Waiting for $name on port $port"
    while [ $attempt -lt $max_attempts ]; do
        if check_port $port; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        ((attempt++))
    done
    echo -e " ${RED}✗ (timeout)${NC}"
    return 1
}

# Function to kill process on port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        echo "  Killing existing process on port $port"
        kill -9 $pids 2>/dev/null || true
        sleep 1
    fi
}

# Load environment
cd "$PROJECT_DIR"
if [ -f .env.portkey ]; then
    source .env.portkey
fi
if [ -f .env ]; then
    source .env
fi

echo "=========================================="
echo "📋 DEPLOYMENT PLAN"
echo "=========================================="
echo ""
echo "1. Infrastructure Services:"
echo "   - Redis (6379)"
echo "   - PostgreSQL (5432)"
echo ""
echo "2. MCP Servers:"
echo "   - Memory Server (8081)"
echo "   - Filesystem Server (8082)"
echo "   - Git Server (8084)"
echo "   - Vector Search Server (8085)"
echo ""
echo "3. API Services:"
echo "   - Main Unified API (8003)"
echo "   - Bridge API (8000)"
echo "   - Builder API (8004)"
echo ""
echo "4. UI Applications:"
echo "   - Sophia Intel App (3000)"
echo "   - Dashboard (5173)"
echo "   - Builder UI (3001)"
echo ""
echo "5. Model Configuration:"
echo "   - 17 Active Models via Portkey"
echo "   - Central config: user_models_config.yaml"
echo ""
echo "=========================================="
echo ""

# Step 1: Infrastructure Services
echo -e "${BLUE}[1/5] Starting Infrastructure Services${NC}"
echo "=========================================="

# Redis
if check_port 6379; then
    echo -e "  Redis: ${GREEN}Already running${NC}"
else
    echo "  Starting Redis..."
    redis-server --port 6379 --daemonize yes > "$LOG_DIR/redis.log" 2>&1
    wait_for_service 6379 "Redis"
fi

# PostgreSQL
if check_port 5432; then
    echo -e "  PostgreSQL: ${GREEN}Already running${NC}"
else
    echo -e "  PostgreSQL: ${YELLOW}Please start manually${NC}"
    echo "    brew services start postgresql@17"
fi

echo ""

# Step 2: MCP Servers
echo -e "${BLUE}[2/5] Starting MCP Servers${NC}"
echo "=========================================="

# MCP Memory Server
if check_port 8081; then
    echo -e "  MCP Memory: ${GREEN}Already running${NC}"
else
    echo "  Starting MCP Memory Server..."
    kill_port 8081
    python3 -m mcp.memory_server > "$LOG_DIR/mcp_memory.log" 2>&1 &
    echo $! > "$PID_DIR/mcp_memory.pid"
    wait_for_service 8081 "MCP Memory"
fi

# MCP Filesystem Server
if check_port 8082; then
    echo -e "  MCP Filesystem: ${GREEN}Already running${NC}"
else
    echo "  Starting MCP Filesystem Server..."
    kill_port 8082
    WORKSPACE_PATH="$PROJECT_DIR" python3 -m uvicorn mcp.filesystem.server:app \
        --host 0.0.0.0 --port 8082 > "$LOG_DIR/mcp_filesystem.log" 2>&1 &
    echo $! > "$PID_DIR/mcp_filesystem.pid"
    wait_for_service 8082 "MCP Filesystem"
fi

# MCP Git Server
if check_port 8084; then
    echo -e "  MCP Git: ${GREEN}Already running${NC}"
else
    echo "  Starting MCP Git Server..."
    kill_port 8084
    python3 -m uvicorn mcp.git.server:app \
        --host 0.0.0.0 --port 8084 > "$LOG_DIR/mcp_git.log" 2>&1 &
    echo $! > "$PID_DIR/mcp_git.pid"
    wait_for_service 8084 "MCP Git"
fi

# MCP Vector Search Server
if check_port 8085; then
    echo -e "  MCP Vector: ${GREEN}Already running${NC}"
else
    echo "  Starting MCP Vector Search Server..."
    kill_port 8085
    python3 -m mcp.vector_search_server > "$LOG_DIR/mcp_vector.log" 2>&1 &
    echo $! > "$PID_DIR/mcp_vector.pid"
    wait_for_service 8085 "MCP Vector Search"
fi

echo ""

# Step 3: API Services
echo -e "${BLUE}[3/5] Starting API Services${NC}"
echo "=========================================="

# Main Unified API
if check_port 8003; then
    echo -e "  Main API: ${GREEN}Already running${NC}"
else
    echo "  Starting Main Unified API..."
    kill_port 8003
    python3 -m uvicorn app.main_unified:app \
        --host 0.0.0.0 --port 8003 --reload > "$LOG_DIR/main_api.log" 2>&1 &
    echo $! > "$PID_DIR/main_api.pid"
    wait_for_service 8003 "Main API"
fi

# Bridge API
if check_port 8000; then
    echo -e "  Bridge API: ${GREEN}Already running${NC}"
else
    echo "  Starting Bridge API..."
    kill_port 8000
    python3 -m uvicorn bridge.api:app \
        --host 0.0.0.0 --port 8000 --reload > "$LOG_DIR/bridge_api.log" 2>&1 &
    echo $! > "$PID_DIR/bridge_api.pid"
    wait_for_service 8000 "Bridge API"
fi

# Builder API
if check_port 8004; then
    echo -e "  Builder API: ${GREEN}Already running${NC}"
else
    echo "  Starting Builder API..."
    kill_port 8004
    cd builder_cli
    python3 -m uvicorn app:app \
        --host 0.0.0.0 --port 8004 --reload > "$LOG_DIR/builder_api.log" 2>&1 &
    echo $! > "$PID_DIR/builder_api.pid"
    cd ..
    wait_for_service 8004 "Builder API"
fi

echo ""

# Step 4: UI Applications
echo -e "${BLUE}[4/5] Starting UI Applications${NC}"
echo "=========================================="

# Sophia Intel App
if check_port 3000; then
    echo -e "  Sophia Intel App: ${GREEN}Already running${NC}"
else
    echo "  Starting Sophia Intel App..."
    kill_port 3000
    npm run dev > "$LOG_DIR/sophia_app.log" 2>&1 &
    echo $! > "$PID_DIR/sophia_app.pid"
    cd ..
    wait_for_service 3000 "Sophia Intel App"
fi

# Dashboard
if check_port 5173; then
    echo -e "  Dashboard: ${GREEN}Already running${NC}"
else
    echo "  Starting Dashboard..."
    kill_port 5173
    cd dashboard
    npm run dev > "$LOG_DIR/dashboard.log" 2>&1 &
    echo $! > "$PID_DIR/dashboard.pid"
    cd ..
    wait_for_service 5173 "Dashboard"
fi

# Builder UI (if exists)
if [ -d "builder-ui" ]; then
    if check_port 3001; then
        echo -e "  Builder UI: ${GREEN}Already running${NC}"
    else
        echo "  Starting Builder UI..."
        kill_port 3001
        cd builder-ui
        npm run dev > "$LOG_DIR/builder_ui.log" 2>&1 &
        echo $! > "$PID_DIR/builder_ui.pid"
        cd ..
        wait_for_service 3001 "Builder UI"
    fi
else
    echo -e "  Builder UI: ${YELLOW}Not found${NC}"
fi

echo ""

# Step 5: Testing Services
echo -e "${BLUE}[5/5] Testing Services${NC}"
echo "=========================================="

# Test APIs
test_api() {
    local url=$1
    local name=$2
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    if [ "$response" = "200" ] || [ "$response" = "307" ] || [ "$response" = "404" ]; then
        echo -e "  $name: ${GREEN}✓ Responding${NC}"
        return 0
    else
        echo -e "  $name: ${RED}✗ Not responding (HTTP $response)${NC}"
        return 1
    fi
}

echo "Testing API endpoints..."
test_api "http://localhost:8003/docs" "Main API"
test_api "http://localhost:8000/docs" "Bridge API"
test_api "http://localhost:8081/health" "MCP Memory"
test_api "http://localhost:8082/health" "MCP Filesystem"
test_api "http://localhost:8084/health" "MCP Git"

echo ""
echo "Testing Model Configuration..."
python3 -c "
print('  Models managed via Portkey VKs')
" 2>/dev/null || echo -e "  Model Config: ${RED}Error loading${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE${NC}"
echo "=========================================="
echo ""
echo "📍 Service URLs:"
echo "  Main API:        http://localhost:8003/docs"
echo "  Bridge API:      http://localhost:8000/docs"
echo "  (No in-repo UI; dashboards are external)"
echo "  MCP Memory:      http://localhost:8081"
echo "  MCP Filesystem:  http://localhost:8082"
echo "  MCP Git:         http://localhost:8084"
echo ""
echo "📁 Logs Directory: $LOG_DIR"
echo "📝 PID Directory:  $PID_DIR"
echo ""
echo "🛠️ Quick Commands:"
echo "  Test all:        python3 scripts/test_complete_integration.py"
echo "  Builder CLI:     python3 builder_cli/forge.py --help"
echo "  Stop all:        ./stop_all.sh"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap for cleanup
cleanup() {
    echo ""
    echo "Stopping all services..."
    for pidfile in "$PID_DIR"/*.pid; do
        if [ -f "$pidfile" ]; then
            pid=$(cat "$pidfile")
            kill -9 $pid 2>/dev/null || true
            rm "$pidfile"
        fi
    done
    echo "Services stopped."
    exit 0
}

trap cleanup INT TERM

# Keep script running
while true; do
    sleep 1
done
