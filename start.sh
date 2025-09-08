#!/bin/bash
# Sophia Intel AI - Master Startup Script
# Single entry point for complete system startup with zero technical debt

set -euo pipefail

# Source shared environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
. scripts/env.sh

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}    🚀 SOPHIA INTEL AI - UNIFIED STARTUP SYSTEM${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
  --help, -h          Show this help message
  --dry-run          Test startup without actually starting services
  --skip-deps        Skip dependency check
  --skip-health      Skip health checks
  --services LIST    Start only specific services (comma-separated)
  --env ENV          Set environment (development/production)
  --verbose          Enable verbose output

Services:
  redis            Redis cache and pub/sub
  postgres         PostgreSQL database (optional)
  mcp-memory       MCP memory server
  mcp-bridge       MCP bridge server
  sophia-backend   Sophia backend API
  monitoring       Prometheus/Grafana (optional)

Examples:
  $0                                    # Start all services
  $0 --services redis,mcp-memory       # Start only Redis and MCP
  $0 --dry-run                         # Test startup process
  $0 --env production                  # Start in production mode

EOF
}

# Parse arguments
DRY_RUN=false
SKIP_DEPS=false
SKIP_HEALTH=false
SERVICES="all"
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_usage
            exit 0
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --skip-health)
            SKIP_HEALTH=true
            shift
            ;;
        --services)
            SERVICES="$2"
            shift 2
            ;;
        --env)
            export ENVIRONMENT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            set -x
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check for virtual environments (should be NONE)
log_info "Checking for virtual environments..."
if ! check_no_venv; then
    log_warning "Virtual environments detected - these should be removed"
    if [ "$DRY_RUN" = false ]; then
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Check dependencies
if [ "$SKIP_DEPS" = false ]; then
    log_info "Checking Python dependencies..."
    
    missing_deps=()
    
    # Core dependencies
    for module in fastapi uvicorn redis psycopg2; do
        if ! python3 -c "import $module" 2>/dev/null; then
            missing_deps+=("$module")
        fi
    done
    
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_warning "Missing Python dependencies: ${missing_deps[*]}"
        log_info "Install with: pip3 install --user -r requirements.txt"
        
        if [ "$DRY_RUN" = false ]; then
            read -p "Try to install now? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                pip3 install --user -r requirements.txt
            else
                exit 1
            fi
        fi
    else
        log_success "All Python dependencies satisfied"
    fi
fi

# Service management functions
start_service() {
    local name="$1"
    local command="$2"
    local port="${3:-}"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY RUN] Would start $name: $command"
        return 0
    fi
    
    log_info "Starting $name..."
    
    # Check port if specified
    if [ -n "$port" ]; then
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "Port $port already in use (possibly $name already running)"
            return 0
        fi
    fi
    
    # Start the service
    eval "$command" > "logs/${name}.log" 2>&1 &
    local pid=$!
    echo $pid > "logs/${name}.pid"
    
    # Wait for service to start
    sleep 2
    
    if ps -p $pid > /dev/null; then
        log_success "$name started (PID: $pid)"
        [ -n "$port" ] && echo "   Available at: http://localhost:$port"
        return 0
    else
        log_error "$name failed to start - check logs/${name}.log"
        return 1
    fi
}

wait_for_service() {
    local name="$1"
    local port="$2"
    local max_attempts=30
    local attempt=1
    
    if [ "$SKIP_HEALTH" = true ] || [ "$DRY_RUN" = true ]; then
        return 0
    fi
    
    log_info "Waiting for $name to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
            log_success "$name is healthy"
            return 0
        fi
        
        [ "$VERBOSE" = true ] && echo "   Attempt $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_error "$name health check failed after $max_attempts attempts"
    return 1
}

# Create necessary directories
mkdir -p logs

# Start services based on selection
should_start() {
    local service="$1"
    
    if [ "$SERVICES" = "all" ]; then
        return 0
    fi
    
    if echo "$SERVICES" | grep -q "$service"; then
        return 0
    fi
    
    return 1
}

