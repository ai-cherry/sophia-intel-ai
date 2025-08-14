#!/bin/bash
# Auto-generated Roo extension reload script
echo "🔄 Forcing Roo extension reload..."

# Method 1: Kill and restart code-server (Codespaces)
if [ "${CODESPACES:-false}" = "true" ]; then
    echo "📍 Codespaces environment detected"
    pkill -f "code-server" 2>/dev/null || true
    sleep 2
    echo "✅ Code-server restarted, page will reload automatically"
else
    echo "📍 Local VSCode environment"
    echo "Please run: Ctrl+Shift+P → 'Developer: Reload Window'"
fi

# Method 2: Clear extension cache directories
ROO_CACHE_DIRS=(
    ~/.vscode-remote/data/User/globalStorage/rooveterinaryinc.roo-cline
    ~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline
    ~/.vscode/extensions/rooveterinaryinc.roo-cline*/data
)

for cache_dir in "${ROO_CACHE_DIRS[@]}"; do
    if [ -d "$cache_dir" ]; then
        echo "🧹 Clearing cache: $cache_dir"
        rm -rf "$cache_dir"/* 2>/dev/null || true
    fi
done

echo "✅ Roo extension cache cleared"
echo "🔄 Extension should reload automatically with new modes"
