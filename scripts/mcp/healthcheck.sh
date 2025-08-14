#!/usr/bin/env bash

set -e

echo "=== MCP Servers Health Check ==="

# Check for code_context server
echo "Checking code_context MCP server..."
if python -c "import mcp.code_context.server" 2>/dev/null; then
    echo "✅ code_context server module exists"
else
    echo "❌ code_context server module not found"
fi

# Check for docs_search server
echo "Checking docs_search MCP server..."
if python -c "import mcp.docs_search.server" 2>/dev/null; then
    echo "✅ docs_search server module exists"
else
    echo "❌ docs_search server module not found"
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
