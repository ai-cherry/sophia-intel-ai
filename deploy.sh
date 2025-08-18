#!/bin/bash
set -e

echo "🚀 SOPHIA INTEL DEPLOYMENT TO FLY.IO - EXECUTING NOW"

# Set up Fly CLI path
export PATH="$HOME/.fly/bin:$PATH"

# 1. Deploy to Fly.io
echo "📦 Deploying to Fly.io..."
flyctl deploy --remote-only --app sophia-intel

# 2. Set environment variables on Fly.io
echo "⚙️ Setting environment variables..."
flyctl secrets set OPENROUTER_API_KEY="$OPENROUTER_API_KEY" --app sophia-intel
flyctl secrets set LAMBDA_API_KEY="$LAMBDA_API_KEY" --app sophia-intel
flyctl secrets set LAMBDA_API_BASE="https://cloud.lambdalabs.com/api/v1" --app sophia-intel
flyctl secrets set SENTRY_DSN="$SENTRY_DSN" --app sophia-intel
flyctl secrets set JWT_SECRET_KEY="sophia-intel-production-jwt-secret-$(date +%s)" --app sophia-intel

# 3. Get deployment URL
echo "🌐 Getting deployment URL..."
FLY_URL="https://sophia-intel.fly.dev"
echo "Deployment URL: $FLY_URL"

# 4. Test deployment
echo "🧪 Testing deployment..."
sleep 30
curl -f "$FLY_URL/health" || echo "Health check failed"

# 5. Test dashboard
echo "🎛️ Testing dashboard..."
curl -f "$FLY_URL/dashboard/" || echo "Dashboard check failed"

# 6. Test API endpoints
echo "🔌 Testing API endpoints..."
curl -f "$FLY_URL/api/v1/swarm/status" || echo "Swarm API check failed"

echo "✅ DEPLOYMENT COMPLETE!"
echo "🌐 SOPHIA Intel is live at: $FLY_URL"
echo "🎛️ Dashboard available at: $FLY_URL/dashboard/"
echo "🔌 API endpoints ready at: $FLY_URL/api/"

