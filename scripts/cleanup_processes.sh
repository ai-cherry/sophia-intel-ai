#!/bin/bash
echo "🧹 Cleaning up conflicting processes from multiple sophia directories..."

# Kill processes on conflicting ports
for port in 3000 3001 8005 8006; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid on port $port"
        kill -9 $pid 2>/dev/null || echo "Failed to kill $pid"
    fi
done

# Clean up npm/node processes
echo "Cleaning up npm dev processes..."
pkill -f "npm.*dev" 2>/dev/null || echo "No npm dev processes found"
pkill -f "next.*dev" 2>/dev/null || echo "No next dev processes found"
pkill -f "vite.*3000" 2>/dev/null || echo "No vite processes found"

# Clean up any pnpm processes
pkill -f "pnpm.*dev" 2>/dev/null || echo "No pnpm processes found"

echo "✅ Process cleanup complete"
echo "📊 Current port status:"
for port in 3000 3001 8005 8006; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  Port $port: OCCUPIED"
    else
        echo "  Port $port: FREE"
    fi
done