#!/usr/bin/env bash
set -e

# SOPHIA Intel Northflank Deployment Script
# This script deploys the complete SOPHIA Intel platform to Northflank and configures DNS

# Configure these variables
NF_API_TOKEN="${NF_API_TOKEN:?Please set NF_API_TOKEN env var}"
DNSIMPLE_API_KEY="${DNSIMPLE_API_KEY:?Please set DNSIMPLE_API_KEY env var}"
ORGANIZATION="pay-ready"
TEAM="sophia3"
PROJECT="sophia-intel"
REPO="ai-cherry/sophia-intel"
BRANCH="main"
API_SERVICE="sophia-api"
DASH_SERVICE="sophia-dashboard"
MCP_SERVICE="sophia-mcp"
SECRET_GROUP="sophia-secrets"
DOMAIN="sophia-intel.ai"
DNSIMPLE_ACCOUNT_ID="68a0954"  # Extract from API key or set manually

echo "🚀 Starting SOPHIA Intel deployment to Northflank..."

# Install NF CLI if not present
if ! command -v nf &> /dev/null; then
  echo "📦 Installing Northflank CLI..."
  npm install -g @northflank/cli
fi

# Authenticate
echo "🔐 Authenticating with Northflank..."
nf login --token "$NF_API_TOKEN"

# Ensure project exists (no-op if it already does)
echo "📋 Ensuring project exists..."
if ! nf get project --team "$TEAM" --project "$PROJECT" &> /dev/null; then
  echo "🆕 Creating new project: $PROJECT"
  nf create project --team "$TEAM" --name "$PROJECT" --region "us-east-1"
else
  echo "✅ Project $PROJECT already exists"
fi

# Create or update a secret group
echo "🔒 Setting up secret group..."
if ! nf get secret-group --team "$TEAM" --project "$PROJECT" --name "$SECRET_GROUP" &> /dev/null; then
  echo "🆕 Creating secret group: $SECRET_GROUP"
  nf create secret-group --team "$TEAM" --project "$PROJECT" --name "$SECRET_GROUP"
else
  echo "✅ Secret group $SECRET_GROUP already exists"
fi

# Add secrets
echo "🔑 Configuring secrets..."
nf secrets set --team "$TEAM" --project "$PROJECT" --group "$SECRET_GROUP" \
  LAMBDA_API_KEY="${LAMBDA_API_KEY:?Please set LAMBDA_API_KEY}" \
  LAMBDA_API_BASE="https://api.lambda.ai/v1" \
  OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-}" \
  DNSIMPLE_API_KEY="${DNSIMPLE_API_KEY:-}" \
  DASHBOARD_API_TOKEN="${DASHBOARD_API_TOKEN:-}" \
  NOTION_API_KEY="${NOTION_API_KEY:-}" \
  QDRANT_URL="${QDRANT_URL:-}" \
  QDRANT_API_KEY="${QDRANT_API_KEY:-}" \
  ENVIRONMENT="production"

echo "✅ Secrets configured successfully"

# Deploy the API service (FastAPI container)
echo "🔌 Deploying SOPHIA API service..."
if nf get service --team "$TEAM" --project "$PROJECT" --name "$API_SERVICE" &> /dev/null; then
  echo "🔄 Updating existing API service..."
  nf update service \
    --team "$TEAM" \
    --project "$PROJECT" \
    --name "$API_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --dockerfile-path "northflank/docker/sophia-api.Dockerfile" \
    --secret-group "$SECRET_GROUP"
else
  echo "🆕 Creating new API service..."
  nf create service \
    --team "$TEAM" \
    --project "$PROJECT" \
    --name "$API_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --build-type dockerfile \
    --dockerfile-path "northflank/docker/sophia-api.Dockerfile" \
    --port 5000 \
    --plan standard-1024 \
    --env "PORT=5000" \
    --secret-group "$SECRET_GROUP" \
    --public \
    --domain "api.sophia-intel.ai"
fi

# Deploy the dashboard (React build)
echo "🌐 Deploying SOPHIA Dashboard service..."
if nf get service --team "$TEAM" --project "$PROJECT" --name "$DASH_SERVICE" &> /dev/null; then
  echo "🔄 Updating existing Dashboard service..."
  nf update service \
    --team "$TEAM" \
    --project "$PROJECT" \
    --name "$DASH_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --dockerfile-path "northflank/docker/sophia-dashboard.Dockerfile"
else
  echo "🆕 Creating new Dashboard service..."
  nf create service \
    --team "$TEAM" \
    --project "$PROJECT" \
    --name "$DASH_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --build-type dockerfile \
    --dockerfile-path "northflank/docker/sophia-dashboard.Dockerfile" \
    --port 80 \
    --plan standard-512 \
    --env "VITE_API_URL=https://api.sophia-intel.ai" \
    --env "NODE_ENV=production" \
    --public \
    --domain "www.sophia-intel.ai" \
    --domain "app.sophia-intel.ai"
fi

# Deploy the MCP services
echo "🧠 Deploying SOPHIA MCP services..."
if nf get service --team "$TEAM" --project "$PROJECT" --name "$MCP_SERVICE" &> /dev/null; then
  echo "🔄 Updating existing MCP service..."
  nf update service \
    --team "$TEAM" \
    --project "$PROJECT" \
    --name "$MCP_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --dockerfile-path "northflank/docker/sophia-mcp.Dockerfile" \
    --secret-group "$SECRET_GROUP"
