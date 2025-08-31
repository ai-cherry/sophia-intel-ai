#!/bin/bash

# Sophia Intel AI - Local Development Startup Script
# Starts all services with real API connections

set -e

echo "=========================================="
echo "🚀 Sophia Intel AI - Local Deployment"
echo "=========================================="

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ Error: .env.local file not found"
    echo "Please create .env.local with your API keys"
    exit 1
fi

# Load environment variables
export $(cat .env.local | grep -v '^#' | xargs)

# Check required API keys
if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "dummy-key" ]; then
    echo "❌ Error: OPENAI_API_KEY not set or is dummy"
    exit 1
fi

if [ -z "$PORTKEY_API_KEY" ]; then
    echo "❌ Error: PORTKEY_API_KEY not set"
    exit 1
fi

echo "✅ Environment variables loaded"

# Start API server
echo "🌐 Starting API server on port 8000..."
PORTKEY_API_KEY=$PORTKEY_API_KEY \
OPENROUTER_API_KEY=$OPENROUTER_API_KEY \
LOCAL_DEV_MODE=true \
AGENT_API_PORT=8000 \
python3 -m app.api.unified_server &

# Wait for API to start
echo "⏳ Waiting for API server..."
sleep 5

# Start proxy bridge
echo "🌉 Starting proxy bridge on port 7777..."
python3 proxy_bridge.py &

# Wait for services
sleep 3

# Start UIs
echo "🎨 Starting UIs..."
(cd ui && npm run dev -- --port 3100) &
(cd agent-ui && npm run dev -- --port 3200) &

sleep 5

echo ""
echo "=========================================="
echo "✨ Sophia Intel AI is running!"
echo "=========================================="
echo "  • Main UI: http://localhost:3100"
echo "  • Agent UI: http://localhost:3200"
echo "  • API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="

# Keep running
wait
