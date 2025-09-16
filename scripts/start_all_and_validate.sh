#!/bin/bash
# Sophia Intel AI - Unified Startup and Validation Script
# Loads .env.master, starts all services, and validates health

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env.master"
API_PORT=8000
MCP_MEMORY_PORT=8081
MCP_FS_PORT=8082
MCP_GIT_PORT=8084
REDIS_PORT=6379
WEAVIATE_PORT=8080

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_port() {
    local port=$1
    local name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    log_info "Waiting for $name to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            log_success "$name is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
        echo -n "."
    done
    echo ""
    log_error "$name failed to start after $((max_attempts * 2)) seconds"
    return 1
}

# Check environment
check_environment() {
    log_info "Checking environment configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env.master not found"
        log_info "Creating template .env.master..."
        cat > "$ENV_FILE" << 'EOF'
# Sophia Intel AI Environment Configuration
# Edit this file with your actual API keys

# Primary AI Gateway
PORTKEY_API_KEY=your_portkey_api_key_here

# Provider API Keys (optional if using Portkey)
OPENROUTER_API_KEY=your_openrouter_key_here
TOGETHER_API_KEY=your_together_key_here

# Environment
ENVIRONMENT=development
SOPHIA_ENV=local

# Database URLs (optional)
REDIS_URL=redis://localhost:6379
WEAVIATE_URL=http://localhost:8080

# CORS (for local development)
CORS_ORIGINS=http://localhost,http://localhost:3000,http://127.0.0.1:3000
EOF
        chmod 600 "$ENV_FILE"
        log_warning "Please edit $ENV_FILE with your actual API keys and re-run this script"
        exit 1
    fi
    
    chmod 600 "$ENV_FILE"
    log_success "Found $ENV_FILE"
    
    # Load environment
    set -a
    source "$ENV_FILE"
    set +a
    
    # Check critical keys
    if [ -z "$PORTKEY_API_KEY" ] || [ "$PORTKEY_API_KEY" = "your_portkey_api_key_here" ]; then
        log_warning "PORTKEY_API_KEY not configured (some features may not work)"
    else
        log_success "PORTKEY_API_KEY configured"
    fi
}

# Install dependencies
check_dependencies() {
    log_info "Checking Python dependencies..."
    
    if ! command -v python &> /dev/null; then
        log_error "Python not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Check if we're in a virtual environment or system Python
    if [ -f "pyproject.toml" ]; then
        log_info "Installing dependencies from pyproject.toml..."
        pip install -e . >/dev/null 2>&1 || {
            log_warning "pip install failed, trying with --user flag..."
            pip install --user -e . >/dev/null 2>&1 || log_warning "Could not install dependencies"
        }
    elif [ -f "requirements.txt" ]; then
        log_info "Installing dependencies from requirements.txt..."
        pip install -r requirements.txt >/dev/null 2>&1 || log_warning "Could not install dependencies"
    fi
    
    log_success "Dependencies checked"
}

# Start MCP servers in background
start_mcp_servers() {
    log_info "Starting MCP servers..."
    
    # Memory server
    if check_port $MCP_MEMORY_PORT "MCP Memory"; then
        log_warning "Port $MCP_MEMORY_PORT already in use, skipping MCP Memory server"
    else
        log_info "Starting MCP Memory server on port $MCP_MEMORY_PORT..."
        python -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port $MCP_MEMORY_PORT >/dev/null 2>&1 &
        echo $! > .pids/mcp_memory.pid
    fi
    
    # Filesystem server  
    if check_port $MCP_FS_PORT "MCP Filesystem"; then
        log_warning "Port $MCP_FS_PORT already in use, skipping MCP Filesystem server"
    else
        log_info "Starting MCP Filesystem server on port $MCP_FS_PORT..."
        python -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port $MCP_FS_PORT >/dev/null 2>&1 &
        echo $! > .pids/mcp_fs.pid
    fi
    
    # Git server
    if check_port $MCP_GIT_PORT "MCP Git"; then
        log_warning "Port $MCP_GIT_PORT already in use, skipping MCP Git server"
    else
        log_info "Starting MCP Git server on port $MCP_GIT_PORT..."
        python -m uvicorn mcp.git.server:app --host 0.0.0.0 --port $MCP_GIT_PORT >/dev/null 2>&1 &
        echo $! > .pids/mcp_git.pid
    fi
    
    # Wait for MCP servers
    sleep 3
    log_success "MCP servers started"
}

# Start main API server
start_api_server() {
    log_info "Starting main API server..."
    
    if check_port $API_PORT "API"; then
        log_warning "Port $API_PORT already in use, API server may already be running"
        return 0
    fi
    
    log_info "Starting API server on port $API_PORT..."
    python -m uvicorn app.api.main:app --host 0.0.0.0 --port $API_PORT --reload >/dev/null 2>&1 &
    echo $! > .pids/api.pid
    
    # Wait for API server
    wait_for_service "http://localhost:$API_PORT/health" "API Server"
}

