#!/bin/bash
# setup_cli.sh - Install the 'sophia' CLI wrapper (local machine)
set -e

cat > sophia << 'EOF'
#!/usr/bin/env bash
# Sophia CLI - ARM64 Native wrapper
set -e
ROOT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
cd "$ROOT_DIR"

# Ensure venv Python is used when available
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi

exec "$PY" "$ROOT_DIR/sophia_cli.py" "$@"
EOF

chmod +x sophia

echo "You can symlink this wrapper for global access (requires sudo):"
echo "  sudo ln -sf $(pwd)/sophia /usr/local/bin/sophia"
echo "✅ CLI wrapper created: $(pwd)/sophia"

