#!/bin/bash

# Sophia AI ASIP Codespaces Post-Create Command
# This script runs automatically after the Codespace is created

echo "🚀 Sophia AI ASIP Setup Starting..."
echo "=================================="

# Set working directory
cd /workspace

# Use existing UV virtual environment from Dockerfile
echo "📦 Activating existing Python environment..."
source .venv/bin/activate

# Install ASIP dependencies
echo "📦 Installing ASIP dependencies..."
if [ -f "requirements-codespaces.txt" ]; then
    pip install -r requirements-codespaces.txt
    echo "✅ Codespaces requirements installed"
elif [ -f "requirements-asip.txt" ]; then
    pip install -r requirements-asip.txt
    echo "✅ ASIP requirements installed"
else
    echo "⚠️ No requirements file found, using minimal setup"
    pip install fastapi uvicorn[standard] pydantic python-dotenv
fi

# Install chat interface dependencies
if [ -f "requirements-chat.txt" ]; then
    pip install -r requirements-chat.txt
    echo "✅ Chat interface requirements installed"
fi

# Setup environment variables
echo "🔧 Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ Created .env from template"
    echo ""
    echo "⚠️ IMPORTANT: Configure your Portkey virtual keys in .env:"
    echo "   PORTKEY_API_KEY=your_key"
    echo "   PORTKEY_VIRTUAL_KEY_OPUS=vk_xxx"
    echo "   PORTKEY_VIRTUAL_KEY_SONNET=vk_xxx"
    echo "   PORTKEY_VIRTUAL_KEY_QWEN=vk_xxx"
    echo ""
fi

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null

# Pre-compile Numba cache for performance
echo "⚡ Pre-compiling Numba JIT cache..."
python -c "from asip.numba_ops import compile_cache; compile_cache()" 2>/dev/null || echo "⚠️ Numba cache pre-compilation skipped"

# Start the ASIP backend
echo "🎯 Starting ASIP Backend..."
cd backend
nohup python main.py > /tmp/asip_backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Check if Docker is available and start chat interface
if command -v docker &> /dev/null; then
    echo "🐳 Docker is available, preparing chat interface..."
    if [ -f "scripts/deploy_chat_interface.sh" ]; then
        echo "📱 Chat interface can be deployed with: ./scripts/deploy_chat_interface.sh"
    fi
fi

echo ""
echo "✅ Sophia AI ASIP Setup Complete!"
echo "=================================="
echo ""
echo "🔗 Your ASIP services are available at:"
echo "   • Backend API: https://${CODESPACE_NAME}-8000.app.github.dev/"
echo "   • Health Check: https://${CODESPACE_NAME}-8000.app.github.dev/health"
echo "   • Metrics: https://${CODESPACE_NAME}-8000.app.github.dev/metrics"
echo ""
echo "🤖 Natural Chat Interface (after deployment):"
echo "   • Open WebUI: https://${CODESPACE_NAME}-8080.app.github.dev/"
echo "   • Chat Bridge API: https://${CODESPACE_NAME}-8100.app.github.dev/"
echo "   • Streamlit Dashboard: https://${CODESPACE_NAME}-8501.app.github.dev/"
echo ""
echo "📊 API Endpoints:"
echo "   • POST /api/v1/process - Process task with ASIP orchestrator"
echo "   • POST /api/v1/assist - AI assistance for Codespaces"
echo "   • POST /api/v1/optimize - Code optimization"
echo ""
echo "💰 Cost Optimization:"
echo "   • Qwen3-Coder: $0.20/1M tokens (code tasks)"
echo "   • Gemini Flash: $0.075/1M tokens (simple tasks)"
echo "   • Claude Sonnet: $3/1M tokens (balanced tasks)"
echo ""
echo "💡 Quick Commands:"
echo "   • Test API: curl http://localhost:8000/health"
echo "   • View logs: tail -f /tmp/asip_backend.log"
echo "   • Restart backend: cd backend && python main.py"
echo "   • Deploy Chat UI: ./scripts/deploy_chat_interface.sh"
echo ""
echo "⚠️ Don't forget to configure your API keys in .env!"
