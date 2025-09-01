#!/bin/bash

# ==============================================
# Sophia Intel AI - Natural Language Interface Startup
# Phase 2, Week 3-4: NL Interface with n8n workflows
# ==============================================

set -e

echo "================================================"
echo "Sophia Intel AI - Natural Language Interface"
echo "Phase 2 Week 3-4 Implementation"
echo "================================================"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Function to check service health
check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for $service..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            echo " ✅"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo " ⚠️ (timeout)"
    return 1
}

# Stop any existing containers
echo "Stopping any existing containers..."
docker-compose -f docker-compose.minimal.yml down 2>/dev/null || true

# Start services
echo "Starting services..."
docker-compose -f docker-compose.minimal.yml up -d

# Wait for services to be ready
echo ""
echo "Checking service health..."
check_service "Ollama" "http://localhost:11434/api/tags"
check_service "Weaviate" "http://localhost:8080/v1/.well-known/ready"
check_service "Redis" "http://localhost:6379"
check_service "PostgreSQL" "http://localhost:5432"
check_service "n8n" "http://localhost:5678/healthz"

# Pull Ollama models if needed
echo ""
echo "Checking Ollama models..."
if docker exec sophia-ollama ollama list | grep -q "llama3.2"; then
    echo "✅ Llama 3.2 model already available"
else
    echo "Pulling Llama 3.2 model..."
    docker exec sophia-ollama ollama pull llama3.2:3b
fi

# Start the API server
echo ""
echo "Starting Natural Language API server..."
cd /Users/lynnmusil/sophia-intel-ai
python -m uvicorn app.main_nl:app --host 0.0.0.0 --port 8003 --reload &
API_PID=$!
echo "API server PID: $API_PID"

# Wait for API to be ready
sleep 5
check_service "NL API" "http://localhost:8003/health"

# Start Streamlit UI
echo ""
echo "Starting Streamlit Chat UI..."
streamlit run app/ui/streamlit_chat.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID"

# Wait for Streamlit to be ready
sleep 5

# Display access information
echo ""
echo "================================================"
echo "✅ Natural Language Interface is ready!"
echo "================================================"
echo ""
echo "Access Points:"
echo "  📡 API Server:        http://localhost:8003"
echo "  📚 API Documentation: http://localhost:8003/docs"
echo "  💬 Chat Interface:    http://localhost:8501"
echo "  🔧 n8n Workflows:     http://localhost:5678"
echo "  🗄️ Weaviate:         http://localhost:8080"
echo "  🧠 Ollama:           http://localhost:11434"
echo ""
echo "Quick Test Commands:"
echo "  1. Test NLP: python app/nl_interface/test_nl.py --quick"
echo "  2. Full test: python app/nl_interface/test_nl.py"
echo "  3. Chat UI: Open http://localhost:8501 in your browser"
echo ""
echo "Example NL Commands:"
echo "  - 'show system status'"
echo "  - 'run agent researcher'"
echo "  - 'scale redis to 3'"
echo "  - 'list all agents'"
echo "  - 'help'"
echo ""
echo "To stop all services:"
echo "  kill $API_PID $STREAMLIT_PID"
echo "  docker-compose -f docker-compose.minimal.yml down"
echo ""
echo "================================================"

# Keep script running
wait $API_PID $STREAMLIT_PID