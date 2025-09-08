#!/bin/bash
# Stop all Sophia-Artemis services

echo "
╔════════════════════════════════════════════════════════════════╗
║          🛑 Stopping Sophia-Artemis Platform 🛑                ║
╚════════════════════════════════════════════════════════════════╝
"

# Function to stop process by PID
stop_by_pid() {
    local pid=$1
    local name=$2

    if [ ! -z "$pid" ] && kill -0 $pid 2>/dev/null; then
        echo "  Stopping $name (PID: $pid)..."
        kill $pid 2>/dev/null

        # Wait for process to stop (max 5 seconds)
        local count=0
        while kill -0 $pid 2>/dev/null && [ $count -lt 5 ]; do
            sleep 1
            count=$((count + 1))
        done

        # Force kill if still running
        if kill -0 $pid 2>/dev/null; then
            echo "    Force killing $name..."
            kill -9 $pid 2>/dev/null
        fi
    fi
}

# Try to load PIDs from file
if [ -f .pids ]; then
    echo "📋 Using saved PIDs..."
    source .pids

    stop_by_pid "$MCP_PID" "MCP Server"
    stop_by_pid "$API_PID" "API Server"
    stop_by_pid "$SOPHIA_PID" "Sophia Server"
    stop_by_pid "$ARTEMIS_PID" "Artemis Server"
    stop_by_pid "$PERSONA_PID" "Persona Server"

    rm -f .pids
else
    echo "📋 No PID file found, stopping by process name..."
fi

# Fallback: kill by process name
echo ""
echo "🔍 Checking for remaining processes..."

for process in "mcp_server" "unified_server" "sophia_server" "artemis_server" "persona_server" "uvicorn"; do
    if pgrep -f "$process" > /dev/null 2>&1; then
        echo "  Stopping $process..."
        pkill -f "$process" 2>/dev/null
        sleep 1

        # Force kill if still running
        if pgrep -f "$process" > /dev/null 2>&1; then
            echo "    Force killing $process..."
            pkill -9 -f "$process" 2>/dev/null
        fi
    fi
done

# Check specific ports
echo ""
echo "🔍 Checking ports..."
for port in 3333 8006 9000 8001 8085; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  Port $port still in use, cleaning up..."
        lsof -ti:$port | xargs kill -9 2>/dev/null
    else
        echo "  ✅ Port $port is free"
    fi
done

# Stop Redis if configured
if pgrep redis-server > /dev/null 2>&1; then
    echo ""
    echo "🔍 Stopping Redis..."
    redis-cli shutdown 2>/dev/null || true
fi

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "💡 To restart, run: ./deploy_all.sh"
