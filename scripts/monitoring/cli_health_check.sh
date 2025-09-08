#!/bin/bash
# CLI Health Check - Comprehensive repository and environment verification
# Part of Sophia Intel AI standardized tooling

set -e  # Exit on any error

echo "🔍 Sophia Intel AI - CLI Health Check"
echo "======================================"

HEALTH_STATUS=0
WORKING_DIR="/Users/lynnmusil/sophia-intel-ai"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    HEALTH_STATUS=1
}

error() {
    echo -e "${RED}❌ $1${NC}"
    HEALTH_STATUS=2
}

echo "1. Verifying working directory..."
if [ "$(pwd)" != "$WORKING_DIR" ]; then
    cd "$WORKING_DIR" || { error "Cannot change to $WORKING_DIR"; exit 1; }
    warning "Changed to correct directory: $WORKING_DIR"
else
    success "Working directory is correct: $WORKING_DIR"
fi

echo ""
echo "2. Testing SSH authentication..."
if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    success "SSH authentication to GitHub is working"
else
    error "SSH authentication to GitHub failed"
fi

echo ""
echo "3. Verifying Git configuration..."
GIT_NAME=$(git config user.name 2>/dev/null || echo "NOT_SET")
GIT_EMAIL=$(git config user.email 2>/dev/null || echo "NOT_SET")

if [ "$GIT_NAME" = "scoobyjava" ]; then
    success "Git user.name: $GIT_NAME"
else
    error "Git user.name should be 'scoobyjava', got: $GIT_NAME"
fi

if [ "$GIT_EMAIL" = "musillynn@gmail.com" ]; then
    success "Git user.email: $GIT_EMAIL"
else
    error "Git user.email should be 'musillynn@gmail.com', got: $GIT_EMAIL"
fi

echo ""
echo "4. Verifying Git remote URL..."
REMOTE_URL=$(git remote get-url origin 2>/dev/null || echo "NOT_SET")
EXPECTED_URL="git@github.com:ai-cherry/sophia-intel-ai.git"

if [ "$REMOTE_URL" = "$EXPECTED_URL" ]; then
    success "Git remote URL is correct (SSH-based)"
else
    error "Git remote URL should be '$EXPECTED_URL', got: $REMOTE_URL"
fi

echo ""
echo "5. Checking for virtual environments in repository..."
VENV_COUNT=$(find . -name "pyvenv.cfg" -o -name "bin/activate" -o -name "Scripts/activate.bat" -o -path "*/venv/*" -o -path "*/.venv/*" -type f 2>/dev/null | wc -l)
if [ "$VENV_COUNT" -eq 0 ]; then
    success "No virtual environments found in repository"
else
    error "Found $VENV_COUNT virtual environment files in repository:"
    find . -name "pyvenv.cfg" -o -name "bin/activate" -o -name "Scripts/activate.bat" -o -path "*/venv/*" -o -path "*/.venv/*" -type f 2>/dev/null | head -5
fi

echo ""
echo "6. Checking repository size..."
REPO_SIZE=$(du -sh .git 2>/dev/null | cut -f1)
success "Repository .git size: $REPO_SIZE"

# Convert size to MB for comparison (rough estimate)
if [[ "$REPO_SIZE" == *"G"* ]]; then
    warning "Repository size is quite large (${REPO_SIZE}). Consider cleanup if over 500MB."
fi

echo ""
echo "7. Scanning for large files..."
LARGE_FILES=$(find . -size +10M -not -path "./.git/*" 2>/dev/null | wc -l)
if [ "$LARGE_FILES" -eq 0 ]; then
    success "No large files (>10MB) found outside .git"
else
    warning "Found $LARGE_FILES large files (>10MB):"
    find . -size +10M -not -path "./.git/*" 2>/dev/null | head -5
fi

echo ""
echo "8. Checking Git status..."
if git diff-index --quiet HEAD -- 2>/dev/null; then
    success "Working directory is clean (no uncommitted changes)"
else
    warning "Working directory has uncommitted changes"
    echo "   Use 'git status' to see details"
fi

echo ""
echo "9. Verifying MCP server files..."
if [ -f "mcp_memory_server/server.py" ]; then
    success "MCP memory server found"
else
    error "MCP memory server not found at mcp_memory_server/server.py"
fi

if [ -d "mcp_servers" ]; then
    MCP_COUNT=$(find mcp_servers -name "*.py" | wc -l)
    success "MCP servers directory found with $MCP_COUNT Python files"
else
    error "MCP servers directory not found"
fi

echo ""
echo "10. Checking essential directories..."
for dir in "app/memory" "app/mcp" "scripts" "tmp"; do
    if [ -d "$dir" ]; then
        success "Essential directory exists: $dir"
    else
        error "Essential directory missing: $dir"
    fi
done

echo ""
echo "======================================"
if [ $HEALTH_STATUS -eq 0 ]; then
    echo -e "${GREEN}🎉 All health checks passed!${NC}"
    exit 0
elif [ $HEALTH_STATUS -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Health check completed with warnings${NC}"
    exit 1
else
    echo -e "${RED}❌ Health check failed with errors${NC}"
    exit 2
fi
