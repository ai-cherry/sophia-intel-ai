#!/bin/bash
# Setup script for Agno 1.8.1 with Portkey and Agent UI

set -e

echo "======================================"
echo "🚀 Setting up Agno 1.8.1 Environment"
echo "======================================"

# Check Python version
python3 --version

# Install/upgrade Agno and dependencies
echo "📦 Installing Agno and dependencies..."
pip3 install -U agno 'fastapi[standard]' duckduckgo-search sqlalchemy openai portkey-ai

# Install additional tools for our custom agents
pip3 install -U aiofiles ripgrep-py gitpython pytest mypy ruff

# Create Agno workspace
echo "🏗️ Creating Agno workspace..."
if [ ! -d "agno-workspace" ]; then
    ag ws create --template agent-api --name sophia-intel
    cd sophia-intel

    # Copy our custom playground
    cp ../app/agno_v2/playground.py .

    # Copy environment configuration
    cp ../.env.portkey .env

    cd ..
else
    echo "Workspace already exists"
fi

# Setup Agent UI
echo "🎨 Setting up Agent UI..."
if [ ! -d "agent-ui" ]; then
    npx create-agent-ui@latest agent-ui
    cd agent-ui
    npm install

    # Create UI configuration
    cat > .env.local <<EOF
NEXT_PUBLIC_API_URL=http://127.0.0.1:7777
NEXT_PUBLIC_APP_NAME=Sophia Intel AI
NEXT_PUBLIC_ENABLE_TEAMS=true
NEXT_PUBLIC_ENABLE_MEMORY=true
EOF

    cd ..
else
    echo "Agent UI already exists"
fi

# Create startup script
cat > start_agno.sh <<'EOF'
#!/bin/bash
# Start all Agno services

# Terminal 1: Playground server
echo "Starting Playground server..."
source .env.portkey
cd sophia-intel
python playground.py &
PLAYGROUND_PID=$!

# Terminal 2: Agent UI
echo "Starting Agent UI..."
cd ../agent-ui
npm run dev &
UI_PID=$!

echo "======================================"
echo "✅ All services started!"
echo "======================================"
echo "📡 Playground API: http://127.0.0.1:7777"
echo "🎨 Agent UI: http://localhost:3000"
echo "📚 API Docs: http://127.0.0.1:7777/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "kill $PLAYGROUND_PID $UI_PID; exit" INT
wait
EOF

chmod +x start_agno.sh

echo "======================================"
echo "✅ Setup complete!"
echo "======================================"
echo ""
echo "To start the system:"
echo "1. Edit .env.portkey with your API keys"
echo "2. Run: ./start_agno.sh"
echo ""
echo "Features enabled:"
echo "✅ Agno 1.8.1 with Teams API"
echo "✅ Portkey gateway routing"
echo "✅ Multi-provider support"
echo "✅ Agent UI interface"
echo "✅ 11 specialized agents"
echo "✅ 5 pre-configured teams"
echo "✅ Smart task routing"
