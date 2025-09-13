#!/bin/bash
# scripts/mcp_reality_check.sh

echo "================================"
echo "MCP SERVERS REALITY CHECK"
echo "================================"

# Count actual working servers
WORKING=0
TOTAL=0

for dir in mcp_servers/*/; do
    if [ -d "$dir" ]; then
        SERVER_NAME=$(basename "$dir")
        TOTAL=$((TOTAL + 1))
        
        echo -n "Checking $SERVER_NAME: "
        
        # Check if server.py exists
        if [ -f "$dir/server.py" ]; then
            # Try to import it
            if python3 -c "import sys; sys.path.insert(0, '$dir'); import server" 2>/dev/null; then
                echo "✅ Working"
                WORKING=$((WORKING + 1))
            else
                echo "❌ Import failed"
            fi
        else
            echo "❌ No server.py"
        fi
    fi
done

echo ""
echo "Results: $WORKING/$TOTAL servers working"
echo ""

# Show progress
if [ $WORKING -eq 0 ]; then
    echo "⚠️ STOP! Fix basic structure before continuing"
    exit 1
elif [ $WORKING -lt 5 ]; then
    echo "🔧 Progress made, but more work needed"
elif [ $WORKING -lt 8 ]; then
    echo "🎯 Good progress! Most servers working"
else
    echo "🎉 Excellent! Most servers operational"
fi

echo "Next: Run ./scripts/test_all_mcp_servers.py for full testing"
