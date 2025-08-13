#!/bin/bash
# Health check script for SOPHIA development environment
set -e

echo "🔍 Running SOPHIA Environment Health Check..."

# Check Python version
echo "✓ Checking Python version..."
PYTHON_VERSION=$(python --version)
if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
    echo "  ✅ Python 3 detected: $PYTHON_VERSION"
else
    echo "  ❌ Python 3 not found. Got: $PYTHON_VERSION"
    exit 1
fi

# Check for UV package manager
echo "✓ Checking for UV package manager..."
if command -v uv &> /dev/null; then
    echo "  ✅ UV package manager detected: $(uv --version)"
else
    echo "  ❌ UV not found. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Check for environment setup
echo "✓ Checking Python environment..."
if [ -d ".venv" ]; then
    echo "  ✅ Virtual environment (.venv) found"
else
    echo "  ⚠️ Virtual environment not found. Creating one..."
    uv venv
fi

# Ensure dependencies are installed
echo "✓ Checking dependencies..."
if [ -f "requirements.txt" ]; then
    echo "  ✅ Requirements file found, syncing dependencies..."
    uv pip install -r requirements.txt
else
    echo "  ❌ requirements.txt not found"
    exit 1
fi

# Check for .env file
echo "✓ Checking for environment variables..."
if [ -f ".env.sophia" ]; then
    echo "  ✅ .env.sophia file found"
    # Load but don't display env vars
    export $(grep -v '^#' .env.sophia | xargs) > /dev/null 2>&1
else
    echo "  ⚠️ .env.sophia file not found. Creating template..."
    cat > .env.sophia << EOL
# SOPHIA Environment Configuration
# Core API Keys
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Integration API Keys
GONG_ACCESS_KEY=
ASANA_ACCESS_TOKEN=
LINEAR_API_KEY=
NOTION_API_KEY=

# Database Connections
NEON_DB_URL=
QDRANT_URL=
REDIS_URL=

# Security
SECRET_KEY=
EOL
    echo "  ⚠️ Please fill in the API keys in .env.sophia"
fi

# Check database connections (basic check only)
echo "✓ Checking database connections..."
if [ -n "$NEON_DB_URL" ]; then
    echo "  ✅ Neon DB URL is set"
else 
    echo "  ⚠️ Neon DB URL is not set"
fi

if [ -n "$QDRANT_URL" ]; then
    echo "  ✅ Qdrant URL is set"
else
    echo "  ⚠️ Qdrant URL is not set"
fi

if [ -n "$REDIS_URL" ]; then
    echo "  ✅ Redis URL is set"
else
    echo "  ⚠️ Redis URL is not set"
fi

# Check core API keys (without displaying them)
echo "✓ Checking API keys..."
if [ -n "$OPENAI_API_KEY" ]; then
    echo "  ✅ OpenAI API key is set"
else
    echo "  ⚠️ OpenAI API key is not set"
fi

# Check directory structure
echo "✓ Checking project structure..."
DIRECTORIES=("integrations" "memory" "agents" "apps/api" "apps/dashboard")
for dir in "${DIRECTORIES[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir directory exists"
    else
        echo "  ⚠️ $dir directory does not exist"
    fi
done

echo ""
echo "🎉 Health check completed!"
