#!/bin/bash
# Scout Swarm Test Scenarios

echo "🚀 Starting Sophia Scout Swarm Testing Suite"
echo "============================================="

# Setup environment
set -a
source .env.sophia.local
set +a

# Configure for testing with premium synthesis
export SCOUT_SYNTHESIZER_ENABLED=true
export SCOUT_ENHANCED_SPECIALISTS=true
export SCOUT_SCHEMA_STRICT=true
export SCOUT_PARALLEL_TIMEOUT_MS=120000

# Use Opus for synthesis quality (or GPT-5 if available)
export LLM_SYNTHESIZER_PROVIDER=anthropic
export LLM_SYNTHESIZER_MODEL=claude-3-opus-20240229

# Force a working model setup for quick testing
export LLM_FORCE_PROVIDER=openai
export LLM_FORCE_MODEL=gpt-4o

echo ""
echo "📋 Configuration:"
echo "- Synthesizer: $LLM_SYNTHESIZER_PROVIDER/$LLM_SYNTHESIZER_MODEL"
echo "- Enhanced Specialists: $SCOUT_ENHANCED_SPECIALISTS"
echo "- Schema Strict Mode: $SCOUT_SCHEMA_STRICT"
echo "- Parallel Timeout: ${SCOUT_PARALLEL_TIMEOUT_MS}ms"
echo ""

# Test 1: Security Audit
echo "🔒 Test 1: Security Audit"
echo "-------------------------"
./bin/sophia-run scout --json --approval full-auto \
  --task "Audit authentication, session management, secrets handling, and logging for PII exposure. List high-risk modules and OWASP vulnerabilities." \
  1> test1_security.json 2> test1_security.log

if [ $? -eq 0 ]; then
    echo "✅ Security audit completed"
    echo "Key findings:"
    jq -r '.risks[0:3] | .[] | "  - \(.text // .)"' test1_security.json 2>/dev/null || echo "  (JSON parse issue)"
else
    echo "❌ Security audit failed"
fi
echo ""

# Test 2: Performance Hotspots
echo "⚡ Test 2: Performance Hotspots"
echo "-------------------------------"
./bin/sophia-run scout --json --approval full-auto \
  --task "Identify performance bottlenecks: I/O operations, N+1 queries, caching opportunities, concurrency issues. Propose quick wins with impact estimates." \
  1> test2_performance.json 2> test2_performance.log

if [ $? -eq 0 ]; then
    echo "✅ Performance analysis completed"
    echo "Recommendations:"
    jq -r '.recommendations[0:3] | .[] | "  - \(.)"' test2_performance.json 2>/dev/null || echo "  (JSON parse issue)"
else
    echo "❌ Performance analysis failed"
fi
echo ""

# Test 3: Architecture Mapping
echo "🏗️ Test 3: Architecture & Integrations"
echo "--------------------------------------"
./bin/sophia-run scout --json --approval full-auto \
  --task "Map external services, SDKs, APIs, and data stores. Identify integration points, failure domains, and architectural boundaries. List all third-party dependencies." \
  1> test3_architecture.json 2> test3_architecture.log

if [ $? -eq 0 ]; then
    echo "✅ Architecture mapping completed"
    echo "Integrations found:"
    jq -r '.integrations[0:5] | .[] | "  - \(.)"' test3_architecture.json 2>/dev/null || echo "  (JSON parse issue)"
else
    echo "❌ Architecture mapping failed"
fi
echo ""

# Show metrics
echo "📊 Execution Metrics"
echo "-------------------"
./bin/sophia-run metrics --json --limit 3 | jq '.'

echo ""
echo "🏁 Test Suite Complete!"
echo ""
echo "📝 Results saved to:"
echo "  - test1_security.json"
echo "  - test2_performance.json"
echo "  - test3_architecture.json"
echo ""
echo "To view detailed results:"
echo "  jq '.' test1_security.json"
echo "  jq '.' test2_performance.json"
echo "  jq '.' test3_architecture.json"