else
  echo "🆕 Creating new MCP service..."
  nf create service \
    --team "$TEAM" \
    --project "$PROJECT" \
    --name "$MCP_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --build-type dockerfile \
    --dockerfile-path "northflank/docker/sophia-mcp.Dockerfile" \
    --port 8000 \
    --plan standard-512 \
    --env "PORT=8000" \
    --secret-group "$SECRET_GROUP" \
    --internal-only
fi

echo "⏳ Waiting for services to deploy..."
sleep 30

# Function to configure DNS records
configure_dns() {
  local subdomain=$1
  local service_name=$2
  local record_type=$3
  local target=$4
  
  echo "🌐 Configuring DNS for $subdomain.$DOMAIN -> $target"
  
  # Delete existing record if it exists
  curl -s -X GET \
    -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
    "https://api.dnsimple.com/v2/$DNSIMPLE_ACCOUNT_ID/zones/$DOMAIN/records" | \
    jq -r ".data[] | select(.name == \"$subdomain\") | .id" | \
    while read record_id; do
      if [ ! -z "$record_id" ]; then
        echo "🗑️ Deleting existing DNS record for $subdomain"
        curl -s -X DELETE \
          -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
          "https://api.dnsimple.com/v2/$DNSIMPLE_ACCOUNT_ID/zones/$DOMAIN/records/$record_id"
      fi
    done
  
  # Create new DNS record
  curl -s -X POST \
    -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$subdomain\", \"type\": \"$record_type\", \"content\": \"$target\", \"ttl\": 300}" \
    "https://api.dnsimple.com/v2/$DNSIMPLE_ACCOUNT_ID/zones/$DOMAIN/records" | \
    jq -r '.data.id' && echo "✅ DNS record created for $subdomain.$DOMAIN"
}

# Get service hostnames from Northflank
echo "🔍 Getting service hostnames..."
API_HOSTNAME=$(nf get service --team "$TEAM" --project "$PROJECT" --name "$API_SERVICE" --output json 2>/dev/null | jq -r '.data.ports[0].domains[0]' || echo "")
DASH_HOSTNAME=$(nf get service --team "$TEAM" --project "$PROJECT" --name "$DASH_SERVICE" --output json 2>/dev/null | jq -r '.data.ports[0].domains[0]' || echo "")

# If hostnames are not available, use default Northflank pattern
if [ -z "$API_HOSTNAME" ] || [ "$API_HOSTNAME" = "null" ]; then
  API_HOSTNAME="$API_SERVICE-$PROJECT.northflank.app"
fi

if [ -z "$DASH_HOSTNAME" ] || [ "$DASH_HOSTNAME" = "null" ]; then
  DASH_HOSTNAME="$DASH_SERVICE-$PROJECT.northflank.app"
fi

echo "📡 API Hostname: $API_HOSTNAME"
echo "🌐 Dashboard Hostname: $DASH_HOSTNAME"

# Configure DNS records
if command -v jq &> /dev/null; then
  configure_dns "api" "$API_SERVICE" "CNAME" "$API_HOSTNAME"
  configure_dns "www" "$DASH_SERVICE" "CNAME" "$DASH_HOSTNAME"
  configure_dns "app" "$DASH_SERVICE" "CNAME" "$DASH_HOSTNAME"
else
  echo "⚠️ jq not installed, skipping DNS configuration"
  echo "📋 Manual DNS setup required:"
  echo "   api.$DOMAIN -> CNAME -> $API_HOSTNAME"
  echo "   www.$DOMAIN -> CNAME -> $DASH_HOSTNAME"
  echo "   app.$DOMAIN -> CNAME -> $DASH_HOSTNAME"
fi

# Add custom domains to Northflank services
echo "🔗 Adding custom domains to Northflank services..."
nf update service "$API_SERVICE" --team "$TEAM" --project "$PROJECT" --domain "api.$DOMAIN" || echo "Domain might already be configured"
nf update service "$DASH_SERVICE" --team "$TEAM" --project "$PROJECT" --domain "www.$DOMAIN" --domain "app.$DOMAIN" || echo "Domains might already be configured"

# Check service status
echo "🔍 Checking service status..."
for service in "$API_SERVICE" "$DASH_SERVICE" "$MCP_SERVICE"; do
  echo "Checking $service..."
  if nf get service --team "$TEAM" --project "$PROJECT" --name "$service" &> /dev/null; then
    echo "✅ $service is deployed"
  else
    echo "❌ $service deployment failed"
  fi
done

echo ""
echo "🎉 SOPHIA Intel Deployment Complete!"
echo "📡 API: https://api.sophia-intel.ai"
echo "🌐 Dashboard: https://www.sophia-intel.ai"
echo "🧠 MCP Services: Internal service (not publicly accessible)"
echo ""
echo "🔍 To check deployment status:"
echo "nf get services --team $TEAM --project $PROJECT"
echo ""
echo "📊 To view logs:"
echo "nf logs --team $TEAM --project $PROJECT --service $API_SERVICE"
echo "nf logs --team $TEAM --project $PROJECT --service $DASH_SERVICE"
echo "nf logs --team $TEAM --project $PROJECT --service $MCP_SERVICE"

