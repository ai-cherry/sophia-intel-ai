#!/bin/bash

echo "🔍 Testing UI Connection to API..."
echo "================================="

# Test API directly
echo -e "\n1️⃣ Testing API on port 8003:"
if curl -s http://localhost:8003/healthz | grep -q '"status":"ok"'; then
    echo "   ✅ API Health: OK"
else
    echo "   ❌ API Health: FAILED"
fi

if curl -s http://localhost:8003/teams | grep -q '"id"'; then
    echo "   ✅ Teams endpoint: OK"
else
    echo "   ❌ Teams endpoint: FAILED"
fi

if curl -s http://localhost:8003/agents | grep -q '"id"'; then
    echo "   ✅ Agents endpoint: OK"
else
    echo "   ❌ Agents endpoint: FAILED"
fi

# Check UI is running
echo -e "\n2️⃣ Testing UI on port 3000:"
if curl -s http://localhost:3000 | grep -q "Agent UI"; then
    echo "   ✅ UI is running"
else
    echo "   ❌ UI not accessible"
fi

# Test from browser perspective (CORS)
echo -e "\n3️⃣ Testing CORS headers:"
CORS_RESPONSE=$(curl -s -I -X OPTIONS http://localhost:8003/teams \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" 2>/dev/null | grep -i "access-control")

if [ -n "$CORS_RESPONSE" ]; then
    echo "   ✅ CORS headers present:"
    echo "   $CORS_RESPONSE"
else
    echo "   ⚠️  No CORS headers (may cause browser issues)"
fi

# Show what's in localStorage
echo -e "\n4️⃣ To check browser storage:"
echo "   Open http://localhost:3000 in browser"
echo "   Open DevTools Console (F12)"
echo "   Run: localStorage.getItem('endpoint-storage')"
echo ""
echo "5️⃣ To fix connection issues:"
echo "   Visit: http://localhost:3000/fix-and-redirect.html"
echo ""
echo "================================="