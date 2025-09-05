#!/bin/bash

# AI Rules Cleanup Script
# Removes technical debt and old files according to established rules

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧹 Starting AI Rules Cleanup...${NC}"
echo "======================================"

# Function to safely remove files
safe_remove() {
    local pattern=$1
    local description=$2

    echo -e "${YELLOW}🔍 Looking for ${description}...${NC}"

    # Find files matching pattern
    files=$(find . -name "${pattern}" -type f 2>/dev/null | grep -v ".git" | grep -v "node_modules" || true)

    if [ -n "$files" ]; then
        echo -e "${RED}Found files to remove:${NC}"
        echo "$files"

        # Ask for confirmation in interactive mode
        if [ -t 0 ]; then
            read -p "Remove these files? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                echo "$files" | xargs rm -f
                echo -e "${GREEN}✅ Removed${NC}"
            else
                echo -e "${YELLOW}⏭️  Skipped${NC}"
            fi
        else
            # Non-interactive mode - just remove
            echo "$files" | xargs rm -f
            echo -e "${GREEN}✅ Removed${NC}"
        fi
    else
        echo -e "${GREEN}✅ None found${NC}"
    fi
}

# Remove backup files
safe_remove "*.backup" "backup files"
safe_remove "*_backup.*" "backup files with underscore"
safe_remove "*.old" "old files"
safe_remove "*_old.*" "old files with underscore"

# Remove deprecated files
safe_remove "*_deprecated*" "deprecated files"
safe_remove "*deprecated*" "deprecated files"

# Remove temporary files
safe_remove "*.tmp" "temporary files"
safe_remove "*.temp" "temporary files"
safe_remove "*_temp.*" "temporary files with underscore"
safe_remove "scratch.*" "scratch files"

# Remove Python cache
echo -e "${YELLOW}🔍 Removing Python cache...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo -e "${GREEN}✅ Python cache cleaned${NC}"

# Remove empty files (except __init__.py)
echo -e "${YELLOW}🔍 Looking for empty files...${NC}"
empty_files=$(find . -type f -size 0 ! -name "__init__.py" ! -path "./.git/*" ! -path "./node_modules/*" 2>/dev/null || true)

if [ -n "$empty_files" ]; then
    echo -e "${RED}Found empty files:${NC}"
    echo "$empty_files"

    if [ -t 0 ]; then
        read -p "Remove these empty files? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "$empty_files" | xargs rm -f
            echo -e "${GREEN}✅ Removed${NC}"
        fi
    fi
else
    echo -e "${GREEN}✅ No empty files found${NC}"
fi

# Check for mock implementations
echo -e "${YELLOW}🔍 Checking for mock implementations...${NC}"
mock_files=$(grep -r "class Mock\|class Fake\|class Stub" --include="*.py" --include="*.ts" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=tests 2>/dev/null | cut -d: -f1 | sort -u || true)

if [ -n "$mock_files" ]; then
    echo -e "${RED}⚠️  Warning: Mock implementations found in:${NC}"
    echo "$mock_files"
    echo -e "${YELLOW}Please review and remove mock implementations manually${NC}"
else
    echo -e "${GREEN}✅ No mock implementations found${NC}"
fi

# Check for forbidden phrases
echo -e "${YELLOW}🔍 Checking for forbidden phrases...${NC}"
forbidden_phrases=("should work" "in theory" "placeholder" "hypothetically" "simulated")

found_forbidden=false
for phrase in "${forbidden_phrases[@]}"; do
    results=$(grep -r "$phrase" --include="*.py" --include="*.ts" --include="*.md" --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.ai 2>/dev/null || true)
    if [ -n "$results" ]; then
        echo -e "${RED}⚠️  Found forbidden phrase '${phrase}':${NC}"
        echo "$results" | head -5
        found_forbidden=true
    fi
done

if [ "$found_forbidden" = false ]; then
    echo -e "${GREEN}✅ No forbidden phrases found${NC}"
fi

# Clean git status
echo -e "${YELLOW}🔍 Checking git status...${NC}"
untracked=$(git status --porcelain | grep "^??" || true)

if [ -n "$untracked" ]; then
    echo -e "${YELLOW}⚠️  Untracked files found:${NC}"
    echo "$untracked"
    echo -e "${YELLOW}Consider adding to .gitignore or committing${NC}"
else
    echo -e "${GREEN}✅ Git status clean${NC}"
fi

# Run validation
echo ""
echo -e "${BLUE}🔍 Running validation checks...${NC}"
if python3 .ai/scripts/validate_rules.py; then
    echo -e "${GREEN}✅ Validation passed${NC}"
else
    echo -e "${RED}❌ Validation failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Cleanup complete!${NC}"
echo "======================================"

# Summary
echo -e "${BLUE}📊 Summary:${NC}"
echo "  • Removed backup and old files"
echo "  • Cleaned Python cache"
echo "  • Checked for mocks and forbidden phrases"
echo "  • Validated AI rules compliance"

echo ""
echo -e "${YELLOW}💡 Next steps:${NC}"
echo "  1. Review any warnings above"
echo "  2. Commit changes if satisfied"
echo "  3. Run tests to ensure nothing broke"
