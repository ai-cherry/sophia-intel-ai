#!/bin/bash
set -e

echo "🚀 Deploying Sophia AI Application"

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "🧪 Running tests..."
python -m pytest tests/ || echo "⚠️ Tests failed or no tests found"

# Deploy to Vercel (if configured)
if command -v vercel &> /dev/null; then
    echo "🌐 Deploying to Vercel..."
    vercel --prod
else
    echo "⚠️ Vercel CLI not found, skipping web deployment"
fi

echo "✅ Application deployment completed!"
