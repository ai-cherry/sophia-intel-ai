#!/bin/bash

echo "=========================================="
echo "🧹 REPOSITORY CLEANUP SCRIPT"
echo "This will remove identified duplicates and fragments"
echo "=========================================="

# Safety check
echo -e "\n⚠️  WARNING: This will permanently delete files!"
echo "Have you backed up the repository? (yes/no)"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborting. Please backup first: git add -A && git commit -m 'Pre-cleanup backup'"
    exit 1
fi

# Create cleanup log
LOG_FILE="cleanup_log_$(date +%Y%m%d_%H%M%S).txt"
echo "Starting cleanup at $(date)" > "$LOG_FILE"

# Function to safely remove with logging
safe_remove() {
    local target=$1
    if [ -e "$target" ]; then
        echo "Removing: $target" | tee -a "$LOG_FILE"
        rm -rf "$target"
    else
        echo "Not found (skipping): $target" | tee -a "$LOG_FILE"
    fi
}

echo -e "\n📁 Phase 1: Removing redundant UI directories..."
# Keep sophia-intel-app and builder-agno-system, remove others
safe_remove "ui"
safe_remove "webui"
safe_remove "agent-ui"
safe_remove "dashboards"
safe_remove "app/agents/ui"
safe_remove "app/factory/ui"

echo -e "\n🔧 Phase 2: Removing duplicate builder implementations..."
# Keep builder_cli, remove builder-cli (hyphenated version)
safe_remove "builder-cli"

echo -e "\n🗑️ Phase 3: Removing abandoned experiments..."
safe_remove "sophia-v2"
safe_remove "codex-launch"
safe_remove "hello-fly"
safe_remove "sophia-v2"
safe_remove "archives"

echo -e "\n🧪 Phase 4: Removing scattered test files..."
safe_remove "test_voice_fix.py"
safe_remove "voice_test_server.py"
safe_remove "test_push.txt"

echo -e "\n📊 Phase 5: Removing old reports and logs..."
# Remove old error reports and test results
find . -name "*_error_report_*.json" -type f -delete 2>/dev/null
find . -name "*_test_results_*.json" -type f -delete 2>/dev/null
find . -name "*_test_report_*.json" -type f -delete 2>/dev/null

echo -e "\n🔗 Phase 6: Consolidating MCP implementations..."
# Keep mcp-unified, remove duplicates
safe_remove "backend/mcp"
safe_remove "app/api/mcp"
safe_remove "mcp-bridge"

echo -e "\n📚 Phase 7: Cleaning documentation..."
# Remove redundant READMEs
safe_remove "README_ARM64_LOCAL.md"
safe_remove "README_UNIFIED.md"
safe_remove "README_SOPHIA.md"
# (removed legacy doc)

echo -e "\n🔌 Phase 8: Removing duplicate startup scripts..."
# Analyze which startup scripts are actually needed
echo "Startup scripts found:" | tee -a "$LOG_FILE"
ls -la start_*.sh launch_*.sh deploy_*.sh 2>/dev/null | tee -a "$LOG_FILE"
echo "Keeping: start_builder_agno.sh, start_sophia_intel.sh, validate_separation.sh"

# Remove redundant ones
safe_remove "start_sophia_unified.sh"
safe_remove "start_voice_properly.sh"
safe_remove "launch_voice_everywhere.sh"
safe_remove "deploy_local_complete.sh"

echo -e "\n🧹 Phase 9: Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo -e "\n📦 Phase 10: Checking for more duplicates..."
# Find duplicate Python files
echo "Python files with duplicate names:" | tee -a "$LOG_FILE"
find . -name "*.py" -type f | xargs -I {} basename {} | sort | uniq -d | head -20 | tee -a "$LOG_FILE"

# Summary
echo -e "\n=========================================="
echo "✅ CLEANUP COMPLETE"
echo "Log saved to: $LOG_FILE"
echo ""
echo "Next steps:"
echo "1. Run: ./validate_separation.sh"
echo "2. Test both apps: ./start_builder_agno.sh and ./start_sophia_intel.sh"
echo "3. Commit changes: git add -A && git commit -m 'Repository cleanup: Remove duplicates'"
echo "=========================================="

# Run validation
echo -e "\nRunning validation check..."
if [ -f "./validate_separation.sh" ]; then
    ./validate_separation.sh
else
    echo "Validation script not found"
fi
