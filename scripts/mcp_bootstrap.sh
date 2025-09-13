#!/bin/bash
# MCP Bootstrap - Start MCP servers for Sophia Intel AI
# Part of Sophia Intel AI standardized tooling

set -e

echo "🚀 Starting MCP servers for Sophia Intel AI"
echo "========================================="

# Environment variables with defaults
export BIND_IP=${BIND_IP:-"0.0.0.0"}
export MCP_MEMORY_PORT=${MCP_MEMORY_PORT:-8001}
export REDIS_HOST=${REDIS_HOST:-localhost}
export REDIS_PORT=${REDIS_PORT:-6379}
export QDRANT_URL=${QDRANT_URL:-"http://localhost:6333"}

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

success() { echo -e "${GREEN}✅ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }

# Check if we're in the right directory
EXPECTED_DIR="/Users/lynnmusil/sophia-intel-ai"
if [ "$(pwd)" != "$EXPECTED_DIR" ]; then
    cd "$EXPECTED_DIR" || { error "Cannot change to $EXPECTED_DIR"; exit 1; }
    warning "Changed to correct directory: $EXPECTED_DIR"
fi

echo "Environment configuration:"
echo "  BIND_IP: $BIND_IP"
echo "  MCP_MEMORY_PORT: $MCP_MEMORY_PORT"
echo "  REDIS_HOST: $REDIS_HOST:$REDIS_PORT"
echo "  QDRANT_URL: $QDRANT_URL"
echo ""

# Check for virtual environments (should not exist)
echo "1. Checking for virtual environments..."
VENV_COUNT=$(find . -name "*venv*" -o -name "*env*" -o -name "pyvenv.cfg" -type f 2>/dev/null | wc -l)
if [ "$VENV_COUNT" -eq 0 ]; then
    success "No virtual environments found - using system Python"
else
    error "Found $VENV_COUNT virtual environment files in repository"
    error "Remove virtual environments before starting MCP servers"
    exit 1
fi

# Check Python availability
echo ""
echo "2. Verifying Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    success "Python available: $PYTHON_VERSION"
else
    error "Python3 not found in PATH"
    exit 1
fi

# Check MCP server files
echo ""
echo "3. Verifying MCP server files..."
if [ -f "mcp_memory_server/server.py" ]; then
    success "MCP memory server found"
else
    error "MCP memory server not found at mcp_memory_server/server.py"
    exit 1
fi

# Check dependencies (basic check)
echo ""
echo "4. Checking basic dependencies..."
python3 -c "import fastapi, redis, qdrant_client" 2>/dev/null && success "Basic dependencies available" || {
    warning "Some dependencies may be missing. Install with:"
    echo "  pip3 install fastapi uvicorn redis qdrant-client"
}

# Start Redis check (optional - will work without if already running)
echo ""
echo "5. Checking Redis connection..."
if command -v redis-cli &> /dev/null; then
    if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping 2>/dev/null | grep -q PONG; then
        success "Redis is running and accessible"
    else
        warning "Redis not responding. MCP server will try to connect anyway."
        echo "  To start Redis: redis-server"
    fi
else
    warning "redis-cli not found. Cannot test Redis connection."
fi

# Check if ports are available
echo ""
echo "6. Checking port availability..."
if lsof -i :$MCP_MEMORY_PORT &> /dev/null; then
    warning "Port $MCP_MEMORY_PORT is already in use"
    echo "  Use 'lsof -i :$MCP_MEMORY_PORT' to see what's using it"
else
    success "Port $MCP_MEMORY_PORT is available"
fi

# Create PID directory
mkdir -p .pids

# Start MCP Memory Server
echo ""
echo "7. Starting MCP Memory Server on port $MCP_MEMORY_PORT..."
cd mcp_memory_server
export PORT=$MCP_MEMORY_PORT

# Start the server in background
python3 server.py &
MCP_MEMORY_PID=$!
echo $MCP_MEMORY_PID > ../.pids/mcp_memory.pid

cd ..
success "MCP Memory Server started (PID: $MCP_MEMORY_PID)"

# Wait a moment for startup
sleep 3

# Basic health check
echo ""
echo "8. Performing initial health check..."
if curl -s "http://$BIND_IP:$MCP_MEMORY_PORT/health" > /dev/null 2>&1; then
    success "MCP Memory Server health check passed"
else
    warning "MCP Memory Server health check failed - may still be starting up"
fi

echo ""
echo "========================================="
success "MCP Bootstrap completed!"
echo ""
echo "Services running:"
echo "  MCP Memory Server: http://$BIND_IP:$MCP_MEMORY_PORT"
echo "  Health endpoint: http://$BIND_IP:$MCP_MEMORY_PORT/health"
echo ""
echo "To stop services:"
echo "  kill \$(cat .pids/mcp_memory.pid)"
echo "  or use: pkill -f 'python3 server.py'"
echo ""
echo "Next steps:"
echo "  make mcp-test    # Test MCP functionality"
echo "  make agents-test # Verify AI agents can connect"
