#!/bin/bash
# Quick setup script for Artemis Scout swarm environment

set -e

echo "🚀 Artemis Scout Environment Setup"
echo "=================================="

# Check if .env.artemis.local exists
if [ ! -f ".env.artemis.local" ]; then
    echo "❌ Missing .env.artemis.local file"
    echo "Please create it with your API keys"
    exit 1
fi

# Load environment variables
echo "📦 Loading environment variables..."
source .env.artemis.local

# Check critical keys
echo "🔑 Checking API keys..."
MISSING_KEYS=""

if [ -z "$PORTKEY_API_KEY" ]; then
    MISSING_KEYS="$MISSING_KEYS PORTKEY_API_KEY"
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    MISSING_KEYS="$MISSING_KEYS OPENROUTER_API_KEY"
fi

if [ -z "$WEAVIATE_API_KEY" ]; then
    echo "⚠️  Warning: WEAVIATE_API_KEY not set (vector search will be limited)"
fi

if [ -n "$MISSING_KEYS" ]; then
    echo "❌ Missing required keys:$MISSING_KEYS"
    echo "Please add them to .env.artemis.local"
    exit 1
fi

# Start minimal services
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.artemis.yml up -d redis

# Optional: Start Weaviate if configured
if [ -n "$WEAVIATE_URL" ] && [ -n "$WEAVIATE_API_KEY" ]; then
    echo "🔮 Starting Weaviate (vector store)..."
    docker-compose -f docker-compose.artemis.yml up -d weaviate

    # Wait for Weaviate to be ready
    echo "⏳ Waiting for Weaviate to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
            echo "✅ Weaviate is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "⚠️  Weaviate not ready after 30s (continuing anyway)"
        fi
        sleep 1
    done
else
    echo "ℹ️  Skipping Weaviate (not configured)"
fi

# Check Redis
echo "🔍 Checking Redis..."
if docker exec artemis-redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis not responding"
    exit 1
fi

# Run readiness check
echo "🏥 Running readiness check..."
python3 scripts/scout_readiness_check.py

# Quick test
echo "🧪 Running quick test..."
if python3 -c "from app.mcp.clients.stdio_client import StdioMCPClient; print('✅ MCP client imports OK')"; then
    echo "✅ Basic imports working"
else
    echo "❌ Import errors - check your Python environment"
    exit 1
fi

echo ""
echo "✨ Environment ready!"
echo ""
echo "Next steps:"
echo "  1. Run scout: ./bin/artemis-run scout --task 'Analyze repository'"
echo "  2. Check readiness: ./bin/artemis-run scout --check"
echo "  3. Run benchmarks: python3 tests/artemis/benchmark_swarms.py"
echo "  4. Run tests: pytest tests/artemis/test_scout_integration.py"
echo ""
echo "Feature flags (optional):"
echo "  export SCOUT_PREFETCH_ENABLED=true     # Enable prefetch (default: true)"
echo "  export SCOUT_PREFETCH_MAX_FILES=20     # Max files to prefetch"
echo "  export SCOUT_PREFETCH_MAX_BYTES=50000  # Max bytes per file"
echo ""
