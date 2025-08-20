#!/bin/bash
# 🤠 SOPHIA AI Swarm Automated Cleanup Script
# Prevents future venv pollution and repository bloat

echo "🤠 SOPHIA AI SWARM CLEANUP INITIATED"
echo "Timestamp: $(date)"

# Remove any venv directories that snuck in
echo "Removing venv pollution..."
find . -type d -name "venv" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".venv" -exec rm -rf {} + 2>/dev/null || true

# Clean backup files
echo "Removing backup files..."
find . -type f -name "*.backup" -delete 2>/dev/null || true
find . -type f -name "*.bak" -delete 2>/dev/null || true
find . -type f -name "*.old" -delete 2>/dev/null || true

# Remove duplicate monitoring reports
echo "Cleaning duplicate reports..."
find . -type f -name "MONITORING_REPORT_*.md" -delete 2>/dev/null || true

# Clean Python cache
echo "Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Check repository size
echo "Repository size after cleanup:"
du -sh .

echo "✅ SOPHIA AI Swarm cleanup complete!"
