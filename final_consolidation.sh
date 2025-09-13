#!/bin/bash

echo "FINAL THOUGHTFUL CONSOLIDATION"
echo "==============================="
echo ""

# Backup everything first
BACKUP="$HOME/final-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP"
cp -r ~/sophia-intel-ai "$BACKUP/sophia-intel-ai-before"
cp -r ~/sophia-main-rescue "$BACKUP/sophia-main-copy"

echo "Step 1: Analyzing what sophia-main has that we need"
echo "----------------------------------------------------"

cd ~/sophia-main-rescue

# Check for valuable Python files
echo "Checking Python files in sophia-main..."
for file in $(find . -name '*.py' -type f | grep -v '.git'); do
    if [ ! -f ~/sophia-intel-ai/$file ]; then
        echo "  NEW FILE: $file"
        # Copy it to sophia-intel-ai
        mkdir -p ~/sophia-intel-ai/$(dirname $file)
        cp $file ~/sophia-intel-ai/$file
    else
        # File exists in both - compare them
        MAIN_SIZE=$(wc -l < $file)
        INTEL_SIZE=$(wc -l < ~/sophia-intel-ai/$file)
        if [ $MAIN_SIZE -gt $((INTEL_SIZE + 10)) ]; then
            echo "  LARGER in sophia-main: $file ($MAIN_SIZE vs $INTEL_SIZE lines)"
            # Save both versions for manual review
            cp $file "$BACKUP/review_$(basename $file).from_main"
            cp ~/sophia-intel-ai/$file "$BACKUP/review_$(basename $file).from_intel"
        fi
    fi
done

echo ""
echo "Step 2: Ensuring CLI Structure"
echo "-------------------------------"

cd ~/sophia-intel-ai

# Ensure all directories exist
mkdir -p app/{core,cli,mcp,memory,agents/{sophia,sophia},ingestion,utils}
mkdir -p tests configs docs

# Check if we have the main components
echo "Verifying core components:"
[ -f app/mcp/server_v2.py ] && echo "  ✓ MCP server exists" || echo "  ✗ MCP server missing"
[ -f app/core/unified_memory.py ] && echo "  ✓ Unified memory exists" || echo "  ✗ Unified memory missing"
[ -f app/core/base_agent.py ] && echo "  ✓ Base agent exists" || echo "  ✗ Base agent missing"
[ -f app/cli/unified_agent_cli.py ] && echo "  ✓ Unified CLI exists" || echo "  ✗ Unified CLI missing"

echo ""
echo "Step 3: Creating .gitignore if needed"
echo "--------------------------------------"

if [ ! -f .gitignore ]; then
    cat > .gitignore << 'GITIGNORE'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Logs
*.log
logs/

# Environment
.env
.env.local
*.env

# Test coverage
htmlcov/
.coverage
.pytest_cache/

# Build
build/
dist/
*.egg-info/

# Backup files
*.backup
*.old
*_backup.py
*_old.py
GITIGNORE
    echo "Created .gitignore"
fi

echo ""
echo "Step 4: Summary"
echo "---------------"
echo "Total Python files: $(find . -name '*.py' | wc -l)"
echo "Total directories: $(find app -type d | wc -l)"
echo "Untracked files: $(git ls-files --others --exclude-standard | wc -l)"
echo "Modified files: $(git diff --name-only | wc -l)"

echo ""
echo "Consolidation complete!"
echo "Backup saved to: $BACKUP"
echo ""
echo "Review any conflicts in: $BACKUP/review_*"
