#!/bin/bash
# Tech Stack Upgrade Script for Sophia Intel AI
# Updates all components to latest versions (Aug 30, 2025)

set -e

echo "=============================================="
echo "🚀 TECH STACK UPGRADE SCRIPT"
echo "=============================================="
echo "This script will upgrade all components to latest versions"
echo ""

# 1. Python Packages
echo "📦 Upgrading Python Packages..."
echo "------------------------------"

# Core packages with latest versions
pip3 install -U \
    agno==1.8.1 \
    weaviate-client==4.16.9 \
    weaviate-agents==0.13.0 \
    portkey-ai \
    psycopg2-binary \
    sqlalchemy \
    fastapi==0.116.1 \
    openai \
    httpx \
    aiofiles \
    python-dotenv

# Optional: Airbyte CDK if needed for data pipelines
# pip3 install airbyte-cdk

echo "✅ Python packages upgraded"

# 2. Pulumi CLI Update
echo ""
echo "🔧 Upgrading Pulumi CLI..."
echo "-------------------------"

# Check current version
CURRENT_PULUMI=$(pulumi version 2>/dev/null || echo "not installed")
echo "Current: $CURRENT_PULUMI"

# Upgrade to latest (v3.192.0)
curl -fsSL https://get.pulumi.com | sh
export PATH=$PATH:$HOME/.pulumi/bin

# Upgrade ESC to latest (v0.17.0)
curl -fsSL https://get.pulumi.com/esc/install.sh | sh

echo "✅ Pulumi upgraded to v3.192.0"
echo "✅ ESC upgraded to v0.17.0"

# 3. Weaviate Setup
echo ""
echo "🔍 Setting up Weaviate v1.32..."
echo "--------------------------------"

# Create docker-compose for Weaviate
cat > docker-compose.weaviate.yml <<EOF
version: '3.8'
services:
  weaviate:
    image: semitechnologies/weaviate:1.32.0
    ports:
      - "8080:8080"
    environment:
      - QUERY_DEFAULTS_LIMIT=20
      - AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true
      - PERSISTENCE_DATA_PATH=/var/lib/weaviate
      - DEFAULT_VECTORIZER_MODULE=text2vec-transformers
      - ENABLE_MODULES=text2vec-transformers
      - TRANSFORMERS_INFERENCE_API=http://t2v-transformers:8080
      - CLUSTER_HOSTNAME=node1
    volumes:
      - weaviate_data:/var/lib/weaviate
    restart: unless-stopped

  t2v-transformers:
    image: semitechnologies/transformers-inference:sentence-transformers-multi-qa-MiniLM-L6-cos-v1
    environment:
      - ENABLE_CUDA=0
    restart: unless-stopped

volumes:
  weaviate_data:
EOF

echo "Starting Weaviate..."
docker-compose -f docker-compose.weaviate.yml up -d

echo "✅ Weaviate v1.32 running on http://localhost:8080"

# 4. PostgreSQL/Neon Setup
echo ""
echo "🐘 PostgreSQL/Neon Configuration..."
echo "-----------------------------------"

# Check if we should use Neon or local PostgreSQL
if [ -z "$NEON_DATABASE_URL" ]; then
    echo "⚠️  No Neon database configured"
    echo "   To use Neon (PostgreSQL 17.5):"
    echo "   1. Create account at https://neon.tech"
    echo "   2. Create project with PostgreSQL 17"
    echo "   3. Add NEON_DATABASE_URL to .env"
else
    echo "✅ Neon database configured"
fi

# 5. Environment Configuration
echo ""
echo "🔐 Configuring Environment..."
echo "-----------------------------"

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.complete .env
    echo "⚠️  Please edit .env and add your API keys"
else
    echo "✅ .env file exists"
fi

# 6. Lambda Stack (Optional - for GPU workloads)
echo ""
echo "🎮 Lambda Stack (Optional)..."
echo "-----------------------------"
echo "For GPU acceleration with latest CUDA 12.8:"
echo "  wget -nv -O- https://lambda.ai/install-lambda-stack.sh | I_AGREE_TO_THE_CUDNN_LICENSE=1 sh"
echo "  (Only run on machines with NVIDIA GPUs)"

# 7. Airbyte (Optional - for data pipelines)
echo ""
echo "🔄 Airbyte (Optional)..."
echo "------------------------"
echo "To install Airbyte v1.8:"
echo "  curl -s https://get.airbyte.com | bash"
echo "  abctl local install"

echo ""
echo "=============================================="
echo "📊 UPGRADE SUMMARY"
echo "=============================================="
echo ""
echo "✅ Completed:"
echo "  • Python packages updated to latest"
echo "  • Pulumi CLI v3.192.0"
echo "  • Pulumi ESC v0.17.0"
echo "  • Weaviate v1.32 running"
echo ""
echo "⚠️  Action Required:"
echo "  1. Edit .env file with your API keys:"
echo "     - PORTKEY_API_KEY"
echo "     - OPENROUTER_API_KEY"
echo "     - ANTHROPIC_API_KEY"
echo "     - Other provider keys"
echo ""
echo "  2. Configure Portkey virtual keys at:"
echo "     https://app.portkey.ai"
echo ""
echo "  3. Optional: Set up Neon PostgreSQL 17.5"
echo "     https://neon.tech"
echo ""
echo "✨ Upgrade complete!"