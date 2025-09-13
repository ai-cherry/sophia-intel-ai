#!/bin/bash
# Sophia Daily Startup Script

echo "🚀 Starting Sophia Daily Workflow"
echo "=================================="

# 1. Validate environment
echo "📋 Validating environment..."
sophia-cli validate

# 2. Check for updates
echo "🔄 Checking for updates..."
cd ~/sophia-intel-ai
git fetch origin
git status --short

# 3. Display ready message
echo ""
echo "✅ System ready for development!"
echo "Quick commands:"
echo "  sophia-cli plan <task>     - Plan a feature"
echo "  sophia-cli impl <task>     - Implement code"
echo "  sophia-cli val             - Validate setup"
