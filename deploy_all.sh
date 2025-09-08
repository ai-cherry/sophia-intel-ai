#!/bin/bash
# Comprehensive Deployment Script for Sophia-Artemis Intelligence Platform
# Version 3.0.0 - Unified Architecture

set -e  # Exit on error

echo "
╔════════════════════════════════════════════════════════════════╗
║     🚀 Sophia-Artemis Intelligence Platform Deployment 🚀       ║
║                    Version 3.0.0 - Unified                      ║
╚════════════════════════════════════════════════════════════════╝
"

# Create logs directory
mkdir -p logs

# Load environment variables
if [ -f .env.local ]; then
    source .env.local
else
    echo "⚠️  .env.local not found. Creating default configuration..."
    cat > .env.local << 'EOF'
# API Keys
OPENROUTER_API_KEY=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
PORTKEY_API_KEY=nYraiE8dOR9A1gDwaRNpSSXRkXBc
TOGETHER_API_KEY=together-ai-670469
OPENAI_API_KEY=dummy
ANTHROPIC_API_KEY=dummy

# Server Configuration
LOCAL_DEV_MODE=true
ENVIRONMENT=development
DEBUG=false

# Port Assignments
MCP_PORT=3333
API_PORT=8006
SOPHIA_PORT=9000
ARTEMIS_PORT=8001
PERSONA_PORT=8085

# Database
RBAC_ENABLED=true
DB_TYPE=sqlite
DB_PATH=sophia_rbac.db

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Logging
LOG_LEVEL=INFO
EOF
    source .env.local
fi

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "⚠️  Port $1 is already in use"
        return 1
    fi
    return 0
}

# Function to wait for service
wait_for_service() {
    local port=$1
    local name=$2
    local endpoint=${3:-/health}
    local max_attempts=30
    local attempt=0

    echo -n "  Waiting for $name on port $port"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            echo " ✅"
            return 0
        fi
        echo -n "."
        attempt=$((attempt + 1))
        sleep 1
    done
    echo " ❌"
    echo "  Failed to start $name"
    return 1
}

# Kill existing processes
echo "📋 Checking for existing processes..."
for process in "mcp_server" "unified_server" "sophia_server" "artemis_server" "persona_server"; do
    if pgrep -f "$process" > /dev/null; then
        echo "  Stopping existing $process..."
        pkill -f "$process" 2>/dev/null || true
        sleep 1
    fi
done

# Check port availability
echo ""
echo "🔍 Checking port availability..."
ports_available=true
for port in ${MCP_PORT:-3333} ${API_PORT:-8006} ${SOPHIA_PORT:-9000} ${ARTEMIS_PORT:-8001} ${PERSONA_PORT:-8085}; do
    if ! check_port $port; then
        ports_available=false
    else
        echo "  ✅ Port $port is available"
    fi
done

if [ "$ports_available" = false ]; then
    echo ""
    echo "❌ Some ports are in use. Please free them and try again."
    echo "   You can run: ./stop_all.sh"
    exit 1
fi

# Initialize database if needed
echo ""
echo "💾 Initializing database..."
if [ ! -f "${DB_PATH:-sophia_rbac.db}" ]; then
    echo "  Creating new database..."
    python3.12 migrations/001_rbac_foundation.py up 2>/dev/null || echo "  Database already exists"
else
    echo "  Database exists"
fi

# Start core services
echo ""
echo "🔧 Starting Core Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. MCP Unified Server (Primary Gateway)
echo "1️⃣  MCP Unified Server (port ${MCP_PORT:-3333})"
OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
PORTKEY_API_KEY=$PORTKEY_API_KEY \
TOGETHER_API_KEY=$TOGETHER_API_KEY \
OPENAI_API_KEY=${OPENAI_API_KEY:-dummy} \
LOCAL_DEV_MODE=true \
AGENT_API_PORT=${MCP_PORT:-3333} \
RBAC_ENABLED=${RBAC_ENABLED:-true} \
DB_TYPE=${DB_TYPE:-sqlite} \
DB_PATH=${DB_PATH:-sophia_rbac.db} \
python3.12 -m uvicorn dev_mcp_unified.core.mcp_server:app \
    --host 127.0.0.1 \
    --port ${MCP_PORT:-3333} \
    --reload \
    > logs/mcp_server.log 2>&1 &
