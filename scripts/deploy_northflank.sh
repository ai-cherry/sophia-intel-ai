#!/usr/bin/env bash
set -e

# SOPHIA Intel Northflank Deployment Script
# This script deploys the complete SOPHIA Intel platform to Northflank

# Configure these variables
NF_API_TOKEN="${NF_API_TOKEN:?Please set NF_API_TOKEN env var}"
TEAM="payready"
PROJECT="sophia3"
REPO="ai-cherry/sophia-intel"
BRANCH="main"
API_SERVICE="sophia-api"
DASH_SERVICE="sophia-dashboard"
MCP_SERVICE="sophia-mcp"
SECRET_GROUP="sophia-secrets"

echo "🚀 Starting SOPHIA Intel deployment to Northflank..."

# Install NF CLI if not present
if ! command -v nf &> /dev/null; then
  echo "📦 Installing Northflank CLI..."
  npm install -g @northflank/nf
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
if ! nf get secret-group --project "$PROJECT" --name "$SECRET_GROUP" &> /dev/null; then
  echo "🆕 Creating secret group: $SECRET_GROUP"
  nf create secret-group --project "$PROJECT" --name "$SECRET_GROUP"
else
  echo "✅ Secret group $SECRET_GROUP already exists"
fi

# Add secrets
echo "🔑 Configuring secrets..."
nf secrets set --project "$PROJECT" --group "$SECRET_GROUP" \
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
if nf get service --project "$PROJECT" --name "$API_SERVICE" &> /dev/null; then
  echo "🔄 Updating existing API service..."
  nf update service \
    --project "$PROJECT" \
    --name "$API_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --dockerfile-path "northflank/docker/sophia-api.Dockerfile" \
    --secret-group "$SECRET_GROUP"
else
  echo "🆕 Creating new API service..."
  nf create service \
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
if nf get service --project "$PROJECT" --name "$DASH_SERVICE" &> /dev/null; then
  echo "🔄 Updating existing Dashboard service..."
  nf update service \
    --project "$PROJECT" \
    --name "$DASH_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --dockerfile-path "northflank/docker/sophia-dashboard.Dockerfile"
else
  echo "🆕 Creating new Dashboard service..."
  nf create service \
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
if nf get service --project "$PROJECT" --name "$MCP_SERVICE" &> /dev/null; then
  echo "🔄 Updating existing MCP service..."
  nf update service \
    --project "$PROJECT" \
    --name "$MCP_SERVICE" \
    --repository "$REPO" \
    --branch "$BRANCH" \
    --dockerfile-path "northflank/docker/sophia-mcp.Dockerfile" \
    --secret-group "$SECRET_GROUP"
else
  echo "🆕 Creating new MCP service..."
  nf create service \
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

# Check service status
echo "🔍 Checking service status..."
for service in "$API_SERVICE" "$DASH_SERVICE" "$MCP_SERVICE"; do
  echo "Checking $service..."
  if nf get service --project "$PROJECT" --name "$service" &> /dev/null; then
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
echo "nf get services --project $PROJECT"
echo ""
echo "📊 To view logs:"
echo "nf logs --project $PROJECT --service $API_SERVICE"
echo "nf logs --project $PROJECT --service $DASH_SERVICE"
echo "nf logs --project $PROJECT --service $MCP_SERVICE"

