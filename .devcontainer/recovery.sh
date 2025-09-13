#!/bin/bash
# Sophia AI V9.7 - Emergency Recovery Script
# This script can fix common workspace issues and restore functionality

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[RECOVERY]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

# Recovery start
log_header "Sophia AI V9.7 Emergency Recovery"
log_info "Starting recovery at $(date)"
log_info "Current directory: $(pwd)"
log_info "User: $(whoami)"

# Phase 1: Workspace Directory Recovery
log_header "Phase 1: Workspace Directory Recovery"

# Ensure we're in the right place
if [ ! -d "/workspace" ]; then
    log_warning "Workspace directory missing, creating..."
    sudo mkdir -p /workspace || {
        log_error "Failed to create workspace directory"
        exit 1
    }
    log_success "Workspace directory created"
fi

# Fix permissions
log_info "Fixing workspace permissions..."
sudo chown -R vscode:vscode /workspace 2>/dev/null || sudo chown -R $(whoami):$(whoami) /workspace
sudo chmod -R 755 /workspace
log_success "Workspace permissions fixed"

# Create essential directories
log_info "Creating essential directory structure..."
mkdir -p /workspace/{logs,data,.cache,.venv,backend,frontend,scripts,tests}
mkdir -p /workspace/.cache/{uv,pip,npm}
mkdir -p /workspace/logs
log_success "Directory structure created"

# Phase 2: Python Environment Recovery
log_header "Phase 2: Python Environment Recovery"

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    log_error "Python not found! This requires manual intervention."
    log_info "Try running: sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv"
    exit 1
fi

# Remove corrupted virtual environment
VENV_PATH="/workspace/.venv"
if [ -d "$VENV_PATH" ]; then
    log_info "Checking virtual environment..."
    if ! source "$VENV_PATH/bin/activate" 2>/dev/null; then
        log_warning "Virtual environment corrupted, recreating..."
        rm -rf "$VENV_PATH"
    else
        deactivate 2>/dev/null || true
        log_success "Virtual environment is functional"
    fi
fi

# Create new virtual environment if needed
if [ ! -d "$VENV_PATH" ]; then
    log_info "Creating new virtual environment..."
    python3 -m venv "$VENV_PATH" || python -m venv "$VENV_PATH" || {
        log_error "Failed to create virtual environment"
        exit 1
    }
    log_success "Virtual environment created"
fi

# Test virtual environment
source "$VENV_PATH/bin/activate" || {
    log_error "Failed to activate virtual environment"
    exit 1
}

log_success "Virtual environment activated"
log_info "Python: $(which python)"
log_info "Pip: $(which pip)"

# Phase 3: Dependencies Recovery
log_header "Phase 3: Dependencies Recovery"

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel || {
    log_warning "Failed to upgrade pip, continuing..."
}

# Install essential packages
log_info "Installing essential packages..."
pip install black pylint pytest || {
    log_warning "Failed to install some essential packages"
}

# Install requirements if available
if [ -f "/workspace/requirements.txt" ]; then
    log_info "Installing from requirements.txt..."
    pip install -r /workspace/requirements.txt || {
        log_warning "Failed to install some requirements, continuing..."
    }
else
    log_info "No requirements.txt found, skipping..."
fi

# Phase 4: Service Recovery
log_header "Phase 4: Service Recovery"

# Check Docker
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        log_success "Docker is available"
        
        # Clean up any problematic containers
        log_info "Cleaning up Docker containers..."
        docker stop postgres redis qdrant neo4j 2>/dev/null || true
        docker rm postgres redis qdrant neo4j 2>/dev/null || true
        
        log_success "Docker containers cleaned up"
    else
        log_warning "Docker daemon not running"
    fi
else
    log_warning "Docker not available"
fi

# Phase 5: File System Recovery
log_header "Phase 5: File System Recovery"

# Fix common file permission issues
log_info "Fixing file permissions..."
find /workspace -type d -exec chmod 755 {} \; 2>/dev/null || true
find /workspace -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
find /workspace -type f -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true

# Create essential files if missing
if [ ! -f "/workspace/.gitignore" ]; then
    log_info "Creating .gitignore..."
    cat > /workspace/.gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
*.log
logs/

# Cache
.cache/
*.cache

# OS
.DS_Store
Thumbs.db

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local
EOF
    log_success ".gitignore created"
fi

# Phase 6: Health Validation
log_header "Phase 6: Health Validation"

# Validate workspace
VALIDATION_ERRORS=()

# Check workspace directory
if [ ! -d "/workspace" ] || [ ! -w "/workspace" ]; then
    VALIDATION_ERRORS+=("Workspace directory not accessible")
fi

# Check Python
if ! python --version &> /dev/null; then
    VALIDATION_ERRORS+=("Python not working")
fi

# Check virtual environment
if [ ! -f "/workspace/.venv/bin/activate" ]; then
    VALIDATION_ERRORS+=("Virtual environment missing")
fi

# Check essential directories
for dir in logs data .cache; do
    if [ ! -d "/workspace/$dir" ]; then
        VALIDATION_ERRORS+=("Directory $dir missing")
    fi
done

# Report validation results
if [ ${#VALIDATION_ERRORS[@]} -eq 0 ]; then
    log_success "All validation checks passed!"
else
    log_warning "Validation issues found:"
    for error in "${VALIDATION_ERRORS[@]}"; do
        log_error "  • $error"
    done
fi

# Phase 7: Recovery Summary
log_header "Recovery Summary"

echo -e "\n${GREEN}🔧 Recovery Process Complete!${NC}\n"

echo -e "${CYAN}📁 Workspace:${NC} /workspace"
echo -e "${CYAN}🐍 Python:${NC} $(python --version 2>&1)"
echo -e "${CYAN}📦 Virtual Environment:${NC} /workspace/.venv"
echo -e "${CYAN}👤 User:${NC} $(whoami)"
echo -e "${CYAN}🔑 Permissions:${NC} $(ls -ld /workspace | awk '{print $1, $3, $4}')"

echo -e "\n${YELLOW}📝 Next Steps:${NC}"
echo -e "  1. Run: source /workspace/.venv/bin/activate"
echo -e "  2. Test: python --version"
echo -e "  3. Install dependencies: pip install -r requirements.txt"
echo -e "  4. Start services: bash .devcontainer/startup.sh"

if [ ${#VALIDATION_ERRORS[@]} -gt 0 ]; then
    echo -e "\n${RED}⚠️  Manual intervention required for:${NC}"
    for error in "${VALIDATION_ERRORS[@]}"; do
        echo -e "  • $error"
    done
fi

echo -e "\n${GREEN}✅ Recovery completed at $(date)${NC}"

# Deactivate virtual environment
deactivate 2>/dev/null || true

log_success "Recovery script finished"