MCP_PID=$!

wait_for_service ${MCP_PORT:-3333} "MCP Server" "/docs"

# 2. Unified API Server (Business Logic)
echo "2️⃣  Unified API Server (port ${API_PORT:-8006})"
OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
PORTKEY_API_KEY=$PORTKEY_API_KEY \
TOGETHER_API_KEY=$TOGETHER_API_KEY \
OPENAI_API_KEY=${OPENAI_API_KEY:-dummy} \
LOCAL_DEV_MODE=true \
AGENT_API_PORT=${API_PORT:-8006} \
python3.12 -m app.api.unified_server \
    > logs/api_server.log 2>&1 &
API_PID=$!

wait_for_service ${API_PORT:-8006} "API Server"

# Start application services
echo ""
echo "🚀 Starting Application Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 3. Sophia Business Intelligence Server
echo "3️⃣  Sophia Business Server (port ${SOPHIA_PORT:-9000})"
SOPHIA_PORT=${SOPHIA_PORT:-9000} \
python3.12 sophia_server_standalone.py \
    > logs/sophia_server.log 2>&1 &
SOPHIA_PID=$!

wait_for_service ${SOPHIA_PORT:-9000} "Sophia Server"

# 4. Artemis Technical Operations Server
echo "4️⃣  Artemis Technical Server (port ${ARTEMIS_PORT:-8001})"
ARTEMIS_PORT=${ARTEMIS_PORT:-8001} \
python3.12 artemis_server_standalone.py \
    > logs/artemis_server.log 2>&1 &
ARTEMIS_PID=$!

wait_for_service ${ARTEMIS_PORT:-8001} "Artemis Server"

# 5. Persona Server (Apollo & Athena)
# Note: The persona server file might not exist yet, check first
if [ -f "persona_server_standalone.py" ]; then
    echo "5️⃣  Persona Server (port ${PERSONA_PORT:-8085})"
    AGENT_API_PORT=${PERSONA_PORT:-8085} \
    python3.12 persona_server_standalone.py \
        > logs/persona_server.log 2>&1 &
    PERSONA_PID=$!

    wait_for_service ${PERSONA_PORT:-8085} "Persona Server"
else
    echo "5️⃣  Persona Server (skipped - file not found)"
    PERSONA_PID=""
fi

# Save PIDs for shutdown
cat > .pids << EOF
MCP_PID=$MCP_PID
API_PID=$API_PID
SOPHIA_PID=$SOPHIA_PID
ARTEMIS_PID=$ARTEMIS_PID
PERSONA_PID=$PERSONA_PID
EOF

# Display success message
echo ""
echo "
╔════════════════════════════════════════════════════════════════╗
║                  ✅ DEPLOYMENT SUCCESSFUL! ✅                   ║
╚════════════════════════════════════════════════════════════════╝

🌐 Available Services:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📍 Sophia Intelligence Hub:  http://localhost:${MCP_PORT:-3333}/static/sophia-intelligence-hub.html
📍 Artemis Command Center:   http://localhost:${ARTEMIS_PORT:-8001}/static/command-center.html
📍 API Documentation (MCP):  http://localhost:${MCP_PORT:-3333}/docs
📍 API Documentation (Core): http://localhost:${API_PORT:-8006}/docs
📍 Sophia Business Portal:   http://localhost:${SOPHIA_PORT:-9000}
📍 Artemis Tech Portal:      http://localhost:${ARTEMIS_PORT:-8001}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Quick Commands:
• Health check:     ./health_check.sh
• View all logs:    tail -f logs/*.log
• View MCP logs:    tail -f logs/mcp_server.log
• Stop all:         ./stop_all.sh
• Restart:          ./stop_all.sh && ./deploy_all.sh

📝 Process IDs saved to .pids
"

# Optional: Open browser
if command -v open > /dev/null 2>&1; then
    echo "🌐 Opening Sophia Intelligence Hub in browser..."
    sleep 2
    open "http://localhost:${MCP_PORT:-3333}/static/sophia-intelligence-hub.html"
fi
