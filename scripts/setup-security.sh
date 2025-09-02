#!/bin/bash

# Security Setup Script for Sophia Intel AI
# Installs pre-commit hooks and security tools

set -e

echo "🔒 Setting up Security Tools for Sophia Intel AI"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! python3 --version | grep -E "3\.(11|12)" > /dev/null; then
    echo -e "${RED}Error: Python 3.11+ is required${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python version OK${NC}"

# Install pre-commit
echo -e "${YELLOW}Installing pre-commit...${NC}"
pip install --upgrade pre-commit

# Install security tools
echo -e "${YELLOW}Installing security scanning tools...${NC}"
pip install --upgrade \
    detect-secrets \
    bandit \
    safety \
    pip-audit \
    semgrep

# Install Gitleaks
echo -e "${YELLOW}Installing Gitleaks...${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        brew install gitleaks
    else
        echo -e "${YELLOW}Homebrew not found. Download Gitleaks from: https://github.com/gitleaks/gitleaks/releases${NC}"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    wget -q https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz
    tar -xzf gitleaks_8.18.0_linux_x64.tar.gz
    sudo mv gitleaks /usr/local/bin/
    rm gitleaks_8.18.0_linux_x64.tar.gz
fi

# Install TruffleHog
echo -e "${YELLOW}Installing TruffleHog...${NC}"
pip install truffleHog3

# Set up pre-commit hooks
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
pre-commit install
pre-commit install --hook-type commit-msg

# Create secrets baseline
echo -e "${YELLOW}Creating secrets baseline...${NC}"
detect-secrets scan --baseline .secrets.baseline

# Run initial security scan
echo -e "${YELLOW}Running initial security scan...${NC}"
echo ""

# Secret scanning
echo "1. Scanning for secrets..."
if detect-secrets scan --baseline .secrets.baseline | grep -q "no secrets detected"; then
    echo -e "${GREEN}✓ No secrets detected${NC}"
else
    echo -e "${YELLOW}⚠ Potential secrets found. Review .secrets.baseline${NC}"
fi

# Dependency scanning
echo "2. Scanning dependencies..."
safety check --json --continue-on-error > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Dependency scan complete${NC}"

# Python security linting
echo "3. Running Bandit security linter..."
bandit -r app/ --skip B101 -f json > /dev/null 2>&1 || true
echo -e "${GREEN}✓ Security linting complete${NC}"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}🎉 Security setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review and commit .secrets.baseline file"
echo "2. Run 'pre-commit run --all-files' to test hooks"
echo "3. Configure CI/CD with the GitHub Actions workflow"
echo ""
echo "Security commands:"
echo "  pre-commit run --all-files    # Run all security checks"
echo "  detect-secrets scan           # Scan for secrets"
echo "  bandit -r app/                # Run security linter"
echo "  safety check                  # Check dependencies"
echo ""