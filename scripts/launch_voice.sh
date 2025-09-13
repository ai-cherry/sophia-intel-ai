#!/bin/bash

# Launch script for Agno Voice Coding System
# Supports local (Mac M3), cloud, and hybrid deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VOICE_DIR="$PROJECT_ROOT/voice"
ENV_FILE="$PROJECT_ROOT/.env.voice"

# Default values
DEPLOYMENT_MODE="${DEPLOYMENT_MODE:-hybrid}"
PORT="${VOICE_PORT:-8443}"
HOST="${VOICE_HOST:-0.0.0.0}"

echo -e "${BLUE}🎤 Launching Agno Voice Coding System${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Function to check dependencies
check_dependencies() {
    echo -e "${YELLOW}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 is not installed${NC}"
        exit 1
    fi
    
    # Check Node.js (for PWA)
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed${NC}"
        exit 1
    fi
    
    # Check Docker (optional for containerized deployment)
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✓ Docker is installed${NC}"
        DOCKER_AVAILABLE=true
    else
        echo -e "${YELLOW}⚠ Docker not found (optional)${NC}"
        DOCKER_AVAILABLE=false
    fi
    
    echo -e "${GREEN}✓ Dependencies check passed${NC}"
}

# Function to setup environment
setup_environment() {
    echo -e "${YELLOW}Setting up environment...${NC}"
    
    # Create .env.voice if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Creating .env.voice file...${NC}"
        cat > "$ENV_FILE" << EOF
# Voice Service Configuration
VOICE_DEPLOYMENT_MODE=$DEPLOYMENT_MODE
VOICE_HOST=$HOST
VOICE_PORT=$PORT

# API Keys (add your keys here)
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
DEEPGRAM_API_KEY=

# Security
JWT_SECRET=$(openssl rand -base64 32)

# Paths
VOICE_MODELS_PATH=$PROJECT_ROOT/models
VOICE_LOGS_PATH=$PROJECT_ROOT/logs
EOF
        echo -e "${GREEN}✓ Created .env.voice${NC}"
    fi
    
    # Load environment variables
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/models"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/certs"
    
    echo -e "${GREEN}✓ Environment setup complete${NC}"
}

# Function to download models for local mode
download_models() {
    if [ "$DEPLOYMENT_MODE" = "local" ] || [ "$DEPLOYMENT_MODE" = "hybrid" ]; then
        echo -e "${YELLOW}Downloading models for local mode...${NC}"
        
        # Check if Whisper model exists
        if [ ! -f "$PROJECT_ROOT/models/whisper-base.en.pt" ]; then
            echo "Downloading Whisper base.en model..."
            python3 -c "import whisper; whisper.load_model('base.en', download_root='$PROJECT_ROOT/models')"
        else
            echo -e "${GREEN}✓ Whisper model already downloaded${NC}"
        fi
        
        # Check for XTTS model (if using)
        # Add XTTS download logic here if needed
        
        echo -e "${GREEN}✓ Models ready${NC}"
    fi
}

# Function to install Python dependencies
install_python_deps() {
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "$PROJECT_ROOT/venv_voice" ]; then
        python3 -m venv "$PROJECT_ROOT/venv_voice"
    fi
    
    # Activate virtual environment
    source "$PROJECT_ROOT/venv_voice/bin/activate"
    
    # Install requirements
    pip install -q --upgrade pip
    pip install -q \
        fastapi \
        uvicorn \
        websockets \
        aiortc \
        openai-whisper \
        elevenlabs \
        pydantic \
        python-dotenv \
        numpy \
        structlog
    
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Function to generate SSL certificates for local development
generate_ssl_certs() {
    if [ "$DEPLOYMENT_MODE" != "cloud" ] && [ ! -f "$PROJECT_ROOT/certs/localhost.crt" ]; then
        echo -e "${YELLOW}Generating SSL certificates for local development...${NC}"
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$PROJECT_ROOT/certs/localhost.key" \
            -out "$PROJECT_ROOT/certs/localhost.crt" \
            -subj "/C=US/ST=State/L=City/O=AgnoVoice/CN=localhost"
        
        echo -e "${GREEN}✓ SSL certificates generated${NC}"
    fi
}

