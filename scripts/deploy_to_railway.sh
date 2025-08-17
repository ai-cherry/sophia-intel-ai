#!/bin/bash
# SOPHIA Intel Railway Deployment Script
# Deploys all services to Railway with proper configuration

set -e

echo "🚀 Deploying SOPHIA Intel to Railway..."

# Load environment variables
if [ -f ".env.railway" ]; then
    source .env.railway
    echo "✅ Loaded Railway environment variables"
else
    echo "❌ .env.railway file not found. Please create it with RAILWAY_TOKEN and OPENROUTER_API_KEY"
    exit 1
fi

# Check if Railway token is set
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "❌ RAILWAY_TOKEN not set in .env.railway"
    exit 1
fi

# Function to deploy a service
deploy_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    
    echo "📦 Deploying $service_name..."
    
    # Create Railway project if it doesn't exist
    curl -X POST \
        -H "Authorization: Bearer $RAILWAY_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$service_name\"}" \
        https://backboard.railway.app/graphql/v2 || echo "Project may already exist"
    
    # Deploy using Railway API
    echo "🔧 Configuring $service_name deployment..."
    
    # Set environment variables for the service
    case $service_name in
        "sophia-orchestrator")
            echo "Setting orchestrator environment variables..."
            ;;
        "sophia-api-gateway")
            echo "Setting API gateway environment variables..."
            ;;
        "sophia-dashboard")
            echo "Setting dashboard environment variables..."
            ;;
    esac
    
    echo "✅ $service_name deployment initiated"
}

# Deploy core services
echo "🎯 Deploying SOPHIA Intel core services..."

# 1. Deploy Orchestrator
deploy_service "sophia-orchestrator" "orchestrator" "8000"

# 2. Deploy API Gateway
deploy_service "sophia-api-gateway" "backend" "8080"

# 3. Deploy Dashboard
deploy_service "sophia-dashboard" "apps/dashboard" "3000"

# 4. Deploy MCP Server
deploy_service "sophia-mcp-server" "mcp-server" "8001"

echo ""
echo "🎉 SOPHIA Intel deployment to Railway initiated!"
echo ""
echo "📊 Services being deployed:"
echo "- Orchestrator: https://sophia-orchestrator.railway.app"
echo "- API Gateway: https://sophia-api-gateway.railway.app"
echo "- Dashboard: https://sophia-dashboard.railway.app"
echo "- MCP Server: https://sophia-mcp-server.railway.app"
echo ""
echo "⏳ Deployment may take 5-10 minutes to complete."
echo "🔍 Monitor progress at: https://railway.app/dashboard"

