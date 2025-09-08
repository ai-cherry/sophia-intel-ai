#!/bin/bash
# scripts/test_real_apis.sh
# Test real APIs only - no mocks

set -e

echo "================================"
echo "REAL API TEST (No Mocks)"
echo "================================"

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️ No .env file found. Copy from .env.example first:"
    echo "   cp .env.example .env"
    exit 1
fi

# Function to test API
test_api() {
    local name=$1
    local key_var=$2
    local test_cmd=$3
    
    echo -n "$name: "
    
    if [ -z "${!key_var}" ]; then
        echo "❌ No API key (feature disabled)"
        return 1
    fi
    
    if eval "$test_cmd" > /dev/null 2>&1; then
        echo "✅ Working"
        return 0
    else
        echo "⚠️ Key present but API call failed"
        return 1
    fi
}

# Test each API with real calls
echo "Testing API connectivity..."
echo

# GitHub API
test_api "GitHub" "GITHUB_TOKEN" \
    "curl -s -f -H 'Authorization: token $GITHUB_TOKEN' https://api.github.com/user"

# OpenAI API
test_api "OpenAI" "OPENAI_API_KEY" \
    "curl -s -f -H 'Authorization: Bearer $OPENAI_API_KEY' https://api.openai.com/v1/models"

# HubSpot API
test_api "HubSpot" "HUBSPOT_API_KEY" \
    "curl -s -f 'https://api.hubapi.com/crm/v3/objects/contacts?limit=1&hapikey=$HUBSPOT_API_KEY'"

# Anthropic API (if available)
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo -n "Anthropic: "
    if curl -s -f -H "x-api-key: $ANTHROPIC_API_KEY" -H "anthropic-version: 2023-06-01" \
        -H "content-type: application/json" \
        -d '{"model":"claude-3-sonnet-20240229","max_tokens":5,"messages":[{"role":"user","content":"Hi"}]}' \
        https://api.anthropic.com/v1/messages > /dev/null 2>&1; then
        echo "✅ Working"
    else
        echo "⚠️ Key present but API call failed"
    fi
else
    echo "Anthropic: ❌ No API key (feature disabled)"
fi

# Database connections
echo
echo "Testing database connections..."

# PostgreSQL
if [ -n "$DATABASE_URL" ]; then
    echo -n "PostgreSQL: "
    if python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.close()
    print('✅ Connected')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        echo "✅ Connected"
    else
        echo "❌ Connection failed"
    fi
else
    echo "PostgreSQL: ❌ No DATABASE_URL configured"
fi

# Redis
if [ -n "$REDIS_URL" ]; then
    echo -n "Redis: "
    if python3 -c "
import redis
import os
try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print('✅ Connected')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
" 2>/dev/null; then
        echo "✅ Connected"
    else
        echo "❌ Connection failed"
    fi
else
    echo "Redis: ❌ No REDIS_URL configured"
fi

# Qdrant
if [ -n "$QDRANT_URL" ]; then
    echo -n "Qdrant: "
    if curl -s -f "$QDRANT_URL/collections" > /dev/null 2>&1; then
        echo "✅ Connected"
    else
        echo "❌ Connection failed"
    fi
else
    echo "Qdrant: ❌ No QDRANT_URL configured"
fi

echo
echo "================================"
echo "FEATURE AVAILABILITY"
echo "================================"

# Show what will work
python3 << 'EOF'
import os
import sys

# Add backend to path
sys.path.append('backend')

try:
    from services.feature_flags import FeatureFlags
    
    flags = FeatureFlags()
    status = flags.get_feature_status()
    
    print(f"\n📊 Feature Status: {status['enabled_count']}/{status['total_features']} enabled")
    
    print("\n✅ Enabled Features:")
    for feature in sorted(status['enabled']):
        print(f"  • {feature.replace('_', ' ').title()}")
    
    if status['disabled']:
        print("\n⬜ Disabled Features:")
        for feature in sorted(status['disabled']):
            print(f"  • {feature.replace('_', ' ').title()}")
    
    if status['missing_critical']:
        print(f"\n🚨 Missing Critical APIs:")
        for api in status['missing_critical']:
            print(f"  • {api}")
        print("\n💡 Get free keys: ./scripts/setup_free_api_keys.sh")
    else:
        print(f"\n🎉 All critical APIs configured!")
    
    if status['missing_apis'] and not status['missing_critical']:
        print(f"\n💡 Optional APIs available:")
        for api in status['missing_apis']:
            if api not in status['missing_critical']:
                print(f"  • {api}")

except ImportError as e:
    print(f"❌ Could not import feature flags: {e}")
    print("   Make sure backend dependencies are installed")
except Exception as e:
    print(f"❌ Error checking features: {e}")
EOF

echo
echo "================================"
echo "NEXT STEPS"
echo "================================"

echo "1. ✅ APIs tested - no mocks used"
echo "2. 🔧 Features auto-disabled for missing keys"
echo "3. 💡 Get missing free keys: ./scripts/setup_free_api_keys.sh"
echo "4. 🚀 Start services: ./scripts/sophia.sh start-backend"
echo "5. 🧪 Run integration tests: python -m pytest tests/"

echo
echo "🎯 Remember: No mocks = No confusion for AI agents!"

