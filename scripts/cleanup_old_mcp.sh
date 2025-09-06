#!/bin/bash
# CLEANUP OLD MCP SCRIPTS
# Removes all duplicate/garbage MCP startup scripts

echo "🧹 CLEANING UP OLD MCP SCRIPTS"
echo "=============================="

# Change to repo directory
cd "$(dirname "$0")/.."

# List of OLD scripts to remove (keeping only the master ones)
OLD_SCRIPTS=(
    "scripts/start-mcp-server.sh"
    "scripts/stop-mcp-system.sh"
    "scripts/start-mcp-system.sh"
    "scripts/mcp_consolidation.py"
    "start_mcp.sh"
    "stop_mcp.sh"
    "mcp_startup.sh"
    "run_mcp.py"
)

echo "📋 Removing old/duplicate MCP scripts..."
for script in "${OLD_SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        echo "  ❌ Removing: $script"
        rm -f "$script"
    fi
done

echo ""
echo "✅ CLEANUP COMPLETE"
echo ""
echo "📌 OFFICIAL MCP SCRIPTS (USE THESE ONLY):"
echo "  1. scripts/mcp_master_startup.py - Main startup controller"
echo "  2. scripts/start_all_mcp.sh - Quick start script"
echo "  3. scripts/mcp_health_monitor.py - Health monitoring"
echo "  4. scripts/cleanup_old_mcp.sh - This cleanup script"
echo ""
echo "🚀 To start MCP servers, run:"
echo "   ./scripts/start_all_mcp.sh"
echo ""
