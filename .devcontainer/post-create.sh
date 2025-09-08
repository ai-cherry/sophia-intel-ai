#!/bin/bash
set -euo pipefail

echo "🔧 DevContainer Post-Create Setup..."

# Install Python packages
pip3 install --upgrade pip
pip3 install -r requirements.txt || echo "No requirements.txt found"

# Install MCP components
pip3 install mcp-server || echo "MCP server installation failed"

# Setup GPU monitoring
nvidia-smi -pm 1 || echo "GPU setup failed"

echo "✅ DevContainer post-create setup complete"
