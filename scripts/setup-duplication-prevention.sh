#!/bin/bash

# Setup script for duplication prevention system
# This script installs and configures all components to prevent code duplication

set -e

echo "🚀 Setting up Duplication Prevention System"
echo "=========================================="

# Check Python version
echo "📦 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
if [[ $(echo "$python_version >= 3.8" | bc) -eq 0 ]]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version found"

# Install pre-commit if not installed
echo "📦 Installing pre-commit..."
if ! command -v pre-commit &> /dev/null; then
    pip install pre-commit
    echo "✅ pre-commit installed"
else
    echo "✅ pre-commit already installed"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install pyyaml difflib

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x scripts/check_duplicates.py
chmod +x scripts/check_architecture.py

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type commit-msg
echo "✅ Pre-commit hooks installed"

# Create initial baseline for secret detection
echo "🔐 Creating secrets baseline..."
if [ ! -f .secrets.baseline ]; then
    detect-secrets scan --baseline .secrets.baseline || true
    echo "✅ Secrets baseline created"
else
    echo "✅ Secrets baseline already exists"
fi

# Run initial checks
echo "🔍 Running initial checks..."
echo ""
echo "1️⃣ Checking for duplicates..."
python3 scripts/check_duplicates.py || true
echo ""
echo "2️⃣ Checking architecture compliance..."
python3 scripts/check_architecture.py || true

# Setup Git hooks
echo "🎯 Setting up additional Git hooks..."
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash
# Pre-push hook to prevent pushing violations

echo "🔍 Running pre-push checks..."

# Run duplicate detection
python3 scripts/check_duplicates.py
if [ $? -ne 0 ]; then
    echo "❌ Push blocked: Duplicates detected!"
    echo "Run 'python3 scripts/check_duplicates.py' to see details"
    exit 1
fi

# Run architecture check
python3 scripts/check_architecture.py
if [ $? -ne 0 ]; then
    echo "❌ Push blocked: Architecture violations detected!"
    echo "Run 'python3 scripts/check_architecture.py' to see details"
    exit 1
fi

echo "✅ Pre-push checks passed"
EOF

chmod +x .git/hooks/pre-push
echo "✅ Git hooks configured"

# Display summary
echo ""
echo "✨ Setup Complete!"
echo "=================="
echo ""
echo "📋 Duplication Prevention System is now active with:"
echo "  • Duplicate code detection"
echo "  • Architecture compliance checking"
echo "  • Pre-commit hooks"
echo "  • Pre-push validation"
echo "  • GitHub Actions monitoring"
echo ""
echo "🎯 Next steps:"
echo "  1. Review and fix any violations found above"
echo "  2. Commit changes: git add . && git commit -m 'Setup duplication prevention'"
echo "  3. Test the system: pre-commit run --all-files"
echo ""
echo "📖 Documentation:"
echo "  • Duplication Prevention: DUPLICATION_PREVENTION_SYSTEM.md"
echo "  • Architecture Rules: .architecture.yaml"
echo "  • Pre-commit Config: .pre-commit-config.yaml"
echo ""
echo "💡 Tips:"
echo "  • Run 'pre-commit run --all-files' to check all files"
echo "  • Run 'python3 scripts/check_duplicates.py' to find duplicates"
echo "  • Run 'python3 scripts/check_architecture.py' to check compliance"
echo "  • Edit '.architecture.yaml' to adjust rules"