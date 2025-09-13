#!/bin/bash

# Fix MCP Servers for Sophia Intel AI
# This script sets up the MCP servers properly for Codex

set -e

SOPHIA_DIR="$HOME/sophia-intel-ai"
cd "$SOPHIA_DIR"

echo "🔧 Fixing MCP Server Configuration for Codex..."

# Create a virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install required Python packages
echo "📚 Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q fastapi uvicorn pydantic python-dotenv httpx

echo "✅ Dependencies installed"
