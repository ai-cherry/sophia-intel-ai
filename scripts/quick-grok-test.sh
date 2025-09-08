#!/bin/bash
# scripts/quick-grok-test.sh
# Quick one-off Grok test (no compose/network needed)
set -euo pipefail

# Colors for output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}🧪 Testing Grok integration...${NC}"

# Check for XAI API key
XAI_API_KEY="${XAI_API_KEY:-}"

# Try to load from .env if not in environment
if [ -z "$XAI_API_KEY" ] && [ -f ".env" ]; then
    echo -e "${YELLOW}⚠️  XAI_API_KEY not in environment, checking .env file...${NC}"
    if grep -q "XAI_API_KEY=" .env; then
        export XAI_API_KEY="$(grep "XAI_API_KEY=" .env | cut -d'=' -f2- | sed 's/^["'"'"']//;s/["'"'"']$//')"
        echo -e "${GREEN}✅ Found XAI_API_KEY in .env file${NC}"
    fi
fi

# Final check
if [ -z "$XAI_API_KEY" ]; then
    echo -e "${RED}❌ XAI_API_KEY not found in environment or .env file${NC}"
    echo "Please set XAI_API_KEY in your environment or .env file"
    echo "Example: export XAI_API_KEY='your-api-key-here'"
    echo "Or add to .env: XAI_API_KEY=your-api-key-here"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

# Check if requirements files exist
if [ ! -f "requirements/base.txt" ]; then
    echo -e "${RED}❌ requirements/base.txt not found${NC}"
    echo "Please run this script from the sophia-intel-ai root directory"
    exit 1
fi

echo -e "${CYAN}🐳 Running Grok test in Docker container...${NC}"

# Create a simple test task
TEST_TASK="Create a simple Python function that adds two numbers and returns the result"

# Run the test in Docker
docker run --rm -it \
    --name sophia-grok-test \
    -v "$PWD":/workspace \
    -w /workspace \
    -e XAI_API_KEY="$XAI_API_KEY" \
    -e PYTHONPATH=/workspace \
    python:3.11-slim bash -c "
        echo 'Installing dependencies...' &&
        pip install --no-cache-dir -r requirements/base.txt > /dev/null 2>&1 &&
        echo 'Testing Grok integration...' &&
        python3 -c \"
import sys
import os
sys.path.insert(0, '/workspace')

# Test basic import
try:
    from scripts.unified_ai_agents import create_agent_client
    print('✅ Agent client import successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

# Test XAI provider configuration
try:
    client = create_agent_client('xai')
    print('✅ XAI client creation successful')
except Exception as e:
    print(f'❌ XAI client error: {e}')
    sys.exit(1)

print('🎯 Basic Grok integration test completed successfully')
\"
    " 2>/dev/null

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Grok test completed successfully!${NC}"
    echo -e "${YELLOW}💡 Next steps:${NC}"
    echo "  1. Run: make dev-up (starts full multi-agent environment)"
    echo "  2. Run: make dev-shell (enter development shell)"
    echo "  3. Try: python3 scripts/sophia.py agent grok --task 'your task here'"
else
    echo -e "${RED}❌ Grok test failed with exit code $exit_code${NC}"
    echo -e "${YELLOW}💡 Troubleshooting:${NC}"
    echo "  1. Verify your XAI_API_KEY is valid"
    echo "  2. Check your internet connection"
    echo "  3. Try running with debug: DEBUG=1 $0"
    exit $exit_code
fi
