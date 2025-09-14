#!/usr/bin/env bash
# Registers the repo's stdio MCP server (fs_memory_stdio.py) in:
# - Cline (Cursor) MCP settings
# - Claude Desktop (Roo) MCP settings
# Also sanity-checks that the stdio server runs and responds to "initialize".
set -euo pipefail

# Config
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_FS_STDIO_ABS="/Users/lynnmusil/sophia-intel-ai/tools/mcp/fs_memory_stdio.py"
FS_STDIO="${FS_STDIO:-$DEFAULT_FS_STDIO_ABS}"

# Settings file paths
CLINE_SETTINGS="$HOME/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json"
CLAUDE_SETTINGS="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Preflight checks
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found on PATH. Install Python 3 and retry." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq not found on PATH. Install via: brew install jq" >&2
  exit 1
fi

if [ ! -f "$FS_STDIO" ]; then
  echo "ERROR: MCP stdio server not found at: $FS_STDIO" >&2
  echo "Set FS_STDIO to the correct path and retry, e.g.:" >&2
  echo "FS_STDIO=\"$REPO_ROOT/tools/mcp/fs_memory_stdio.py\" bash ./register_mcp_clients.sh" >&2
  exit 1
fi

# Sanity-check the stdio server responds to initialize
echo "Sanity-checking stdio MCP server..."
TEST_OUTPUT="$(printf '%s\n' '{"id":"1","method":"initialize"}' | python3 "$FS_STDIO")" || {
  echo "ERROR: Failed to execute stdio MCP server." >&2
  exit 1
}
if ! echo "$TEST_OUTPUT" | jq -e '.result.server == "fs-memory-stdio"' >/dev/null 2>&1; then
  echo "ERROR: Unexpected stdio response. Output was:" >&2
  echo "$TEST_OUTPUT" >&2
  exit 1
fi
echo "OK: stdio MCP server responded with fs-memory-stdio."

ensure_json() {
  local file="$1"
  local dir
  dir="$(dirname "$file")"
  mkdir -p "$dir"
  # If file missing, create minimal structure
  if [ ! -f "$file" ]; then
    echo '{"mcpServers":{}}' > "$file"
    return
  fi
  # If file exists but is invalid JSON, back up and reset
  if ! jq -e . "$file" >/dev/null 2>&1; then
    cp "$file" "$file.bak.$(date +%s)"
    echo '{"mcpServers":{}}' > "$file"
  fi
  # If file exists but lacks mcpServers root, add it without destroying other keys
  if ! jq -e 'has("mcpServers")' "$file" >/dev/null 2>&1; then
    local tmp="$file.tmp.$$"
    jq '. + {"mcpServers":{}}' "$file" > "$tmp" && mv "$tmp" "$file"
  fi
}

merge_server() {
  local file="$1"
  local tmp="$file.tmp.$$"
  # Merge/overwrite mcpServers.fs-memory with our stdio config
  jq --arg cmd "python3" \
     --arg arg "$FS_STDIO" \
     '.mcpServers["fs-memory"] = {
        "command": $cmd,
        "args": [$arg],
        "env": {},
        "disabled": false,
        "autoApprove": []
      }' \
     "$file" > "$tmp"
  mv "$tmp" "$file"
}

echo "Registering MCP stdio server in Cline (Cursor) settings..."
ensure_json "$CLINE_SETTINGS"
merge_server "$CLINE_SETTINGS"
echo "Updated: $CLINE_SETTINGS"

echo "Registering MCP stdio server in Claude Desktop (Roo) settings..."
ensure_json "$CLAUDE_SETTINGS"
merge_server "$CLAUDE_SETTINGS"
echo "Updated: $CLAUDE_SETTINGS"

cat <<EONOTE

Registration complete.

Next steps:
1) Restart Cursor (Cline) and Claude Desktop / Roo.
2) In a fresh chat, you should see a connected MCP server "fs-memory".
3) Try tools (examples):
   - fs.list {"path":"."}
   - fs.read {"path":"README.md"}
   - git.status {}
   - repo.index {"root":".","max_bytes_per_file":50000}
   - memory.add {"topic":"note","content":"hello","tags":["demo"]}

If you want to change the path, re-run with:
FS_STDIO="$REPO_ROOT/tools/mcp/fs_memory_stdio.py" bash ./register_mcp_clients.sh
EONOTE
