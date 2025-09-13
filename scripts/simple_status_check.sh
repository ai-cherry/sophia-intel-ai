#!/bin/bash

# Simple Sophia AI Status Check
# No complex dependencies, just basic curl commands

echo "🔍 Sophia AI Simple Status Check"
echo "================================"
echo ""

# Function to check endpoint
check_endpoint() {
    local url=$1
    local name=$2
    
    echo -n "Checking $name... "
    
    if curl -s --max-time 10 "$url" > /dev/null 2>&1; then
        echo "✅ UP"
        return 0
    else
        echo "❌ DOWN"
        return 1
    fi
}

# Check main endpoints
echo "📊 Endpoint Status:"
check_endpoint "http://www.sophia-intel.ai/health" "Main Health"
check_endpoint "http://www.sophia-intel.ai/" "Main Site"
check_endpoint "http://api.sophia-intel.ai/health" "API Health"

echo ""

# Check SSL status (simple)
echo "🔒 SSL Status:"
echo -n "HTTPS www.sophia-intel.ai... "
if curl -s --max-time 10 https://www.sophia-intel.ai > /dev/null 2>&1; then
    echo "✅ SSL OK"
else
    echo "❌ SSL Issue (expected - needs certificate fix)"
fi

echo ""

# Simple system info
echo "💻 System Info:"
echo "Date: $(date)"
echo "Uptime: $(uptime -p 2>/dev/null || uptime)"

# Check if monitoring is running
echo ""
echo "📈 Monitoring Status:"
if pgrep -f "simple_monitoring.py" > /dev/null; then
    echo "✅ Monitoring script is running"
else
    echo "⚠️  Monitoring script not running"
    echo "   To start: python3 scripts/simple_monitoring.py &"
fi

echo ""
echo "✅ Status check complete!"
echo "💡 This is a simple check - no complex tools required"

