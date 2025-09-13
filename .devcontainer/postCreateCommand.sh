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

echo "📦 Installing Python dependencies..."
if [ -f "requirements-codespaces.txt" ]; then
    pip install -r requirements-codespaces.txt
    echo "✅ Codespaces requirements installed"
elif [ -f "requirements-asip.txt" ]; then
    pip install -r requirements-asip.txt
    echo "✅ ASIP requirements installed"
else
    echo "⚠️ No requirements file found, using minimal setup"
    # Do NOT install python-dotenv; env comes from ./.env.master via ./sophia
    pip install fastapi uvicorn[standard] pydantic
fi

# Install chat interface dependencies
if [ -f "requirements-chat.txt" ]; then
    pip install -r requirements-chat.txt
    echo "✅ Chat interface requirements installed"
fi

# Environment policy: single source ./.env.master loaded by ./sophia. No .env files created here.

# Make scripts executable
chmod +x scripts/*.sh 2>/dev/null

# Pre-compile Numba cache for performance
echo "⚡ Pre-compiling Numba JIT cache..."
python -c "from asip.numba_ops import compile_cache; compile_cache()" 2>/dev/null || echo "⚠️ Numba cache pre-compilation skipped"

# Backend startup is managed via ./sophia/unified-system-manager.sh when needed.

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
echo "🔗 Use './sophia start' to start MCP (8081,8082,8084). No UI in this repo."
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
echo "   • Note: No UI runs from this repo. Use external Coding UI."
echo "   • View logs: tail -f /tmp/asip_backend.log"
echo "   • Restart backend: cd backend && python main.py"
echo "   • Deploy Chat UI: ./scripts/deploy_chat_interface.sh"
echo ""
echo "⚠️ Don't forget to configure your API keys in .env!"

echo "[devcontainer] Coding UI is a separate project; only API/MCP run here."
