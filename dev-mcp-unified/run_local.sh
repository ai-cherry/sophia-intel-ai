#!/bin/bash
set -euo pipefail

# Start MCP server with environment variables
cd "$HOME/sophia-intel-ai"

# Robust .env loader (supports quoted values; ignores invalid lines)
load_env() {
  local file="$1"
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "${line// }" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"; val="${BASH_REMATCH[2]}"
      # Preserve quoted values; quote if contains pipes/commas/spaces
      if [[ ! "$val" =~ ^\".*\"$ ]] && [[ "$val" == *"|"* || "$val" == *","* || "$val" == *" "* ]]; then
        val="\"$val\""
      fi
      eval export "$key=$val"
    fi
  done < "$file"
}

if [[ -f dev-mcp-unified/.env.local ]]; then
  load_env dev-mcp-unified/.env.local || true
fi

echo "🚀 Starting MCP Server at http://localhost:3333"
echo "📊 Available UIs:"
echo "   - Artemis Multi-Model Chat: file://$HOME/sophia-intel-ai/dev-mcp-unified/ui/multi-chat-six.html"
echo "   - All Tabs: file://$HOME/sophia-intel-ai/dev-mcp-unified/ui/index.html#artemis"
echo "   - Sophia Business: file://$HOME/sophia-intel-ai/dev-mcp-unified/ui/index.html#sophia"
echo ""
echo "📚 API Docs: http://localhost:3333/docs"
echo ""

# Start the server
exec python3 -m uvicorn dev_mcp_unified.core.mcp_server:app --host 127.0.0.1 --port 3333
