#!/bin/bash

echo "=========================================="
echo "📊 SOPHIA INTEL APP"
echo "UI Port: 3000"
echo "API Port: 8003"
echo "Purpose: PayReady Business Intelligence"
echo "=========================================="

# Check if sophia-intel-app exists
if [ ! -d "sophia-intel-app" ]; then
    echo "❌ Error: sophia-intel-app directory not found!"
    echo "Please ensure sophia-intel-app is properly set up."
    exit 1
fi

# Start the API server
echo "🚀 Starting Sophia Intel API on http://localhost:8003"
cd app
python -m uvicorn api.unified_server:app --host 0.0.0.0 --port 8003 --reload &
API_PID=$!
echo "API PID: $API_PID"

# Start the UI
echo "🚀 Starting Sophia Intel UI on http://localhost:3000"
cd ../sophia-intel-app
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Sophia Intel dependencies..."
    npm install
fi
npm run dev &
UI_PID=$!
echo "UI PID: $UI_PID"

# Function to handle shutdown
cleanup() {
    echo "Shutting down Sophia Intel..."
    kill $API_PID 2>/dev/null
    kill $UI_PID 2>/dev/null
    exit 0
}

# Set up trap for clean shutdown
trap cleanup SIGINT SIGTERM

# Wait for processes
wait