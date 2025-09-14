#!/usr/bin/env bash
set -euo pipefail

# Start or prepare a curated stdio MCP stack based on an example config.
# This does not run blocking stdio servers directly (your IDE/CLI will spawn them).
# It prepares a local config file and prints import/run instructions.

CONFIG_SRC=${1:-"examples/mcp/mcp.local.json"}
CONFIG_OUT=${2:-"./mcp.local.json"}

if [ ! -f "$CONFIG_SRC" ]; then
  echo "Config source not found: $CONFIG_SRC" >&2
  exit 1
fi

cp "$CONFIG_SRC" "$CONFIG_OUT"
echo "[mcp] Wrote local config: $CONFIG_OUT"

cat <<'EOT'
Next steps:

- Cursor: Settings → MCP → Import JSON → select mcp.local.json
- VS Code (MCP extension): Add config → select mcp.local.json
- JetBrains (MCP plugin): Add → select mcp.local.json
- CLI (example): mcp-use-cli fs --config mcp.local.json "refactor main.py"

Notes:
- Many servers use stdio; your IDE/CLI starts them on demand.
- For Docker-based servers, ensure Docker is running and your user can access the socket.
- Set needed env (e.g., GITHUB_TOKEN) in your shell profile before IDE launch.
EOT

exit 0

