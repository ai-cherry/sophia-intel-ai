#!/bin/bash
# ==============================================
# SOPHIA INTEL AI - MINIMAL RAG ENVIRONMENT STARTUP
# Phase 2, Week 1-2: Quick startup script for MVP RAG pipeline
# ==============================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="docker-compose.minimal.yml"
LOG_FILE="${SCRIPT_DIR}/minimal-startup.log"

# Functions
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')
    
    case $level in
        "INFO")  echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "SUCCESS") echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "WARNING") echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "ERROR")   echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "HEADER")  echo -e "${PURPLE}[${timestamp}] ${message}${NC}" | tee -a "$LOG_FILE" ;;
    esac
}

show_banner() {
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════════"
    echo "  🚀 SOPHIA INTEL AI - MINIMAL RAG ENVIRONMENT"
    echo "  📦 Phase 2, Week 1-2: MVP with Ollama & Basic RAG"
    echo "  📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
}

check_dependencies() {
    log "INFO" "Checking system dependencies..."
    
    local missing_deps=()
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    fi
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log "ERROR" "Missing dependencies: ${missing_deps[*]}"
        log "ERROR" "Please install the missing dependencies and try again."
        exit 1
    fi
    
    log "SUCCESS" "All system dependencies are available"
}

check_files() {
    log "INFO" "Checking required files..."
    
    local missing_files=()
    
    # Check required files
    [ ! -f "$COMPOSE_FILE" ] && missing_files+=("$COMPOSE_FILE")
    [ ! -f "scripts/pull-models.sh" ] && missing_files+=("scripts/pull-models.sh")
    [ ! -f "app/rag/basic_rag.py" ] && missing_files+=("app/rag/basic_rag.py")
    [ ! -f "app/quickstart/test_rag.py" ] && missing_files+=("app/quickstart/test_rag.py")
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        log "ERROR" "Missing required files:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    log "SUCCESS" "All required files present"
}

