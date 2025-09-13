#!/bin/bash
# Sophia Directories Cleanup Script
# Removes duplicate sophia directories causing port conflicts
# Generated: September 11, 2025

set -e  # Exit on any error

echo "🧹 SOPHIA DIRECTORIES CLEANUP SCRIPT"
echo "===================================="
echo ""

# Verify we're in the correct directory
if [[ "$(pwd)" != "/Users/lynnmusil/sophia-intel-ai" ]]; then
    echo "❌ ERROR: Must run from /Users/lynnmusil/sophia-intel-ai"
    echo "Current: $(pwd)"
    exit 1
fi

echo "✅ Running from correct directory: $(pwd)"
echo ""

# Show current sophia directories
echo "📊 Current Sophia directories:"
du -sh ~/sophia-* 2>/dev/null || echo "No directories found"
echo ""

# Kill processes from backup directories first
echo "🛑 Stopping processes from backup directories..."
for dir in sophia-consolidation-20250907-201952 sophia-intel-ai-github sophia-rescue-backup sophia-backup-20250909-232621 sophia-services; do
    full_path="$HOME/$dir"
    if [ -d "$full_path" ]; then
        echo "  Stopping processes in $dir..."
        pkill -f "$dir.*npm" 2>/dev/null || echo "    No processes found"
        pkill -f "$dir.*node" 2>/dev/null || echo "    No node processes found"
        pkill -f "$dir.*next" 2>/dev/null || echo "    No next processes found"
    fi
done

# Clean up port conflicts from non-main directories
echo ""
echo "🔧 Cleaning up port conflicts..."
for port in 3000 3001 8005 8006; do
    pids=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pids" ]; then
        for pid in $pids; do
            process_dir=$(ps -p $pid -o command= | grep -o '/Users/lynnmusil/sophia[^/]*' | head -1)
            if [[ "$process_dir" != "/Users/lynnmusil/sophia-intel-ai" ]]; then
                echo "  Killing PID $pid on port $port (from $process_dir)"
                kill -9 $pid 2>/dev/null || echo "    Failed to kill $pid"
            fi
        done
    fi
done

echo ""
echo "📦 Creating archive of recent backup..."

# Archive recent backup before removal
cd ~
if [ -d "sophia-backup-20250909-232621" ]; then
    tar -czf sophia-backup-20250909.tar.gz sophia-backup-20250909-232621/
    echo "✅ Backup archived as ~/sophia-backup-20250909.tar.gz"
else
    echo "⚠️  sophia-backup-20250909-232621 directory not found"
fi

echo ""
echo "🗑️  Removing duplicate directories..."

# Remove backup directories
directories_to_remove=(
    "sophia-consolidation-20250907-201952"
    "sophia-intel-ai-github" 
    "sophia-rescue-backup"
    "sophia-backup-20250909-232621"
    "sophia-services"
)

total_freed=0

for dir in "${directories_to_remove[@]}"; do
    full_path="$HOME/$dir"
    if [ -d "$full_path" ]; then
        # Get size before removal
        size=$(du -sm "$full_path" 2>/dev/null | cut -f1)
        
        echo "  Removing $dir (${size}MB)..."
        rm -rf "$full_path"
        
        if [ ! -d "$full_path" ]; then
            echo "    ✅ Successfully removed"
            total_freed=$((total_freed + size))
        else
            echo "    ❌ Failed to remove"
        fi
    else
        echo "  ⚠️  Directory $dir not found"
    fi
done

echo ""
echo "📊 CLEANUP SUMMARY:"
echo "==================="

# Show remaining directories
echo "📁 Remaining Sophia directories:"
remaining=$(ls -la ~/sophia-* 2>/dev/null | grep "^d" || echo "Only main directory remains")
if [[ "$remaining" == "Only main directory remains" ]]; then
    echo "  ✅ Only main directory: ~/sophia-intel-ai"
else
    echo "$remaining"
fi

# Show freed space
echo ""
echo "💾 Total disk space freed: ${total_freed}MB"

# Show archive created  
if [ -f ~/sophia-backup-20250909.tar.gz ]; then
    archive_size=$(du -sh ~/sophia-backup-20250909.tar.gz | cut -f1)
    echo "📦 Archive created: ~/sophia-backup-20250909.tar.gz ($archive_size)"
fi

echo ""
echo "🔧 Verifying port cleanup..."

# Check for remaining port conflicts
conflict_found=false
for port in 3000 8005; do
    if lsof -ti:$port >/dev/null 2>&1; then
        process_info=$(lsof -ti:$port | xargs ps -p | grep -v PID)
        if echo "$process_info" | grep -v "sophia-intel-ai" >/dev/null; then
            echo "  ⚠️  Port $port still has conflicts: $process_info"
            conflict_found=true
        else
            echo "  ✅ Port $port: Clean (main app only)"
        fi
    else
        echo "  ✅ Port $port: Free"
    fi
done

if [ "$conflict_found" = true ]; then
    echo ""
    echo "⚠️  WARNING: Some port conflicts remain. Run cleanup_processes.sh"
else
    echo ""
    echo "✅ All port conflicts resolved!"
fi

echo ""
echo "🚀 CLEANUP COMPLETE!"
echo "==================="
echo ""
echo "Next steps:"
echo "1. Test application startup: ./scripts/start_apps_properly.sh"
echo "2. Verify both apps load correctly:"
echo "   - Sophia Intel: http://localhost:3000"  
echo "   - Builder Agno: http://localhost:8005"
echo ""
echo "Recovery option if needed:"
echo "   tar -xzf ~/sophia-backup-20250909.tar.gz"
echo ""
echo "✅ Port conflicts should be eliminated!"

# Return to original directory
cd /Users/lynnmusil/sophia-intel-ai