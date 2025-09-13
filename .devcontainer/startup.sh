#!/bin/bash
# Sophia AI V9.7 - Bulletproof Startup Script
# This script ensures the development environment starts correctly every time

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging setup
LOG_FILE="/workspace/logs/startup.log"
mkdir -p /workspace/logs
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

# Error handling
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Startup script failed with exit code $exit_code"
        log_info "Check logs at: $LOG_FILE"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Start startup process
log_header "Sophia AI V9.7 Startup Process"
log_info "Starting at $(date)"
log_info "Workspace: $(pwd)"
log_info "User: $(whoami)"

# Phase 1: Validate Environment
log_header "Phase 1: Environment Validation"

# Check workspace directory
if [ ! -d "/workspace" ]; then
    log_error "Workspace directory /workspace does not exist!"
    exit 1
fi

if [ ! -w "/workspace" ]; then
    log_error "Workspace directory /workspace is not writable!"
    exit 1
fi

log_success "Workspace directory validated"

# Create necessary directories
log_info "Creating workspace structure..."
mkdir -p /workspace/{logs,data,.cache,.venv,backend,frontend,scripts,tests}
mkdir -p /workspace/.cache/{uv,pip,npm}

# Check required tools
log_info "Validating required tools..."

REQUIRED_TOOLS=("python3" "git" "curl" "docker" "node" "npm")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS+=("$tool")
        log_warning "$tool not found"
    else
        log_success "$tool found: $(command -v "$tool")"
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    log_warning "Missing tools: ${MISSING_TOOLS[*]}"
    log_info "Attempting to install missing tools..."
    
    # Try to install missing tools
    if command -v apt-get &> /dev/null; then
        sudo apt-get update || true
        for tool in "${MISSING_TOOLS[@]}"; do
            case "$tool" in
                "python3")
                    sudo apt-get install -y python3 python3-pip python3-venv || true
                    ;;
                "node")
                    sudo apt-get install -y nodejs || true
                    ;;
                "npm")
                    sudo apt-get install -y npm || true
                    ;;
                *)
                    sudo apt-get install -y "$tool" || true
                    ;;
            esac
        done
    fi
fi

# Phase 2: Python Environment Setup
log_header "Phase 2: Python Environment Setup"

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 || echo "Python not found")
log_info "Python version: $PYTHON_VERSION"

# Set up virtual environment
VENV_PATH="/workspace/.venv"
if [ ! -d "$VENV_PATH" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv "$VENV_PATH" || {
        log_warning "Failed to create venv with python3, trying python..."
        python -m venv "$VENV_PATH" || {
            log_error "Failed to create virtual environment"
            exit 1
        }
    }
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate" || {
    log_error "Failed to activate virtual environment"
    exit 1
}

log_success "Virtual environment activated"
log_info "Python path: $(which python)"
log_info "Pip path: $(which pip)"

# Phase 3: Dependency Installation
log_header "Phase 3: Dependency Installation"

# Check for requirements.txt
if [ -f "/workspace/requirements.txt" ]; then
    log_info "Found requirements.txt, installing dependencies..."
    
    # Try UV first (fastest)
    if command -v uv &> /dev/null; then
        log_info "Using UV package manager..."
        uv pip install -r /workspace/requirements.txt || {
            log_warning "UV installation failed, falling back to pip..."
            pip install -r /workspace/requirements.txt || {
                log_error "Failed to install Python dependencies"
                exit 1
            }
        }
    else
        log_info "Using pip package manager..."
        pip install --upgrade pip || true
        pip install -r /workspace/requirements.txt || {
            log_error "Failed to install Python dependencies"
            exit 1
        }
    fi
    
    log_success "Python dependencies installed"
else
    log_warning "No requirements.txt found, skipping Python dependency installation"
fi

# Install common development packages
log_info "Installing common development packages..."
pip install --upgrade pip setuptools wheel || true
pip install black pylint pytest fastapi uvicorn || true

# Phase 4: Node.js Setup (if frontend exists)
if [ -d "/workspace/frontend" ] && [ -f "/workspace/frontend/package.json" ]; then
    log_header "Phase 4: Node.js Frontend Setup"
    
    cd /workspace/frontend
    
    if [ ! -d "node_modules" ]; then
        log_info "Installing Node.js dependencies..."
        npm install --legacy-peer-deps || {
            log_warning "npm install failed, trying with --force..."
            npm install --force || {
                log_error "Failed to install Node.js dependencies"
                exit 1
            }
        }
        log_success "Node.js dependencies installed"
    else
        log_info "Node.js dependencies already installed"
    fi
    
    cd /workspace
else
    log_info "No frontend directory found, skipping Node.js setup"
fi

