#!/bin/bash
# Simple test script for Sophia Intel AI

echo "Sophia Intel AI - Quick System Test"
echo "===================================="
echo ""

# 1. Service checks
echo "Service Status:"
./sophia status
echo ""

# 2. Test suite
echo "Running Tests:"
./sophia test
echo ""

# 3. MCP endpoints
echo "Testing MCP Endpoints:"
echo -n "Memory: "
curl -sf http://localhost:8081/health && echo "✅" || echo "❌"
echo -n "Filesystem: "
curl -sf http://localhost:8082/health && echo "✅" || echo "❌"
echo -n "Git: "
curl -sf http://localhost:8084/health && echo "✅" || echo "❌"
echo ""

# 4. Auth bypass
echo "Testing Auth Bypass:"
echo -n "Sessions API: "
curl -sf http://localhost:8081/sessions >/dev/null && echo "✅ No auth required" || echo "❌ Auth required"
echo ""

# 5. OpenCode
echo "Testing OpenCode:"
./dev opencode --version && echo "✅ OpenCode working" || echo "❌ OpenCode not working"
echo ""

echo "===================================="
echo "Test complete!"