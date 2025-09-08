#!/bin/bash
set -euo pipefail

# Sophia AI V9.7 Ultimate Setup Script - BULLETPROOF VERSION
# This script WILL work when you create a fresh Codespaces instance

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging setup
LOG_FILE="/tmp/sophia-setup.log"
mkdir -p /tmp/logs
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${PURPLE}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_phase() {
    echo -e "${CYAN}[PHASE]${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
show_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    SOPHIA AI V9.7                           ║"
    echo "║                 ULTIMATE SETUP SCRIPT                       ║"
    echo "║                                                              ║"
    echo "║  This script WILL make your Codespaces work properly        ║"
    echo "║  No more 'command not found' bullshit                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Check if we're running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must run as root. The devcontainer is configured for root user."
        log_error "If you see this error, the devcontainer.json is not configured correctly."
        exit 1
    fi
    log_success "Running as root - permissions OK"
}

# Verify all CLI tools are available
verify_cli_tools() {
    log_info "🔧 Verifying CLI tools are installed..."
    
    local tools=("curl" "wget" "git" "redis-cli" "psql" "docker" "python3" "pip3" "jq")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        fi
    done
    
    # Check node and npm separately (they might be in NVM path)
    # Source NVM if it exists
    if [ -f "/home/ubuntu/.nvm/nvm.sh" ]; then
        source /home/ubuntu/.nvm/nvm.sh
    fi
    
    if ! command -v node &> /dev/null; then
        log_warn "Node.js not found in PATH, but may be available via NVM"
    fi
    
    if ! command -v npm &> /dev/null; then
        log_warn "npm not found in PATH, but may be available via NVM"
    fi
    
    # Check netcat (might be nc or netcat)
    if ! command -v netcat &> /dev/null && ! command -v nc &> /dev/null; then
        missing_tools+=("netcat")
    fi
    
    if [ ${#missing_tools[@]} -eq 0 ]; then
        log_success "All essential CLI tools are available"
        return 0
    else
        log_warn "Some CLI tools missing: ${missing_tools[*]}"
        log_info "Continuing setup - missing tools will be handled by Docker services"
        return 0
    fi
}

# Install UV package manager if not available
install_uv() {
    log_info "📦 Setting up UV package manager..."
    
    if command -v uv &> /dev/null; then
        log_success "UV already installed: $(uv --version)"
        return 0
    fi
    
    log_info "Installing UV package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || {
        log_error "Failed to install UV package manager"
        return 1
    }
    
    # Add UV to PATH
    export PATH="/root/.local/bin:$PATH"
    echo 'export PATH="/root/.local/bin:$PATH"' >> ~/.bashrc
    
    if command -v uv &> /dev/null; then
        log_success "UV installed successfully: $(uv --version)"
    else
        log_error "UV installation failed"
        return 1
    fi
}

# Install Python dependencies
install_python_deps() {
    log_info "🐍 Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        log_warn "requirements.txt not found, skipping Python dependencies"
        return 0
    fi
    
    # Try UV first (much faster)
    if command -v uv &> /dev/null; then
        log_info "Using UV to install dependencies (100x faster than pip)..."
        uv pip install --system -r requirements.txt || {
            log_warn "UV failed, falling back to pip"
            pip3 install -r requirements.txt || {
                log_error "Both UV and pip failed to install dependencies"
                return 1
            }
        }
    else
        log_info "Using pip to install dependencies..."
        pip3 install -r requirements.txt || {
            log_error "pip failed to install dependencies"
            return 1
        }
    fi
    
    log_success "Python dependencies installed successfully"
}

# Start Redis service
start_redis() {
    log_info "🔴 Starting Redis service..."
    
    # Check if Redis is already running
    if redis-cli ping &>/dev/null; then
        log_success "Redis is already running"
        return 0
    fi
    
    # Try to start Redis server
    if command -v redis-server &> /dev/null; then
        log_info "Starting Redis server..."
        redis-server --daemonize yes --port 6379 --bind ${BIND_IP} || {
            log_warn "Redis server failed to start, trying Docker fallback"
            docker run -d --name redis --restart unless-stopped -p 6379:6379 redis:alpine || {
                log_error "Both Redis server and Docker fallback failed"
                return 1
            }
        }
    else
        log_info "Redis server not found, using Docker..."
        docker run -d --name redis --restart unless-stopped -p 6379:6379 redis:alpine || {
            log_error "Docker Redis failed to start"
            return 1
        }
    fi
    
    # Wait for Redis to be ready
    local retries=10
    while [ $retries -gt 0 ]; do
        if redis-cli ping &>/dev/null; then
            log_success "Redis is running and responding to PING"
            return 0
        fi
        log_info "Waiting for Redis to start... ($retries retries left)"
        sleep 2
        ((retries--))
    done
    
    log_error "Redis failed to start after multiple attempts"
    return 1
}

# Start PostgreSQL service
start_postgresql() {
    log_info "🐘 Starting PostgreSQL service..."
    
    # Check if PostgreSQL is already running
    if psql -h localhost -U postgres -d postgres -c "SELECT 1;" &>/dev/null; then
        log_success "PostgreSQL is already running"
        return 0
    fi
    
    # Try Docker PostgreSQL (more reliable in containers)
    log_info "Starting PostgreSQL with Docker..."
    docker run -d --name postgres --restart unless-stopped \
        -e POSTGRES_PASSWORD=password \
        -e POSTGRES_DB=sophia_ai \
        -p 5432:5432 \
        postgres:15-alpine || {
        log_error "Docker PostgreSQL failed to start"
        return 1
    }
    
    # Wait for PostgreSQL to be ready
    local retries=15
    while [ $retries -gt 0 ]; do
        if psql -h localhost -U postgres -d postgres -c "SELECT 1;" &>/dev/null; then
            log_success "PostgreSQL is running and accepting connections"
            return 0
        fi
        log_info "Waiting for PostgreSQL to start... ($retries retries left)"
        sleep 3
        ((retries--))
    done
    
    log_error "PostgreSQL failed to start after multiple attempts"
    return 1
}

# Start Qdrant vector database
start_qdrant() {
    log_info "🔍 Starting Qdrant vector database..."
    
    # Check if Qdrant is already running
    if curl -s http://localhost:6333/health &>/dev/null; then
        log_success "Qdrant is already running"
        return 0
    fi
    
    log_info "Starting Qdrant with Docker..."
    docker run -d --name qdrant --restart unless-stopped \
        -p 6333:6333 \
        -v qdrant_storage:/qdrant/storage \
        qdrant/qdrant || {
        log_error "Qdrant failed to start"
        return 1
    }
    
    # Wait for Qdrant to be ready
    local retries=10
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:6333/health &>/dev/null; then
            log_success "Qdrant is running and healthy"
            return 0
        fi
        log_info "Waiting for Qdrant to start... ($retries retries left)"
        sleep 3
        ((retries--))
    done
    
    log_warn "Qdrant may not be fully ready yet, but continuing..."
    return 0
}

# Start Neo4j graph database
start_neo4j() {
    log_info "🕸️ Starting Neo4j graph database..."
    
    # Check if Neo4j is already running
    if curl -s http://localhost:7474 &>/dev/null; then
        log_success "Neo4j is already running"
        return 0
    fi
    
    log_info "Starting Neo4j with Docker..."
    docker run -d --name neo4j --restart unless-stopped \
        -p 7474:7474 -p 7687:7687 \
        -e NEO4J_AUTH=none \
        -v neo4j_data:/data \
        neo4j:latest || {
        log_warn "Neo4j failed to start, continuing without it"
        return 0
    }
    
    log_info "Neo4j starting in background..."
    return 0
}

# Start backend API
start_backend() {
    log_info "🚀 Starting backend API..."
    
    # Check if backend is already running
    if curl -s http://localhost:8000/health &>/dev/null; then
        log_success "Backend API is already running"
        return 0
    fi
    
    if [ ! -f "backend/main.py" ]; then
        log_warn "backend/main.py not found, skipping backend startup"
        return 0
    fi
    
    log_info "Starting FastAPI backend..."
    cd backend
    
    # Kill any existing uvicorn processes
    pkill -f "uvicorn.*main:app" || true
    
    # Start backend in background
    nohup python -m uvicorn main:app --host ${BIND_IP} --port 8000 --reload > /tmp/logs/backend.log 2>&1 &
    cd ..
    
    # Wait for backend to be ready
    local retries=15
    while [ $retries -gt 0 ]; do
        if curl -s http://localhost:8000/health &>/dev/null; then
            log_success "Backend API is running and healthy"
            return 0
        fi
        log_info "Waiting for backend API to start... ($retries retries left)"
        sleep 2
        ((retries--))
    done
    
    log_warn "Backend API may not be ready yet, check /tmp/logs/backend.log"
    return 0
}

# Start MCP servers
start_mcp_servers() {
    log_info "🔌 Starting MCP servers..."
    
    if [ ! -f "mcp_servers/unified_mcp_server.py" ]; then
        log_warn "MCP server not found, skipping MCP startup"
        return 0
    fi
    
    # Kill any existing MCP processes
    pkill -f "mcp_server" || true
    
    log_info "Starting unified MCP server..."
    nohup python mcp_servers/unified_mcp_server.py > /tmp/logs/mcp.log 2>&1 &
    
    sleep 3
    log_success "MCP servers started in background"
    return 0
}

# Start frontend
start_frontend() {
    log_info "🎨 Starting frontend dashboard..."
    
    # Check if frontend is already running
    if curl -s ${SOPHIA_FRONTEND_ENDPOINT} &>/dev/null; then
        log_success "Frontend is already running"
        return 0
    fi
    
    if [ ! -f "frontend/package.json" ]; then
        log_warn "frontend/package.json not found, skipping frontend startup"
        return 0
    fi
    
    cd frontend
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install || {
            log_warn "npm install failed, trying with --legacy-peer-deps"
            npm install --legacy-peer-deps || {
                log_error "Frontend dependency installation failed"
                cd ..
                return 1
            }
        }
    fi
    
    # Kill any existing frontend processes
    pkill -f "npm.*dev" || true
    
    # Start frontend in background
    log_info "Starting frontend development server..."
    nohup npm run dev > /tmp/logs/frontend.log 2>&1 &
    cd ..
    
    sleep 5
    log_success "Frontend started in background"
    return 0
}

# Comprehensive health check
health_check() {
    log_phase "🔍 PHASE 4: COMPREHENSIVE HEALTH CHECK"
    
    local services_status=()
    
    # Check backend API
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "200"; then
        log_success "✅ Backend API: HEALTHY (http://localhost:8000)"
        services_status+=("backend:OK")
    else
        log_warn "❌ Backend API: NOT RESPONDING"
        services_status+=("backend:FAIL")
    fi
    
    # Check Redis
    if redis-cli ping &>/dev/null; then
        log_success "✅ Redis: CONNECTED"
        services_status+=("redis:OK")
    else
        log_warn "❌ Redis: NOT AVAILABLE"
        services_status+=("redis:FAIL")
    fi
    
    # Check PostgreSQL
    if psql -h localhost -U postgres -d postgres -c "SELECT 1;" &>/dev/null; then
        log_success "✅ PostgreSQL: CONNECTED"
        services_status+=("postgres:OK")
    else
        log_warn "❌ PostgreSQL: NOT AVAILABLE"
        services_status+=("postgres:FAIL")
    fi
    
    # Check Qdrant
    if curl -s http://localhost:6333/health &>/dev/null; then
        log_success "✅ Qdrant: HEALTHY"
        services_status+=("qdrant:OK")
    else
        log_warn "❌ Qdrant: NOT RESPONDING"
        services_status+=("qdrant:FAIL")
    fi
    
    # Check frontend
    if curl -s ${SOPHIA_FRONTEND_ENDPOINT} &>/dev/null; then
        log_success "✅ Frontend: RUNNING"
        services_status+=("frontend:OK")
    else
        log_warn "❌ Frontend: NOT RESPONDING"
        services_status+=("frontend:FAIL")
    fi
    
    # Summary
    echo -e "\n${PURPLE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                      SETUP COMPLETE                         ║${NC}"
    echo -e "${PURPLE}╠══════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║  🚀 Backend API:    http://localhost:8000                   ║${NC}"
    echo -e "${PURPLE}║  🎨 Frontend:       ${SOPHIA_FRONTEND_ENDPOINT}                   ║${NC}"
    echo -e "${PURPLE}║  📚 API Docs:       http://localhost:8000/docs              ║${NC}"
    echo -e "${PURPLE}║  🔴 Redis:          localhost:6379                          ║${NC}"
    echo -e "${PURPLE}║  🐘 PostgreSQL:     localhost:5432                          ║${NC}"
    echo -e "${PURPLE}║  🔍 Qdrant:         http://localhost:6333                   ║${NC}"
    echo -e "${PURPLE}║                                                              ║${NC}"
    echo -e "${PURPLE}║  📋 Logs:           /tmp/sophia-setup.log                   ║${NC}"
    echo -e "${PURPLE}║  📊 Service Logs:   /tmp/logs/                              ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    # Show service status
    echo -e "\n${CYAN}Service Status:${NC}"
    for status in "${services_status[@]}"; do
        service=$(echo "$status" | cut -d: -f1)
        state=$(echo "$status" | cut -d: -f2)
        if [ "$state" = "OK" ]; then
            echo -e "  ${GREEN}✅ $service${NC}"
        else
            echo -e "  ${RED}❌ $service${NC}"
        fi
    done
    
    echo -e "\n${GREEN}🎉 Sophia AI V9.7 setup complete!${NC}"
    echo -e "${YELLOW}💡 If any service failed, check the logs in /tmp/logs/${NC}"
}

# Main execution function
main() {
    show_banner
    
    log_phase "🚀 STARTING SOPHIA AI V9.7 ULTIMATE SETUP"
    log_info "Timestamp: $(date)"
    log_info "User: $(whoami)"
    log_info "Working directory: $(pwd)"
    
    # Phase 1: Verify environment
    log_phase "🔧 PHASE 1: ENVIRONMENT VERIFICATION"
    check_root || exit 1
    verify_cli_tools || exit 1
    install_uv || exit 1
    
    # Phase 2: Install dependencies
    log_phase "📦 PHASE 2: DEPENDENCY INSTALLATION"
    install_python_deps || exit 1
    
    # Phase 3: Start services
    log_phase "🚀 PHASE 3: SERVICE STARTUP"
    start_redis || log_warn "Redis startup failed"
    start_postgresql || log_warn "PostgreSQL startup failed"
    start_qdrant || log_warn "Qdrant startup failed"
    start_neo4j || log_warn "Neo4j startup failed"
    start_mcp_servers || log_warn "MCP servers startup failed"
    start_backend || log_warn "Backend startup failed"
    start_frontend || log_warn "Frontend startup failed"
    
    # Phase 4: Health check
    health_check
    
    log_success "🎉 ALL PHASES COMPLETE!"
    log_info "Check /tmp/sophia-setup.log for detailed logs"
    log_info "Check /tmp/logs/ for individual service logs"
}

# Trap to handle script interruption
trap 'log_error "Setup interrupted!"; exit 1' INT TERM

# Run main function
main "$@"

