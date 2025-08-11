#!/bin/bash
set -e

echo "Starting repository layout refactoring..."

# 1. Create new directories if they don't exist
mkdir -p orchestrator/workflows
mkdir -p tools

# 2. Move workflows into orchestrator/workflows
# Check if there are files to move
if [ -n "$(ls -A workflows/)" ]; then
    echo "Moving workflows to orchestrator/workflows..."
    git mv workflows/* orchestrator/workflows/
fi

# 3. Move backend/main.py to services and remove backend
if [ -f "backend/main.py" ]; then
    echo "Moving backend/main.py to services/api_server.py..."
    git mv backend/main.py services/api_server.py
fi
echo "Removing backend directory..."
git rm -r backend/

# 4. Consolidate specified scripts into tools and remove the rest
echo "Moving relevant scripts to tools..."
if [ -f "scripts/repo_audit.py" ]; then
    git mv scripts/repo_audit.py tools/
fi
if [ -f "scripts/validate_config.py" ]; then
    git mv scripts/validate_config.py tools/
fi
echo "Removing scripts directory..."
git rm -r scripts/

# 5. Remove other obsolete directories and files
echo "Removing obsolete directories and files..."
if [ -d "frontend" ]; then
    git rm -r frontend/
fi
if [ -d "planning" ]; then
    git rm -r planning/
fi
if [ -d "reports" ]; then
    git rm -r reports/
fi
if [ -f "junk.py" ]; then
    git rm junk.py
fi

# 6. Remove the temporary scripts from previous steps
echo "Removing temporary helper scripts..."
if [ -f "cleanup.sh" ]; then
    git rm cleanup.sh
fi
if [ -f "salvage.sh" ]; then
    git rm salvage.sh
fi

echo "Repository layout refactoring complete."
# The script will be removed manually after execution.