# Phase 5: Service Startup
log_header "Phase 5: Service Startup"

# Function to start service with Docker
start_docker_service() {
    local service_name=$1
    local docker_image=$2
    local port_mapping=$3
    local additional_args=${4:-""}
    
    log_info "Starting $service_name..."
    
    # Check if container already exists
    if docker ps -a --format "table {{.Names}}" | grep -q "^${service_name}$"; then
        log_info "$service_name container exists, checking status..."
        if docker ps --format "table {{.Names}}" | grep -q "^${service_name}$"; then
            log_success "$service_name is already running"
            return 0
        else
            log_info "Starting existing $service_name container..."
            docker start "$service_name" || {
                log_warning "Failed to start existing container, removing and recreating..."
                docker rm "$service_name" || true
            }
        fi
    fi
    
    # Start new container if needed
    if ! docker ps --format "table {{.Names}}" | grep -q "^${service_name}$"; then
        docker run -d --name "$service_name" $port_mapping $additional_args "$docker_image" || {
            log_error "Failed to start $service_name"
            return 1
        }
        
        # Wait for service to be ready
        sleep 5
        log_success "$service_name started successfully"
    fi
}

# Start database services
if command -v docker &> /dev/null && docker info &> /dev/null; then
    log_info "Docker is available, starting database services..."
    
    # PostgreSQL
    start_docker_service "postgres" "postgres:15-alpine" "-p 5432:5432" "-e POSTGRES_PASSWORD=password -e POSTGRES_DB=sophia_ai"
    
    # Redis
    start_docker_service "redis" "redis:7-alpine" "-p 6379:6379" ""
    
    # Qdrant
    start_docker_service "qdrant" "qdrant/qdrant:latest" "-p 6333:6333" "-v qdrant_storage:/qdrant/storage"
    
    # Neo4j
    start_docker_service "neo4j" "neo4j:5-community" "-p 7474:7474 -p 7687:7687" "-e NEO4J_AUTH=neo4j/password"
    
    log_success "Database services started"
else
    log_warning "Docker not available, skipping database service startup"
fi

# Phase 6: Health Checks
log_header "Phase 6: Health Checks"

# Function to check service health
check_service_health() {
    local service_name=$1
    local health_check=$2
    
    log_info "Checking $service_name health..."
    
    for i in {1..30}; do
        if eval "$health_check" &> /dev/null; then
            log_success "$service_name is healthy"
            return 0
        fi
        sleep 2
    done
    
    log_warning "$service_name health check failed"
    return 1
}

# Check database health
if command -v docker &> /dev/null; then
    check_service_health "PostgreSQL" "docker exec postgres pg_isready -U postgres"
    check_service_health "Redis" "docker exec redis redis-cli ping"
    check_service_health "Qdrant" "curl -f http://localhost:6333/health"
    check_service_health "Neo4j" "curl -f http://localhost:7474/"
fi

# Phase 7: Final Setup
log_header "Phase 7: Final Setup"

# Set up Git configuration if not already set
if [ -z "$(git config --global user.name 2>/dev/null || true)" ]; then
    log_info "Setting up Git configuration..."
    git config --global user.name "Sophia AI Developer" || true
    git config --global user.email "developer@sophia-ai.dev" || true
    git config --global init.defaultBranch main || true
    log_success "Git configuration set"
fi

# Create startup summary
log_header "Startup Summary"

echo -e "\n${GREEN}🎉 Sophia AI V9.7 Startup Complete!${NC}\n"

echo -e "${CYAN}📁 Workspace:${NC} /workspace"
echo -e "${CYAN}🐍 Python:${NC} $(python --version 2>&1)"
echo -e "${CYAN}📦 Virtual Environment:${NC} $VENV_PATH"
echo -e "${CYAN}🌐 Node.js:${NC} $(node --version 2>/dev/null || echo 'Not available')"

echo -e "\n${YELLOW}🔗 Available Services:${NC}"
echo -e "  • PostgreSQL: localhost:5432"
echo -e "  • Redis: localhost:6379"
echo -e "  • Qdrant: http://localhost:6333"
echo -e "  • Neo4j: http://localhost:7474"

echo -e "\n${YELLOW}📊 Development URLs:${NC}"
echo -e "  • Backend API: http://localhost:8000"
echo -e "  • Frontend: ${SOPHIA_FRONTEND_ENDPOINT}"
echo -e "  • API Docs: http://localhost:8000/docs"

echo -e "\n${YELLOW}📝 Logs:${NC}"
echo -e "  • Startup Log: $LOG_FILE"
echo -e "  • Service Logs: /workspace/logs/"

echo -e "\n${GREEN}✅ Ready for development!${NC}"

log_success "Startup completed at $(date)"

