#!/bin/bash
set -e

echo "🚀 Deploying Sophia AI Infrastructure"

# Check required environment variables
required_vars=(
    "PULUMI_ACCESS_TOKEN"
    "LAMBDA_CLOUD_API_KEY" 
    "DNSIMPLE_API_KEY"
    "OPENROUTER_API_KEY"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        missing_vars+=("$var")
    fi
done

if [[ ${#missing_vars[@]} -gt 0 ]]; then
    echo "❌ Missing required environment variables:"
    printf '   %s\n' "${missing_vars[@]}"
    exit 1
fi

# Navigate to infrastructure directory
cd infra

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Select Pulumi stack
echo "🎯 Selecting Pulumi stack..."
pulumi stack select scoobyjava-org/sophia-prod-on-lambda

# Deploy infrastructure
echo "🏗️ Deploying infrastructure..."
pulumi up --yes

echo "✅ Infrastructure deployment completed!"
