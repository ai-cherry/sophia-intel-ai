#!/bin/bash
set -euo pipefail

# Lambda Labs Initialization Script for Sophia AI
# Audit-compliant startup with comprehensive error handling

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/lambda-init.log"
TIMEOUT_SECONDS=300
MAX_RETRIES=3

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Cleanup function
cleanup() {
    log "Cleaning up temporary files..."
    # Add cleanup logic here
}
trap cleanup EXIT

# Health check function
health_check() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    log "Health checking $service on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" >/dev/null 2>&1; then
            log "✅ $service is healthy"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: $service not ready, waiting..."
        sleep 5
        ((attempt++))
    done
    
    error_exit "$service failed health check after $max_attempts attempts"
}

# Environment validation
validate_environment() {
    log "Validating environment variables..."
    
    local required_vars=(
        "LAMBDA_API_KEY"
        "PORTKEY_API_KEY"
        "OPENROUTER_API_KEY"
        "REDIS_URL"
        "DATABASE_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            error_exit "Required environment variable $var is not set"
        fi
        log "✅ $var is configured"
    done
    
    # Optional variables with warnings
    local optional_vars=(
        "MCP_KEY"
        "DOCKER_TOKEN"
        "LAMBDA_SSH_KEY"
        "LAMBDA_SSH_KEY_NAME"
        "SLACK_WEBHOOK_URL"
    )
    
    for var in "${optional_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log "⚠️  Optional variable $var is not set"
        else
            log "✅ $var is configured"
        fi
    done
}

# System dependencies
install_dependencies() {
    log "Installing system dependencies..."
    
    # Update package list
    sudo apt-get update -qq || error_exit "Failed to update package list"
    
    # Install required packages
    local packages=(
        "curl"
        "jq"
        "redis-tools"
        "postgresql-client"
        "htop"
        "nvtop"
        "docker.io"
    )
    
    for package in "${packages[@]}"; do
        if ! dpkg -l | grep -q "^ii  $package "; then
            log "Installing $package..."
            sudo apt-get install -y "$package" || error_exit "Failed to install $package"
        else
            log "✅ $package already installed"
        fi
    done
}

# Python environment setup
setup_python_environment() {
    log "Setting up Python environment..."
    
    # Install UV package manager if not present
    if ! command -v uv &> /dev/null; then
        log "Installing UV package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh || error_exit "Failed to install UV"
        source "$HOME/.cargo/env"
    fi
    
    # Install Python dependencies
    if [[ -f "requirements.txt" ]]; then
        log "Installing Python dependencies with UV..."
        uv pip install --system -r requirements.txt || error_exit "Failed to install Python dependencies"
    else
        log "⚠️  No requirements.txt found, skipping Python dependencies"
    fi
}

# Database initialization
initialize_databases() {
    log "Initializing databases..."
    
    # Start Redis if not running
    if ! pgrep redis-server > /dev/null; then
        log "Starting Redis server..."
        sudo systemctl start redis-server || error_exit "Failed to start Redis"
        sudo systemctl enable redis-server
    fi
    
    # Test Redis connection
    if ! redis-cli ping > /dev/null 2>&1; then
        error_exit "Redis is not responding"
    fi
    log "✅ Redis is running"
    
    # Test PostgreSQL connection
    if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        log "⚠️  PostgreSQL not available locally, using remote connection"
    else
        log "✅ PostgreSQL is available"
    fi
    
    # Start Qdrant vector database
    if ! docker ps | grep -q qdrant; then
        log "Starting Qdrant vector database..."
        docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest || error_exit "Failed to start Qdrant"
    fi
    
    # Wait for Qdrant to be ready
    health_check "Qdrant" 6333
}

# MCP server setup
setup_mcp_servers() {
    log "Setting up MCP servers..."
    
    # Create MCP configuration directory
    mkdir -p ~/.config/mcp
    
    # Generate MCP configuration
    cat > ~/.config/mcp/config.json << EOF
{
    "servers": {
        "sophia-ai": {
            "command": "python",
            "args": ["backend/services/estuary_cdc_pool.py"],
            "env": {
                "REDIS_URL": "${REDIS_URL}",
                "DATABASE_URL": "${DATABASE_URL}",
                "LAMBDA_API_KEY": "${LAMBDA_API_KEY}"
            }
        }
    }
}
EOF
    
    log "✅ MCP configuration created"
}

# Lambda Labs API validation
validate_lambda_labs() {
    log "Validating Lambda Labs API connection..."
    
    local api_response
    api_response=$(curl -s -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
        "https://cloud.lambdalabs.com/api/v1/instance-types" || echo "")
    
    if [[ -z "$api_response" ]]; then
        error_exit "Failed to connect to Lambda Labs API"
    fi
    
    if echo "$api_response" | jq -e '.error' > /dev/null 2>&1; then
        error_exit "Lambda Labs API error: $(echo "$api_response" | jq -r '.error.message')"
    fi
    
    log "✅ Lambda Labs API connection successful"
    
    # Check GPU availability
    local gpu_available
    gpu_available=$(echo "$api_response" | jq -r '.data[] | select(.name | contains("gpu_1x_a100")) | .regions_with_capacity_available | length')
    
    if [[ "$gpu_available" -gt 0 ]]; then
        log "✅ GPU instances available in $gpu_available regions"
    else
        log "⚠️  No GPU instances currently available"
    fi
}

# Service startup
start_services() {
    log "Starting Sophia AI services..."
    
    # Start backend API
    if [[ -f "backend/main.py" ]]; then
        log "Starting backend API..."
        cd backend
        nohup uvicorn main:app --host ${BIND_IP} --port 8000 > /tmp/backend.log 2>&1 &
        cd ..
        
        # Health check backend
        health_check "Backend API" 8000
    fi
    
    # Start MCP server
    if [[ -f "backend/services/estuary_cdc_pool.py" ]]; then
        log "Starting MCP server..."
        nohup python backend/services/estuary_cdc_pool.py > /tmp/mcp.log 2>&1 &
        
        # Health check MCP server
        health_check "MCP Server" 8001
    fi
    
    # Start Lambda Labs manager
    if [[ -f "backend/services/lambda_labs_manager.py" ]]; then
        log "Starting Lambda Labs manager..."
        nohup python backend/services/lambda_labs_manager.py > /tmp/lambda-manager.log 2>&1 &
        
        # Health check Lambda Labs manager
        health_check "Lambda Labs Manager" 8002
    fi
}

# Cost safety checks
setup_cost_controls() {
    log "Setting up cost safety controls..."
    
    # Create cost monitoring script
    cat > /tmp/cost-monitor.sh << 'EOF'
#!/bin/bash
# Cost monitoring script
MAX_COST_PER_HOUR=${LAMBDA_MAX_COST_PER_HOUR:-15.00}
CURRENT_COST=$(curl -s http://localhost:8002/cost-analysis | jq -r '.current_cost_per_hour // 0')

if (( $(echo "$CURRENT_COST > $MAX_COST_PER_HOUR" | bc -l) )); then
    echo "ALERT: Cost limit exceeded: $CURRENT_COST > $MAX_COST_PER_HOUR"
    curl -X POST http://localhost:8002/emergency-shutdown
fi
EOF
    
    chmod +x /tmp/cost-monitor.sh
    
    # Setup cron job for cost monitoring (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * /tmp/cost-monitor.sh") | crontab -
    
    log "✅ Cost monitoring enabled (max: \$${LAMBDA_MAX_COST_PER_HOUR:-15.00}/hour)"
}

# Main execution
main() {
    log "🚀 Starting Sophia AI Lambda Labs initialization..."
    
    # Validation phase
    validate_environment
    
    # Setup phase
    install_dependencies
    setup_python_environment
    initialize_databases
    setup_mcp_servers
    
    # Validation phase
    validate_lambda_labs
    
    # Service startup phase
    start_services
    
    # Safety phase
    setup_cost_controls
    
    log "✅ Sophia AI Lambda Labs initialization complete!"
    log "📊 Services running:"
    log "   - Backend API: http://localhost:${AGENT_API_PORT:-8003}"
    log "   - MCP Server: http://localhost:8001"
    log "   - Lambda Manager: http://localhost:8002"
    log "   - Qdrant Vector DB: http://localhost:6333"
    log "📋 Logs available in /tmp/*.log"
    log "💰 Cost monitoring active (check every 5 minutes)"
}

# Execute main function
main "$@"
