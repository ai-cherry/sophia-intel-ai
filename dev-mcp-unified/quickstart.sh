#!/bin/bash
# Quick setup and test script for MCP Unified Server

echo "🚀 MCP Unified Server - Quick Setup"
echo "===================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install basic requirements
echo "📚 Installing core dependencies..."
pip install -q --upgrade pip
pip install -q fastapi uvicorn httpx pydantic PyYAML

# Create necessary directories
echo "📁 Creating MCP directories..."
mkdir -p ~/.mcp/cache ~/.mcp/vectors ~/.mcp/logs

# Test imports
echo "🧪 Testing imports..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from core.simple_key_manager import SimpleKeyManager
    from core.mcp_server import UnifiedMCPServer
    print('   ✅ Core modules OK')
except Exception as e:
    print(f'   ❌ Import error: {e}')
"

# Start the server
echo ""
echo "🎯 Starting MCP Server..."
echo "   Port: 3333"
echo "   URL: http://localhost:3333"
echo ""

# Run server in background for testing
python3 -m core.mcp_server &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Test server health
echo "🩺 Testing server health..."
curl -s http://localhost:3333/health | python3 -m json.tool

# Test API keys
echo ""
echo "🔑 Testing API keys..."
curl -s -X POST http://localhost:3333/validate/keys | python3 -m json.tool

echo ""
echo "📝 Usage Examples:"
echo "   ./mcp start              # Start server"
echo "   ./mcp test all           # Test all LLMs"
echo "   ./mcp query --llm claude 'explain this code'"
echo "   ./mcp index ~/projects   # Index your projects"
echo "   ./mcp search 'function'  # Search indexed code"
echo "   ./mcp stop               # Stop server"

echo ""
echo "🎉 Setup complete! Server is running on http://localhost:3333"
echo "   Press Ctrl+C to stop the test server"

# Wait for user to stop
wait $SERVER_PID