#!/bin/bash
set -euo pipefail

echo "🚨 EMERGENCY ARCHITECTURAL CLEANUP 🚨"
echo "======================================"

# 1. BACKUP FIRST
echo "📦 Creating backup..."
tar -czf ../sophia-backup-$(date +%Y%m%d-%H%M%S).tar.gz . --exclude node_modules --exclude .git

# 2. DELETE REDUNDANT ORCHESTRATORS (Keep only 3)
echo "🗑️  Removing redundant orchestrators..."
find . -name "*orchestrat*.py" -type f | grep -v "app/orchestrators/base.py" | grep -v "app/orchestrators/sophia_orchestrator.py" | head -20

# 3. CONSOLIDATE MCP SERVERS
echo "🗑️  Consolidating MCP servers to 3..."
echo "Keeping: Memory (8081), FS (8082), Git (8084)"

# 4. REMOVE LEGACY
[ -f "sophia_unified_server.py" ] && rm -f sophia_unified_server.py && echo "✅ Deleted legacy server"

echo "✅ Run with 'bash scripts/emergency/cleanup.sh' after review"
