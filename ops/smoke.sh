#!/bin/bash
set -e

echo "🧪 SOPHIA Intel Smoke Tests"
echo "=========================="

API_BASE=${API_BASE:-http://localhost:8000}

echo "1. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" -o /tmp/health.json "$API_BASE/health")
if [ "$HEALTH_RESPONSE" = "200" ]; then
    echo "   ✅ Health check passed"
    cat /tmp/health.json | jq .
else
    echo "   ❌ Health check failed (HTTP $HEALTH_RESPONSE)"
    exit 1
fi

echo ""
echo "✅ All smoke tests passed!"