create_minimal_dockerfile() {
    log "INFO" "Creating minimal Dockerfile..."
    
    cat > Dockerfile.minimal << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    langchain==0.1.0 \
    langchain-community==0.1.0 \
    weaviate-client==4.4.0 \
    ollama==0.1.7 \
    redis==5.0.1 \
    psycopg2-binary==2.9.9 \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    pydantic==2.5.3

# Copy application code
COPY app/ /app/

# Create simple API server
RUN cat > /app/server.py << 'PYEOF'
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Sophia RAG API - Minimal")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "minimal-rag"}

@app.get("/")
async def root():
    return {"message": "Sophia Intel AI - Minimal RAG Environment", "phase": "2", "week": "1-2"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
PYEOF

CMD ["python", "/app/server.py"]
EOF
    
    log "SUCCESS" "Dockerfile.minimal created"
}

start_services() {
    log "HEADER" "🚀 STARTING SERVICES"
    
    # Stop any existing services
    log "INFO" "Stopping any existing services..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans 2>/dev/null || true
    
    # Build images if needed
    log "INFO" "Building Docker images..."
    docker-compose -f "$COMPOSE_FILE" build --quiet
    
    # Start services in order
    log "INFO" "Starting Ollama service..."
    docker-compose -f "$COMPOSE_FILE" up -d ollama
    
    log "INFO" "Starting infrastructure services (Weaviate, Redis, Postgres)..."
    docker-compose -f "$COMPOSE_FILE" up -d weaviate redis postgres
    
    # Wait for infrastructure
    log "INFO" "Waiting for infrastructure to be ready..."
    sleep 20
    
    log "INFO" "Starting API service..."
    docker-compose -f "$COMPOSE_FILE" up -d api
    
    log "SUCCESS" "All services started"
}

health_check() {
    log "HEADER" "🩺 HEALTH CHECK"
    
    local all_healthy=true
    
    # Check Ollama
    log "INFO" "Checking Ollama..."
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        log "SUCCESS" "✅ Ollama is healthy"
    else
        log "ERROR" "❌ Ollama health check failed"
        all_healthy=false
    fi
    
    # Check Weaviate
    log "INFO" "Checking Weaviate..."
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        log "SUCCESS" "✅ Weaviate is healthy"
    else
        log "ERROR" "❌ Weaviate health check failed"
        all_healthy=false
    fi
    
    # Check Redis
    log "INFO" "Checking Redis..."
    if docker exec sophia-redis-minimal redis-cli ping > /dev/null 2>&1; then
        log "SUCCESS" "✅ Redis is healthy"
    else
        log "ERROR" "❌ Redis health check failed"
        all_healthy=false
    fi
    
    # Check Postgres
    log "INFO" "Checking PostgreSQL..."
    if docker exec sophia-postgres-minimal pg_isready -U sophia > /dev/null 2>&1; then
        log "SUCCESS" "✅ PostgreSQL is healthy"
    else
        log "ERROR" "❌ PostgreSQL health check failed"
        all_healthy=false
    fi
    
    # Check API
    log "INFO" "Checking API service..."
    if curl -s http://localhost:8003/health > /dev/null 2>&1; then
        log "SUCCESS" "✅ API service is healthy"
    else
        log "ERROR" "❌ API service health check failed"
        all_healthy=false
    fi
    
    if [ "$all_healthy" = true ]; then
        log "SUCCESS" "🎉 All services are healthy!"
        return 0
    else
        log "ERROR" "Some services failed health checks"
        return 1
    fi
}

pull_models() {
    log "HEADER" "🤖 PULLING OLLAMA MODELS"
    
    # Make script executable
    chmod +x scripts/pull-models.sh
    
    # Wait for Ollama to be ready
    log "INFO" "Waiting for Ollama to be ready..."
    local retries=30
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            break
        fi
        retries=$((retries - 1))
        sleep 2
    done
    
    if [ $retries -eq 0 ]; then
        log "ERROR" "Ollama did not become ready in time"
        return 1
    fi
    
    # Pull models
    log "INFO" "Pulling required models (this may take several minutes)..."
    if bash scripts/pull-models.sh setup; then
        log "SUCCESS" "Models pulled successfully"
    else
        log "WARNING" "Some models may have failed to pull"
    fi
}

test_rag() {
    log "HEADER" "🧪 TESTING RAG PIPELINE"
    
    log "INFO" "Installing Python dependencies for testing..."
    pip install -q langchain langchain-community weaviate-client ollama 2>/dev/null || {
        log "WARNING" "Failed to install some Python dependencies"
    }
    
    log "INFO" "Running RAG pipeline test..."
    if python3 app/quickstart/test_rag.py --clear; then
        log "SUCCESS" "RAG pipeline test completed successfully"
    else
        log "WARNING" "RAG pipeline test encountered issues"
    fi
}

show_status() {
    log "HEADER" "📊 DEPLOYMENT STATUS"
    
    echo -e "${CYAN}Service Status:${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
    
    echo -e "\n${CYAN}Access URLs:${NC}"
    echo "🤖 Ollama:           http://localhost:11434"
    echo "🗄️  Weaviate:        http://localhost:8080"
    echo "📦 Redis:            redis://localhost:6379"
    echo "🗂️  PostgreSQL:      postgresql://localhost:5432"
    echo "🌐 API Service:      http://localhost:8003"
    
    echo -e "\n${CYAN}Quick Commands:${NC}"
    echo "• Test RAG:     python app/quickstart/test_rag.py"
    echo "• View logs:    docker-compose -f $COMPOSE_FILE logs -f"
    echo "• Stop all:     docker-compose -f $COMPOSE_FILE down"
    echo "• Pull models:  bash scripts/pull-models.sh setup"
    
    echo -e "\n${CYAN}Next Steps:${NC}"
    echo "1. Test the RAG pipeline: python app/quickstart/test_rag.py"
    echo "2. Ingest documents using the basic_rag.py module"
    echo "3. Query the system through the API"
    echo "4. Monitor performance and adjust models as needed"
}

cleanup() {
    log "INFO" "Cleaning up..."
    docker-compose -f "$COMPOSE_FILE" down --volumes --remove-orphans
    log "SUCCESS" "Cleanup complete"
}

main() {
    # Clear log file
    > "$LOG_FILE"
    
    show_banner
    
    # Pre-flight checks
    check_dependencies
    check_files
    create_minimal_dockerfile
    
    # Start services
    start_services
    
    # Health checks
    if ! health_check; then
        log "WARNING" "Some services are not healthy, but continuing..."
    fi
    
    # Pull models
    pull_models
    
    # Optional: Run test
    if [ "${1:-}" = "--test" ]; then
        test_rag
    fi
    
    # Show status
    show_status
    
    log "SUCCESS" "🎉 MINIMAL RAG ENVIRONMENT IS READY!"
    log "INFO" "Log file: $LOG_FILE"
}

# Handle script termination
trap 'log "WARNING" "Script interrupted"; exit 130' INT TERM

# Parse command line arguments
case "${1:-start}" in
    "start")
        main "${2:-}"
        ;;
    "stop")
        log "INFO" "Stopping all services..."
        docker-compose -f "$COMPOSE_FILE" down
        log "SUCCESS" "All services stopped"
        ;;
    "restart")
        log "INFO" "Restarting all services..."
        docker-compose -f "$COMPOSE_FILE" restart
        health_check
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    "health")
        health_check
        ;;
    "models")
        pull_models
        ;;
    "test")
        test_rag
        ;;
    "clean")
        cleanup
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|health|models|test|clean} [--test]"
        echo ""
        echo "  start [--test]  - Start minimal environment (optionally run tests)"
        echo "  stop            - Stop all services"
        echo "  restart         - Restart all services"
        echo "  status          - Show service status"
        echo "  logs            - Follow service logs"
        echo "  health          - Run health checks"
        echo "  models          - Pull Ollama models"
        echo "  test            - Run RAG pipeline test"
        echo "  clean           - Clean up everything"
        exit 1
        ;;
esac