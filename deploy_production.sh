#!/bin/bash
# SOPHIA V4 Production Deployment Script
# Sets up all API keys as Fly.io secrets and deploys to production

set -e

echo "🚀 SOPHIA V4 Production Deployment Starting..."

# Load secrets from environment file
echo "🔑 Step 1: Loading secrets..."
if [ -f "secrets.env" ]; then
    echo "Loading secrets from secrets.env..."
    source secrets.env
else
    echo "❌ secrets.env file not found!"
    echo "📋 Please create secrets.env from secrets.env.example and fill in your API keys"
    echo "   cp secrets.env.example secrets.env"
    echo "   # Edit secrets.env with your actual API keys"
    exit 1
fi

# Authenticate with Fly.io
echo "📋 Step 2: Authenticate with Fly.io"
echo "Run: fly auth login"
echo "Press Enter when authenticated..."
read -p ""

# Set all API keys as Fly.io secrets
echo "🔑 Step 3: Setting up Fly.io secrets..."
fly secrets set \
  OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
  GITHUB_TOKEN="$GITHUB_TOKEN" \
  MEM0_API_KEY="$MEM0_API_KEY" \
  NEON_API_TOKEN="$NEON_API_TOKEN" \
  N8N_API_KEY="$N8N_API_KEY" \
  GONG_ACCESS_KEY="$GONG_ACCESS_KEY" \
  GONG_CLIENT_SECRET="$GONG_CLIENT_SECRET" \
  LAMBDA_API_KEY="$LAMBDA_API_KEY" \
  TELEGRAM_API_KEY="$TELEGRAM_API_KEY" \
  DNSIMPLE_API_KEY="$DNSIMPLE_API_KEY" \
  NEON_ORG_ID="$NEON_ORG_ID" \
  NEON_PROJECT_ID="$NEON_PROJECT_ID" \
  NEON_PROJECT_NAME="$NEON_PROJECT_NAME" \
  LAMBDA_IPS="$LAMBDA_IPS" \
  --app sophia-intel

echo "✅ Secrets configured successfully!"

# Verify secrets are set
echo "🔍 Step 4: Verifying secrets..."
fly secrets list --app sophia-intel

# Deploy to production
echo "🚀 Step 5: Deploying to production..."
fly deploy --app sophia-intel

# Check deployment status
echo "📊 Step 6: Checking deployment status..."
fly status --app sophia-intel

# Test the deployment
echo "🧪 Step 7: Testing production deployment..."
echo "Production URL: https://sophia-intel.fly.dev"
echo "Health check: https://sophia-intel.fly.dev/health"
echo "SOPHIA interface: https://sophia-intel.fly.dev/v4/"

# Test API endpoints
echo "Testing API endpoints..."
curl -s https://sophia-intel.fly.dev/health | jq .
curl -s https://sophia-intel.fly.dev/api/v1/mcp/analytics | jq .

echo "🎉 SOPHIA V4 Production Deployment Complete!"
echo "🌐 Access SOPHIA at: https://sophia-intel.fly.dev/v4/"
echo "🔧 Test MCP functionality through the real interface!"

