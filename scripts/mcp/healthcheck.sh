#!/usr/bin/env bash
set -euo pipefail

echo "=== MCP Servers Health Check ==="

# Check code_context server health via --health flag
echo "Checking code_context MCP server..."
if python mcp/code_context/server.py --health | grep -q '"status": "healthy"'; then
    echo "✅ code_context MCP server is healthy"
else
    echo "❌ code_context MCP server is unhealthy"
    exit 1
fi

# Check config file for docs-mcp
if [ -f "mcp/docs-mcp.config.json" ]; then
    echo "✅ docs-mcp.config.json exists"
else
    echo "❌ docs-mcp.config.json not found"
fi

# Check VS Code MCP config
if [ -f ".vscode/mcp.json" ]; then
    echo "✅ .vscode/mcp.json exists"
else
    echo "❌ .vscode/mcp.json not found"
fi

echo
echo "If any checks failed, run the following:"
echo "1. bash scripts/setup.sh to install dependencies"
echo "2. Make sure MCP server implementations exist in:"
echo "   - mcp/code_context/server.py"
echo "   - mcp/docs_search/server.py"
