#!/usr/bin/env bash

set -e

echo "=== SOPHIA Roo Code + MCP Setup ==="
echo

# Make scripts executable
find scripts -name "*.sh" -exec chmod +x {} \;
echo "✅ Made scripts executable"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 is installed"

# Install required Python libraries
echo "Installing required Python libraries..."
pip install -q fastapi uvicorn pydantic whoosh ripgrep-python pytest pytest-asyncio ruff mypy

echo "✅ Installed required Python libraries"

# Create directory structure for MCP servers if needed
mkdir -p mcp/code_context
mkdir -p mcp/docs_search

echo "✅ Created MCP directory structure"

echo
echo "=== Next Steps ==="
echo "1. Configure Roo Code modes:"
echo "   - Open Roo sidebar → Prompts → Project Prompts (⋯) → Edit Project Modes"
echo "   - Ensure it points to .roomodes (YAML)"
echo
echo "2. Enable MCP servers:"
echo "   - Open VS Code MCP view"
echo "   - Start 'code-context' and 'docs-mcp' servers"
echo "   - Add GitHub MCP via OAuth (search 'GitHub' in MCP view)"
echo 
echo "3. Run verification commands:"
echo "   bash scripts/mcp/healthcheck.sh"
echo "   bash scripts/start_all_mcps.sh"
echo "   bash scripts/qa/checks.sh"
echo
echo "See docs/roo_code_setup.md for complete instructions."
