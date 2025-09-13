#!/bin/bash

echo "🧪 Multi-Tool Integration Test"
echo "=============================="
echo ""

# Check tools
echo "Installed Tools:"
command -v claude &> /dev/null && echo "✓ Claude Code"
command -v opencode &> /dev/null && echo "✓ Opencode" 
command -v codex &> /dev/null && echo "✓ Codex"
command -v cursor &> /dev/null && echo "✓ Cursor"
echo ""

# Check MCP servers
echo "MCP Servers:"
curl -s http://localhost:8081/health 2>/dev/null && echo "✓ Memory Server (8081)" || echo "✗ Memory Server"
curl -s http://localhost:8082/health 2>/dev/null && echo "✓ Filesystem Server (8082)" || echo "✗ Filesystem Server"
curl -s http://localhost:8084/health 2>/dev/null && echo "✓ Git Server (8084)" || echo "✗ Git Server"
echo ""

# Check environment
echo "Environment:"
[ -n "$ANTHROPIC_API_KEY" ] && echo "✓ ANTHROPIC_API_KEY set" || echo "✗ ANTHROPIC_API_KEY missing"
[ -n "$OPENAI_API_KEY" ] && echo "✓ OPENAI_API_KEY set" || echo "✗ OPENAI_API_KEY missing"
echo ""

# Check configs
echo "Configuration Files:"
[ -f CLAUDE.md ] && echo "✓ CLAUDE.md"
[ -f rules.yaml ] && echo "✓ rules.yaml"
[ -f .cursorrules ] && echo "✓ .cursorrules"
[ -f .env ] && echo "✓ .env"
echo ""

# Test basic operation
echo "Testing basic operations..."
echo "def test(): return 'Multi-tool ready!'" > test_multi.py
python3 test_multi.py 2>/dev/null && echo "✓ Python execution works"
rm -f test_multi.py
