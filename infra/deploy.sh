#!/bin/bash
# Production deployment script for Sophia Intel AI

set -e

echo "🚀 Deploying Sophia Intel AI to production..."

# Load environment variables strictly from repo-local .env.master
if [ -f ".env.master" ]; then
    # shellcheck disable=SC2046
    export $(grep -v '^#' .env.master | xargs)
    echo "✅ Loaded environment from .env.master"
else
    echo "❌ .env.master not found in repository root"
    echo "   Create it: cp .env.template .env.master && chmod 600 .env.master"
    exit 1
fi

# Function to set Fly.io secrets
set_fly_secrets() {
    echo "🔐 Setting Fly.io secrets..."
    
    # Required secrets
    fly secrets set \
        OPENROUTER_API_KEY="$OPENROUTER_API_KEY" \
        POSTGRES_URL="$POSTGRES_URL" \
        REDIS_URL="$REDIS_URL" \
        NEO4J_URI="$NEO4J_URI" \
        NEO4J_USER="$NEO4J_USER" \
        NEO4J_PASSWORD="$NEO4J_PASSWORD" \
        --app sophia-intel-ai
    
    # Optional secrets (if set)
    if [ -n "$DASHSCOPE_API_KEY" ]; then
        fly secrets set DASHSCOPE_API_KEY="$DASHSCOPE_API_KEY" --app sophia-intel-ai
    fi
    
    if [ -n "$BRIGHTDATA_API_KEY" ]; then
        fly secrets set BRIGHTDATA_API_KEY="$BRIGHTDATA_API_KEY" --app sophia-intel-ai
    fi
    
    if [ -n "$SENTRY_DSN" ]; then
        fly secrets set SENTRY_DSN="$SENTRY_DSN" --app sophia-intel-ai
    fi
    
    echo "✅ Secrets configured"
}

# Function to deploy to Fly.io
deploy_fly() {
    echo "🏗️ Building and deploying to Fly.io..."
    
    # Deploy the application
    fly deploy --app sophia-intel-ai
    
    echo "✅ Deployment complete"
}

# Function to check deployment status
check_status() {
    echo "📊 Checking deployment status..."
    
    fly status --app sophia-intel-ai
    
    # Check health endpoint
    APP_URL=$(fly info --app sophia-intel-ai -j | jq -r '.Hostname')
    if [ -n "$APP_URL" ]; then
        echo "🔍 Testing health endpoint..."
        curl -sf "https://$APP_URL/health" && echo "✅ Health check passed" || echo "❌ Health check failed"
    fi
}

# Main deployment flow
main() {
    case "${1:-deploy}" in
        secrets)
            set_fly_secrets
            ;;
        deploy)
            set_fly_secrets
            deploy_fly
            check_status
            ;;
        status)
            check_status
            ;;
        logs)
            fly logs --app sophia-intel-ai
            ;;
        scale)
            fly scale count ${2:-2} --app sophia-intel-ai
            ;;
        *)
            echo "Usage: $0 {deploy|secrets|status|logs|scale [count]}"
            exit 1
            ;;
    esac
}

# Check if Fly CLI is installed
if ! command -v fly &> /dev/null; then
    echo "❌ Fly CLI not found. Install from https://fly.io/docs/getting-started/installing-flyctl/"
    exit 1
fi

# Check if app exists, create if not
if ! fly apps list | grep -q sophia-intel-ai; then
    echo "📱 Creating Fly.io app..."
    fly apps create sophia-intel-ai
fi

# Run main deployment
main "$@"