# Function to start voice service
start_voice_service() {
    echo -e "${YELLOW}Starting voice service in $DEPLOYMENT_MODE mode...${NC}"
    
    # Activate virtual environment
    source "$PROJECT_ROOT/venv_voice/bin/activate"
    
    # Export Python path
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # Start the service based on deployment mode
    if [ "$DOCKER_AVAILABLE" = true ] && [ -f "$PROJECT_ROOT/docker-compose.voice.yml" ]; then
        echo "Starting with Docker Compose..."
        docker-compose -f "$PROJECT_ROOT/docker-compose.voice.yml" up -d
    else
        echo "Starting with Python directly..."
        
        # Create FastAPI app file if it doesn't exist
        if [ ! -f "$VOICE_DIR/main.py" ]; then
            cat > "$VOICE_DIR/main.py" << 'EOF'
"""Main FastAPI application for Voice Service"""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from voice.core.service import VoiceService
from voice.webrtc.server import WebRTCVoiceServer
from voice.config.settings import get_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(title="Agno Voice Service", version="1.0.0")

# Load configuration
config = get_config()

# Initialize voice service
voice_service = VoiceService(config)
webrtc_server = WebRTCVoiceServer(voice_service)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy", "mode": config.mode}

# WebSocket endpoint for WebRTC signaling
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await webrtc_server.handle_websocket(websocket, client_id)

# Serve PWA files
@app.get("/")
async def root():
    return FileResponse("public/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        ssl_keyfile=config.ssl_key if config.use_ssl else None,
        ssl_certfile=config.ssl_cert if config.use_ssl else None
    )
EOF
        fi
        
        # Start the FastAPI server
        if [ "$DEPLOYMENT_MODE" = "local" ]; then
            SSL_ARGS=""
        else
            SSL_ARGS="--ssl-keyfile $PROJECT_ROOT/certs/localhost.key --ssl-certfile $PROJECT_ROOT/certs/localhost.crt"
        fi
        
        uvicorn voice.main:app \
            --host $HOST \
            --port $PORT \
            --reload \
            $SSL_ARGS &
        
        VOICE_PID=$!
        echo "Voice service started with PID: $VOICE_PID"
    fi
    
    echo -e "${GREEN}✓ Voice service started${NC}"
}

# Function to start PWA dev server
start_pwa_server() {
    echo -e "${YELLOW}Starting PWA development server...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if Next.js is configured
    if [ -f "package.json" ]; then
        # Install dependencies if needed
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        
        # Start Next.js dev server
        npm run dev &
        PWA_PID=$!
        echo "PWA server started with PID: $PWA_PID"
    else
        echo -e "${YELLOW}⚠ No package.json found, skipping PWA server${NC}"
    fi
    
    echo -e "${GREEN}✓ PWA server started${NC}"
}

# Function to display access information
display_info() {
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Agno Voice System Ready!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}Access Points:${NC}"
    
    if [ "$DEPLOYMENT_MODE" = "local" ]; then
        echo -e "  📱 PWA (Mobile): ${GREEN}http://localhost:3000/voice${NC}"
        echo -e "  🖥️  Desktop App: ${GREEN}http://localhost:3000${NC}"
        echo -e "  🔌 WebSocket: ${GREEN}ws://localhost:$PORT/ws${NC}"
    else
        echo -e "  📱 PWA (Mobile): ${GREEN}https://localhost:3000/voice${NC}"
        echo -e "  🖥️  Desktop App: ${GREEN}https://localhost:3000${NC}"
        echo -e "  🔌 WebSocket: ${GREEN}wss://localhost:$PORT/ws${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Voice Commands:${NC}"
    echo -e "  • 'Create a React component for...'"
    echo -e "  • 'Write a Python function that...'"
    echo -e "  • 'Build an API endpoint for...'"
    echo -e "  • 'Fix this error...'"
    echo -e "  • 'Explain this code...'"
    echo ""
    echo -e "${BLUE}Mobile Access:${NC}"
    echo -e "  1. Open Safari/Chrome on your phone"
    echo -e "  2. Navigate to the PWA URL above"
    echo -e "  3. Add to Home Screen for app-like experience"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    
    if [ ! -z "$VOICE_PID" ]; then
        kill $VOICE_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$PWA_PID" ]; then
        kill $PWA_PID 2>/dev/null || true
    fi
    
    if [ "$DOCKER_AVAILABLE" = true ]; then
        docker-compose -f "$PROJECT_ROOT/docker-compose.voice.yml" down 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✓ Services stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Main execution
main() {
    check_dependencies
    setup_environment
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --local)
                DEPLOYMENT_MODE="local"
                shift
                ;;
            --cloud)
                DEPLOYMENT_MODE="cloud"
                shift
                ;;
            --hybrid)
                DEPLOYMENT_MODE="hybrid"
                shift
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --help)
                echo "Usage: $0 [--local|--cloud|--hybrid] [--port PORT]"
                echo ""
                echo "Options:"
                echo "  --local   Run in local mode (Mac M3 optimized)"
                echo "  --cloud   Run in cloud mode (API-based)"
                echo "  --hybrid  Run in hybrid mode (default)"
                echo "  --port    Specify port (default: 8443)"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Update deployment mode
    export DEPLOYMENT_MODE
    
    # Continue with setup
    install_python_deps
    download_models
    generate_ssl_certs
    start_voice_service
    start_pwa_server
    display_info
    
    # Keep script running
    while true; do
        sleep 1
    done
}

# Run main function
main "$@"