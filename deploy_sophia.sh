#!/bin/bash
set -e

echo "🚀 SOPHIA DEPLOYMENT SEQUENCE"
echo "=============================="

# Check environment
if [ ! -f .env ]; then
    echo "❌ Missing .env file"
    exit 1
fi

source .env

# Kill any existing processes
echo "Cleaning up old processes..."
pkill -f "mcp_servers/working_servers.py" 2>/dev/null || true
pkill -f "telemetry_endpoint.py" 2>/dev/null || true
pkill -f "agno_ui_bridge.py" 2>/dev/null || true
pkill -f "production_server.py" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true

# Start Phase 1: Backend
echo ""
echo "PHASE 1: Starting backend services..."
./launch_mcp.sh
sleep 2

# Start Phase 2: Telemetry
echo ""
echo "PHASE 2: Starting telemetry..."
python3 webui/telemetry_endpoint.py >/dev/null 2>&1 &
sleep 1

# Start Phase 3: Production API (FastAPI on :8000)
echo ""
echo "PHASE 3: Starting Production API..."
API_PORT=8000 python3 production_server.py >/dev/null 2>&1 &
sleep 2

# Start Phase 4: UI
echo ""
echo "PHASE 4: Starting UI..."
cd agent-ui
npm run dev >/dev/null 2>&1 &
cd ..
sleep 5

# Run integration test
echo ""
echo "PHASE 5: Running integration test..."
python3 test_integration.py || true

echo ""
echo "================================"
echo "✅ SOPHIA IS FULLY DEPLOYED!"
echo "================================"
echo ""
echo "Access points:"
echo "  UI: http://localhost:3000"
echo "  API: http://localhost:8000"
echo "  Telemetry: http://localhost:5003"
echo "  MCP Servers: 8081-8086"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep running
wait
