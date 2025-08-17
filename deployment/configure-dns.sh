#!/bin/bash
# SOPHIA Intel DNS Configuration Script

echo "🌐 Configuring DNS for SOPHIA Intel Production"
echo "=============================================="

# DNSimple API configuration
DNSIMPLE_API_KEY="dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN"
DNSIMPLE_ACCOUNT_ID="placeholder"  # Need actual account ID
DOMAIN="sophia-intel.ai"

# Current working deployments
FRONTEND_URL="www.sophia-intel.ai"
BACKEND_URL="api-placeholder.railway.app"  # Will be updated when backend deploys

echo "1. Configuring www.sophia-intel.ai → $FRONTEND_URL"
# curl -X POST \
#   -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
#   -H "Content-Type: application/json" \
#   -d "{\"name\": \"www\", \"type\": \"CNAME\", \"content\": \"$FRONTEND_URL\", \"ttl\": 300}" \
#   "https://api.dnsimple.com/v2/$DNSIMPLE_ACCOUNT_ID/zones/$DOMAIN/records"

echo "2. Configuring api.sophia-intel.ai → $BACKEND_URL"
# curl -X POST \
#   -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
#   -H "Content-Type: application/json" \
#   -d "{\"name\": \"api\", \"type\": \"CNAME\", \"content\": \"$BACKEND_URL\", \"ttl\": 300}" \
#   "https://api.dnsimple.com/v2/$DNSIMPLE_ACCOUNT_ID/zones/$DOMAIN/records"

echo "✅ DNS configuration prepared (commented out until backend deployment)"
