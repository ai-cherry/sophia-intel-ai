#!/bin/bash
echo '🔄 Restarting everything fresh...'

# Kill any existing processes
pkill -f 'next-server' 2>/dev/null || true
pkill -f 'simple_server' 2>/dev/null || true

# Clear all caches
rm -rf .next/
export PATH=/opt/homebrew/bin:$PATH
pnpm store prune

# Start backend
cd ../
python3 simple_server_7777.py &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Start UI
cd ui
pnpm dev --port 3000 &
UI_PID=$!

echo '✅ Backend PID:' $BACKEND_PID
echo '✅ UI PID:' $UI_PID
echo '🌐 UI: http://localhost:3000'
echo '⚡ Backend: http://localhost:7777'

# Test connection
curl -s http://localhost:7777/healthz

