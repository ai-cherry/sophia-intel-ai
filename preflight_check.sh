#!/bin/bash
set -e
echo "Pre-deployment checks..."

# Check Python
if python3 --version >/dev/null 2>&1; then echo "✓ Python installed"; else echo "✗ Python missing"; fi

# Check Node
if node --version >/dev/null 2>&1; then echo "✓ Node installed"; else echo "✗ Node missing"; fi

# Check .env exists
if [ -f .env ]; then echo "✓ .env file exists"; else echo "✗ .env missing"; fi

# Check key directories exist
if [ -d agent-ui ]; then echo "✓ agent-ui directory"; else echo "✗ agent-ui missing"; fi
if [ -d agno_core ]; then echo "✓ agno_core directory"; else echo "✗ agno_core missing"; fi
if [ -d mcp_servers ]; then echo "✓ mcp_servers directory"; else echo "✗ mcp_servers missing"; fi

# Check for port conflicts
for port in 3000 5003 8000 8081 8082 8084 8085 8086; do
  if lsof -i:$port >/dev/null 2>&1; then echo "⚠ Port $port in use"; else echo "✓ Port $port available"; fi
done

