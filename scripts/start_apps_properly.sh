#!/bin/bash
echo "🚀 Starting applications from /Users/lynnmusil/sophia-intel-ai (CORRECT directory)..."

# Clean up first
./scripts/cleanup_processes.sh

echo ""
echo "📍 Current directory: $(pwd)"
echo "📂 Sophia directories on system:"
ls -la ~/sophia-* | head -20

echo ""
echo "🏗️ Starting Sophia Intel App (port 3000)..."
cd sophia-intel-app 
if [ -f package.json ]; then
    echo "✅ Found package.json in sophia-intel-app"
    npm run dev &
    SOPHIA_PID=$!
    echo "🚀 Sophia Intel App started with PID: $SOPHIA_PID"
else
    echo "❌ No package.json found in sophia-intel-app"
fi

# Go back to root
cd ..

# Wait for port to be available
echo "⏳ Waiting 10 seconds for Sophia app to start..."
sleep 10

echo ""
echo "🏗️ Starting Builder Agno System (port 8005)..."
cd builder-agno-system
if [ -f package.json ]; then
    echo "✅ Found package.json in builder-agno-system"
    npm run dev -- --port 8005 &
    BUILDER_PID=$!
    echo "🚀 Builder Agno System started with PID: $BUILDER_PID"
else
    echo "❌ No package.json found in builder-agno-system"
fi

# Go back to root
cd ..

echo ""
echo "✅ Applications started from CORRECT directory:"
echo "  📍 Working directory: $(pwd)"
echo "  🌐 Sophia Intel: http://localhost:3000"
echo "  🌐 Builder Agno: http://localhost:8005"

echo ""
echo "🔍 Final port status:"
for port in 3000 8005; do
    sleep 2
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  ✅ Port $port: OCCUPIED (app running)"
    else
        echo "  ❌ Port $port: FREE (app not started)"
    fi
done