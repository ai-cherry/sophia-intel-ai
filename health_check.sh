#!/bin/bash
# Health check script for Sophia Platform

# Load environment if available
# Do not source local env files; environment is provided by ./sophia (.env.master)

# Set default ports if not defined
MCP_PORT=${MCP_PORT:-3333}
API_PORT=${API_PORT:-8006}
SOPHIA_PORT=${SOPHIA_PORT:-9000}
# Legacy port removed
PERSONA_PORT=${PERSONA_PORT:-8085}

echo "
╔════════════════════════════════════════════════════════════════╗
║         🔍 Sophia Platform Health Check 🔍                      ║
╚════════════════════════════════════════════════════════════════╝
"

# Function to check service health
check_service() {
    local port=$1
    local name=$2
    local endpoint=${3:-/health}

    printf "%-30s [Port %5s]: " "$name" "$port"

    # Try to connect to the service
    if timeout 2 curl -s "http://localhost:$port$endpoint" > /dev/null 2>&1; then
        echo "✅ Online"
        return 0
    else
        # Check if port is listening
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo "⚠️  Running but not responding"
        else
            echo "❌ Offline"
        fi
        return 1
    fi
}

# Function to test API endpoint
test_api() {
    local port=$1
    local endpoint=$2
    local method=${3:-GET}
    local data=${4:-}
    local name=$5

    printf "  %-28s: " "$name"

    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST "http://localhost:$port$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    else
        response=$(curl -s "http://localhost:$port$endpoint" 2>/dev/null)
    fi

    if [ ! -z "$response" ] && [ "$response" != "null" ]; then
        # Check for error in response
        if echo "$response" | grep -q "error\|Error\|failed\|Failed"; then
            echo "⚠️  Error response"
        else
            echo "✅ Working"
        fi
        return 0
    else
        echo "❌ No response"
        return 1
    fi
}

# Core Services Check
echo "Core Services Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

services_ok=0
total_services=5

check_service $MCP_PORT "MCP Unified Server" "/docs" && ((services_ok++))
check_service $API_PORT "Unified API Server" "/health" && ((services_ok++))
check_service $SOPHIA_PORT "Sophia Business Server" "/health" && ((services_ok++))
check_service $PERSONA_PORT "Persona Server" "/health" && ((services_ok++)) || echo "  (Optional service)"

echo ""
echo "Service Summary: $services_ok/$total_services services online"
echo ""

# API Endpoints Check
echo "API Endpoints Test:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test MCP endpoints
echo "MCP Server Endpoints:"
test_api $MCP_PORT "/docs" "GET" "" "API Documentation"
test_api $MCP_PORT "/api/swarms/status" "GET" "" "Swarms Status"

# Test API Server endpoints
echo ""
echo "API Server Endpoints:"
test_api $API_PORT "/health" "GET" "" "Health Check"
test_api $API_PORT "/docs" "GET" "" "API Documentation"

# Test Sophia endpoints
if lsof -Pi :$SOPHIA_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo ""
    echo "Sophia Server Endpoints:"
    test_api $SOPHIA_PORT "/health" "GET" "" "Health Check"
    test_api $SOPHIA_PORT "/api/orchestrate" "POST" '{"command":"status","context":{}}' "Orchestration"
fi

# Legacy endpoints removed

# Check UI availability
echo ""
echo "User Interfaces:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

printf "%-30s: " "Sophia Intelligence Hub"
if curl -s "http://localhost:$MCP_PORT/static/sophia-intelligence-hub.html" | grep -q "<html" 2>/dev/null; then
    echo "✅ Available at http://localhost:$MCP_PORT/static/sophia-intelligence-hub.html"
else
    echo "❌ Not available"
fi


# Process Check
echo ""
echo "Process Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

for process in "mcp_server" "unified_server" "sophia_server" "persona_server"; do
    printf "%-30s: " "$process"
    if pgrep -f "$process" > /dev/null 2>&1; then
        pid=$(pgrep -f "$process" | head -1)
        echo "✅ Running (PID: $pid)"
    else
        echo "❌ Not running"
    fi
done

# Resource Usage
echo ""
echo "Resource Usage:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get memory usage
total_mem=0
process_count=0

for process in "mcp_server" "unified_server" "sophia_server" "persona_server"; do
    if pgrep -f "$process" > /dev/null 2>&1; then
        pid=$(pgrep -f "$process" | head -1)
        if [ ! -z "$pid" ]; then
            # Get memory in MB (works on macOS and Linux)
            if command -v ps > /dev/null 2>&1; then
                mem=$(ps -o rss= -p $pid 2>/dev/null | awk '{print int($1/1024)}')
                if [ ! -z "$mem" ]; then
                    printf "%-30s: %4d MB\n" "$process" "$mem"
                    total_mem=$((total_mem + mem))
                    process_count=$((process_count + 1))
                fi
            fi
        fi
    fi
done

if [ $process_count -gt 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    printf "%-30s: %4d MB\n" "Total Memory Usage" "$total_mem"
fi

# Final Status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $services_ok -eq $total_services ]; then
    echo "✅ System Status: All services operational"
elif [ $services_ok -ge 3 ]; then
    echo "⚠️  System Status: Partially operational ($services_ok/$total_services services)"
else
    echo "❌ System Status: Critical issues detected ($services_ok/$total_services services)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Provide recommendations
if [ $services_ok -lt $total_services ]; then
    echo ""
    echo "💡 Recommendations:"
    echo "  • Check logs: tail -f logs/*.log"
    echo "  • Restart services: ./stop_all.sh && ./deploy_all.sh"
    echo "  • Check environment: ensure <repo>/.env.master exists (chmod 600)"
fi
