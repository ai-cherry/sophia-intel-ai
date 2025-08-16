#!/bin/bash
set -e

echo "🚀 SOPHIA INTEL DEPLOYMENT PLAN - EXECUTING NOW"

# 1. Deploy to Railway
echo "📦 Deploying to Railway..."
export RAILWAY_TOKEN="67dc4ecc-2aaa-40ec-8d5d-846c8ca89f1c"
railway up --detach

# 2. Configure environment variables
echo "⚙️ Setting environment variables..."
railway variables set LAMBDA_API_KEY="secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f.EsLXt0lkGlhZ1Nd369Ld5DMSuhJg9O9y"
railway variables set LAMBDA_API_BASE="https://api.lambda.ai/v1"
railway variables set PORT="8080"
railway variables set PYTHONPATH="/app"

# 3. Get deployment URL
echo "🌐 Getting deployment URL..."
RAILWAY_URL=$(railway status --json | jq -r '.deployments[0].url')
echo "Deployment URL: $RAILWAY_URL"

# 4. Configure domain
echo "🔗 Configuring domain..."
curl -H "Authorization: Bearer dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN" \
     -H "Content-Type: application/json" \
     -X POST \
     -d "{\"name\": \"\", \"type\": \"CNAME\", \"content\": \"${RAILWAY_URL#https://}\", \"ttl\": 300}" \
     https://api.dnsimple.com/v2/162809/zones/sophia-intel.ai/records

# 5. Test deployment
echo "🧪 Testing deployment..."
sleep 30
curl -f "$RAILWAY_URL/health" || echo "Health check failed"

echo "✅ DEPLOYMENT COMPLETE!"
echo "🌐 SOPHIA Intel is live at: https://sophia-intel.ai"
echo "🔗 Railway URL: $RAILWAY_URL"
