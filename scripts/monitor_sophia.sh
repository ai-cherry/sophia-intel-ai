#!/bin/bash
# Sophia AI Monitoring Script

ENDPOINTS=(
    "https://www.sophia-intel.ai"
    "http://104.171.202.103:8080/api/health"
    "https://mcp.sophia-intel.ai/health"
    "https://ml.sophia-intel.ai/health"
)

echo "🔍 Sophia AI Health Check - $(date)"
echo "=================================="

for endpoint in "${ENDPOINTS[@]}"; do
    echo -n "Checking ${endpoint}... "
    
    if curl -f -s -o /dev/null -w "%{http_code}" "${endpoint}" | grep -q "200\|301\|302"; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
    fi
done

echo ""
echo "SSL Certificate Check:"
echo "======================"

DOMAINS=("www.sophia-intel.ai" "api.sophia-intel.ai" "mcp.sophia-intel.ai" "ml.sophia-intel.ai")

for domain in "${DOMAINS[@]}"; do
    echo -n "Checking SSL for ${domain}... "
    
    if echo | openssl s_client -servername "${domain}" -connect "${domain}:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null; then
        echo "✅ Valid"
    else
        echo "❌ Invalid"
    fi
done

echo ""
echo "Performance Check:"
echo "=================="

response_time=$(curl -o /dev/null -s -w "%{time_total}" "https://www.sophia-intel.ai" 2>/dev/null || echo "N/A")
echo "Response time: ${response_time}s"

echo ""
echo "Monitoring complete - $(date)"
