#!/bin/bash

# Pulumi Setup Script for slim-agno
# This script initializes Pulumi with your Personal Access Token

set -e

echo "🔧 Setting up Pulumi for slim-agno infrastructure"

# Check if Pulumi is installed
if ! command -v pulumi &> /dev/null; then
    echo "📦 Installing Pulumi..."
    brew install pulumi/tap/pulumi
fi

echo "✅ Pulumi version: $(pulumi version)"

# Login with PAT (will be provided by user)
if [ -z "$PULUMI_ACCESS_TOKEN" ]; then
    echo "⚠️  Please set PULUMI_ACCESS_TOKEN environment variable"
    echo "   export PULUMI_ACCESS_TOKEN='your-pat-here'"
    exit 1
fi

echo "🔐 Logging into Pulumi Cloud..."
pulumi login

# Create Python project without cloud-specific template
echo "📝 Creating Pulumi Python project..."
pulumi new python --name slim-infra --stack dev --generate-only --yes

# Create neutral Python program
cat > __main__.py <<'EOF'
"""
Slim-agno infrastructure configuration.
Currently manages configuration only; will add cloud resources later.
"""

import pulumi

# Get configuration
cfg = pulumi.Config()

# Export configuration values for reference
pulumi.export("weaviate_url", cfg.get("weaviateUrl") or "http://localhost:8080")
pulumi.export("openai_base_url", cfg.get("openaiBaseUrl") or "https://api.portkey.ai/v1")
pulumi.export("embed_base_url", cfg.get("embedBaseUrl") or "https://api.portkey.ai/v1")
pulumi.export("environment", cfg.get("environment") or "dev")
pulumi.export("note", "slim-agno infrastructure (local-first, no cloud provider)")
EOF

echo "📌 Setting up stack configuration..."

# Set non-secret configs
pulumi stack select dev
pulumi config set weaviateUrl "http://localhost:8080"
pulumi config set openaiBaseUrl "https://api.portkey.ai/v1"
pulumi config set embedBaseUrl "https://api.portkey.ai/v1"
pulumi config set environment "dev"

# Note about secrets
echo ""
echo "⚠️  Next steps:"
echo "1. Set your Portkey Virtual Keys as secrets:"
echo "   pulumi config set --secret portkeyOpenRouterVK 'your-openrouter-vk'"
echo "   pulumi config set --secret portkeyTogetherVK 'your-together-vk'"
echo ""
echo "2. Preview the configuration:"
echo "   pulumi preview"
echo ""
echo "3. Apply the configuration:"
echo "   pulumi up --yes"

echo "✅ Pulumi setup complete!"