# Infrastructure services
if should_start "redis"; then
    if ! pgrep -x "redis-server" > /dev/null; then
        start_service "redis" "redis-server --daemonize no" "6379"
    else
        log_info "Redis already running"
    fi
fi

if should_start "postgres"; then
    # PostgreSQL is optional and may be managed externally
    if command -v pg_isready &> /dev/null; then
        if pg_isready -q; then
            log_info "PostgreSQL already running"
        else
            log_warning "PostgreSQL not running (manage externally if needed)"
        fi
    fi
fi

# MCP services
if should_start "mcp-memory"; then
    start_service "mcp-memory" "python3 mcp_memory_server/main.py --port ${MCP_MEMORY_PORT}" "$MCP_MEMORY_PORT"
    wait_for_service "mcp-memory" "$MCP_MEMORY_PORT"
fi

if should_start "mcp-bridge"; then
    if [ -f "mcp-bridge/server.py" ]; then
        start_service "mcp-bridge" "python3 mcp-bridge/server.py --port ${MCP_BRIDGE_PORT}" "$MCP_BRIDGE_PORT"
        wait_for_service "mcp-bridge" "$MCP_BRIDGE_PORT"
    fi
fi

# Sophia backend
if should_start "sophia-backend"; then
    if [ -f "backend/main.py" ]; then
        start_service "sophia-backend" "uvicorn backend.main:app --host 0.0.0.0 --port 8000" "8000"
        wait_for_service "sophia-backend" "8000"
    fi
fi

# Optional monitoring
if should_start "monitoring"; then
    if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
        log_info "Starting monitoring services..."
        docker-compose up -d prometheus grafana 2>/dev/null && \
            log_success "Monitoring started" || \
            log_warning "Monitoring not available"
    fi
fi

# Final status
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}    ✅ SOPHIA INTEL AI - STARTUP COMPLETE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "📊 Services Status:"

# Check running services
for service in redis mcp-memory mcp-bridge sophia-backend; do
    if [ -f "logs/${service}.pid" ]; then
        pid=$(cat "logs/${service}.pid")
        if ps -p $pid > /dev/null 2>&1; then
            echo "  ✅ $service: Running (PID: $pid)"
        else
            echo "  ❌ $service: Not running"
        fi
    fi
done

echo ""
echo "🔗 Available Endpoints:"
echo "  • Sophia Backend: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • MCP Memory: http://localhost:${MCP_MEMORY_PORT}"
echo "  • MCP Bridge: http://localhost:${MCP_BRIDGE_PORT}"

if should_start "monitoring"; then
    echo "  • Prometheus: http://localhost:9090"
    echo "  • Grafana: http://localhost:3000"
fi

echo ""
echo "🤖 AI Agent CLI:"
echo "  • Unified CLI: python3 scripts/unified_ai_agents.py --help"
echo "  • Grok: python3 scripts/grok_agent.py --task 'your task'"
echo "  • Claude: python3 scripts/claude_coder_agent.py --task 'your task'"
echo "  • Codex: python3 scripts/codex_agent.py --task 'your task'"

echo ""
echo "📝 Logs: tail -f logs/*.log"
echo "🛑 Stop: pkill -f 'python3.*main.py|redis-server'"
echo ""

# Trap for cleanup
trap 'echo "Shutting down..."; pkill -f "python3.*main.py|redis-server" 2>/dev/null; exit' INT TERM

if [ "$DRY_RUN" = false ]; then
    echo "Press Ctrl+C to stop all services..."
    
    # Keep script running
    while true; do
        sleep 60
        
        # Optional: periodic health check
        if [ "$SKIP_HEALTH" = false ]; then
            for service in mcp-memory sophia-backend; do
                if [ -f "logs/${service}.pid" ]; then
                    pid=$(cat "logs/${service}.pid")
                    if ! ps -p $pid > /dev/null 2>&1; then
                        log_warning "$service stopped unexpectedly"
                    fi
                fi
            done
        fi
    done
fi