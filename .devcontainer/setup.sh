#!/bin/bash
set -e

echo "🚀 Sophia AI Platform - Automated Setup"
echo "========================================="

# Install UV
echo "📦 Installing UV package manager..."
pip install --upgrade pip
pip install uv

# Install Pulumi
echo "☁️ Installing Pulumi..."
curl -fsSL https://get.pulumi.com | sh
echo 'export PATH=$PATH:$HOME/.pulumi/bin' >> ~/.bashrc
source ~/.bashrc

# Create and activate virtual environment
echo "🐍 Setting up Python environment..."
uv venv .venv
source .venv/bin/activate

# Install dependencies
echo "📋 Installing dependencies..."
uv pip install -r requirements.txt

# Create .env file
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << 'EOF'
ENVIRONMENT=development
DATABASE_URL=postgresql+asyncpg://sophia:localdev@localhost:5432/sophia
REDIS_URL=${REDIS_URL}
JWT_SECRET_KEY=dev-secret-change-in-production
DEBUG=true
SENTRY_DSN=
EOF
fi

# Make all scripts executable
echo "🔧 Setting up scripts..."
find scripts -type f -name "*.sh" -exec chmod +x {} \;
find scripts -type f -name "*.py" -exec chmod +x {} \;

# Start Docker services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Run cleanup script
echo "🧹 Running cleanup script..."
python scripts/cleanup.py || echo "Cleanup script not found or failed"

# Verify installation
echo "✅ Verifying installation..."
python -c "from backend.main import app; print('✓ Backend OK')"

echo ""
echo "✅ Setup complete! The API is ready to start."
echo "Run: python backend/main.py"
echo "Then visit: http://localhost:8000/docs"