# Validate all services
validate_services() {
    log_info "Validating all services..."
    
    local all_good=true
    
    # API Server
    if curl -sf "http://localhost:$API_PORT/health" >/dev/null 2>&1; then
        log_success "API Server (port $API_PORT)"
    else
        log_error "API Server (port $API_PORT)"
        all_good=false
    fi
    
    # Dashboard
    if curl -sf "http://localhost:$API_PORT/dashboard" >/dev/null 2>&1; then
        log_success "Dashboard UI"
    else
        log_error "Dashboard UI"
        all_good=false
    fi
    
    # API Documentation
    if curl -sf "http://localhost:$API_PORT/docs" >/dev/null 2>&1; then
        log_success "API Documentation"
    else
        log_error "API Documentation"
        all_good=false
    fi
    
    # MCP Services
    if curl -sf "http://localhost:$MCP_MEMORY_PORT/health" >/dev/null 2>&1; then
        log_success "MCP Memory Server (port $MCP_MEMORY_PORT)"
    else
        log_error "MCP Memory Server (port $MCP_MEMORY_PORT)"
        all_good=false
    fi
    
    if curl -sf "http://localhost:$MCP_FS_PORT/health" >/dev/null 2>&1; then
        log_success "MCP Filesystem Server (port $MCP_FS_PORT)"
    else
        log_error "MCP Filesystem Server (port $MCP_FS_PORT)"
        all_good=false
    fi
    
    if curl -sf "http://localhost:$MCP_GIT_PORT/health" >/dev/null 2>&1; then
        log_success "MCP Git Server (port $MCP_GIT_PORT)"
    else
        log_error "MCP Git Server (port $MCP_GIT_PORT)"
        all_good=false
    fi
    
    # Optional services (don't fail on these)
    if check_port $REDIS_PORT "Redis"; then
        log_success "Redis (port $REDIS_PORT) - optional"
    else
        log_warning "Redis (port $REDIS_PORT) - optional service not running"
    fi
    
    if check_port $WEAVIATE_PORT "Weaviate"; then
        log_success "Weaviate (port $WEAVIATE_PORT) - optional"
    else
        log_warning "Weaviate (port $WEAVIATE_PORT) - optional service not running"
    fi
    
    if [ "$all_good" = true ]; then
        log_success "All core services validated successfully!"
        return 0
    else
        log_error "Some services failed validation"
        return 1
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    if [ -d ".pids" ]; then
        for pidfile in .pids/*.pid; do
            if [ -f "$pidfile" ]; then
                pid=$(cat "$pidfile")
                if kill -0 "$pid" 2>/dev/null; then
                    log_info "Stopping process $pid"
                    kill "$pid" 2>/dev/null || true
                fi
                rm -f "$pidfile"
            fi
        done
        rmdir .pids 2>/dev/null || true
    fi
}

# Show usage
usage() {
    echo "Sophia Intel AI - Unified Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --validate-only    Only validate running services, don't start new ones"
    echo "  --stop            Stop all services and exit"
    echo "  --help            Show this help message"
    echo ""
    echo "Default: Start all services and validate"
}

# Main execution
main() {
    local validate_only=false
    local stop_services=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --validate-only)
                validate_only=true
                shift
                ;;
            --stop)
                stop_services=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Handle stop request
    if [ "$stop_services" = true ]; then
        cleanup
        log_success "All services stopped"
        exit 0
    fi
    
    # Create pids directory
    mkdir -p .pids
    
    # Set up cleanup trap
    trap cleanup EXIT INT TERM
    
    log_info "🚀 Starting Sophia Intel AI Platform..."
    
    # Check environment
    check_environment
    
    if [ "$validate_only" = false ]; then
        # Check dependencies
        check_dependencies
        
        # Start services
        start_mcp_servers
        start_api_server
    fi
    
    # Validate everything
    if validate_services; then
        echo ""
        log_success "🎉 Sophia Intel AI is running!"
        echo ""
        echo -e "${BLUE}📊 Dashboard:      ${NC}http://localhost:$API_PORT/dashboard"
        echo -e "${BLUE}📚 API Docs:       ${NC}http://localhost:$API_PORT/docs" 
        echo -e "${BLUE}🔍 Health Check:   ${NC}http://localhost:$API_PORT/health"
        echo -e "${BLUE}🧠 MCP Memory:     ${NC}http://localhost:$MCP_MEMORY_PORT"
        echo -e "${BLUE}📁 MCP Filesystem: ${NC}http://localhost:$MCP_FS_PORT"
        echo -e "${BLUE}🔀 MCP Git:        ${NC}http://localhost:$MCP_GIT_PORT"
        echo ""
        if [ "$validate_only" = false ]; then
            log_info "Press Ctrl+C to stop all services"
            wait
        fi
    else
        log_error "Service validation failed"
        exit 1
    fi
}

# Run main function
main "$@"
