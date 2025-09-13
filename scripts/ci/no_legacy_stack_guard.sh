#!/usr/bin/env bash
# Fail CI if legacy coding UI, legacy MCP servers, or forbidden env patterns exist
set -euo pipefail

err() { echo "[GUARD] $*" >&2; }

# 1) No in-repo coding UI
if [ -d "builder-agno-system" ]; then
  err "builder-agno-system/ must not exist in BI repo"
  exit 1
fi

# 2) Only canonical MCP servers
if [ -f "mcp/filesystem.py" ]; then
  err "Legacy mcp/filesystem.py found; use mcp/filesystem/server.py"
  exit 1
fi
if [ -f "mcp/git_server.py" ]; then
  err "Legacy mcp/git_server.py found; use mcp/git/server.py"
  exit 1
fi

# 3) Single env source: no dotenv or ~/.config fallbacks
if rg -n "dotenv|from\s+dotenv|load_dotenv|~/.config|expanduser\(.*\.config" --hidden -S app mcp backend services -g '!**/requirements*' -g '!**/*.lock' 2>/dev/null | rg -v "README|md$|yaml$" -nq; then
  err "Found forbidden dotenv or ~/.config usages; only ./.env.master via ./sophia"
  rg -n "dotenv|from\s+dotenv|load_dotenv|~/.config|expanduser\(.*\.config" --hidden -S app mcp backend services -g '!**/requirements*' -g '!**/*.lock' 2>/dev/null | rg -v "README|md$|yaml$" | head -20 >&2
  exit 1
fi

echo "[GUARD] OK: no legacy stack artifacts detected"
