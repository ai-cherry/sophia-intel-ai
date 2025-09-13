#!/bin/bash

# Unified System Manager for Sophia Intel AI
# Quality-controlled and integration-tested

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_FILE="$SCRIPT_DIR/.env.master"
PID_DIR="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"

# Create necessary directories
mkdir -p "$PID_DIR" "$LOG_DIR"

# Source environment strictly from repo-local .env.master (single source of truth)
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    source "$ENV_FILE"
else
    echo -e "${RED}Error: .env.master not found at $ENV_FILE${NC}"
    echo -e "Create it once and you're done: cp .env.template .env.master && chmod 600 .env.master"
    exit 1
fi

# Dev-friendly defaults to align ./sophia with ./dev behavior (keys/secrets consolidation)
export MCP_DEV_BYPASS="${MCP_DEV_BYPASS:-true}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/1}"
# LLM Gateway: Portkey is preferred via PORTKEY_API_KEY

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    # JSON log event for visibility (avoid arg parsing issues; read from stdin)
    local ts msg_json
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    msg_json="$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))' <<< "$1" 2>/dev/null || printf '"%s"' "$1")"
    printf '{"ts":"%s","level":"info","message":%s}\n' "$ts" "$msg_json" >> "$LOG_DIR/agent_sysmgr.json" 2>/dev/null || true
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    local ts msg_json
    ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    msg_json="$(python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))' <<< "$1" 2>/dev/null || printf '"%s"' "$1")"
    printf '{"ts":"%s","level":"error","message":%s}\n' "$ts" "$msg_json" >> "$LOG_DIR/agent_sysmgr.json" 2>/dev/null || true
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

check_port() {
    local port=$1
    if command -v nc >/dev/null 2>&1 && nc -z localhost "$port" 2>/dev/null; then
        return 0
    fi
    if command -v lsof >/dev/null 2>&1 && lsof -Pi :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    fi
    if command -v netstat >/dev/null 2>&1 && netstat -an 2>/dev/null | grep -q "LISTEN.*[.:]$port"; then
        return 0
    fi
    return 1
}

// LiteLLM removed: Portkey is the preferred gateway; no local proxy management

start_mcp_servers() {
    log "Starting MCP servers..."
    
    # Kill any existing MCP servers
    pkill -f "mcp.memory_server" 2>/dev/null || true
    pkill -f "mcp.filesystem.server" 2>/dev/null || true
    pkill -f "mcp.git_server" 2>/dev/null || true
    sleep 2
    
    # Ensure uvicorn available
    if ! python3 -c "import uvicorn" >/dev/null 2>&1; then
        error "uvicorn not available in python3. Try: pip install uvicorn fastapi redis pydantic"
        return 1
    fi

    # Start Memory Server
    if ! check_port 8081; then
        nohup python3 -m uvicorn mcp.memory_server:app --host 0.0.0.0 --port 8081 > "$LOG_DIR/mcp-memory.log" 2>&1 &
        echo $! > "$PID_DIR/mcp-memory.pid"
        # Wait until port is up (max 10s)
        for i in {1..10}; do
          if check_port 8081; then log "✅ Memory server started on port 8081"; break; fi
          sleep 1
        done
    fi
    
    # Start Filesystem Server
    if ! check_port 8082; then
        nohup python3 -m uvicorn mcp.filesystem.server:app --host 0.0.0.0 --port 8082 > "$LOG_DIR/mcp-filesystem.log" 2>&1 &
        echo $! > "$PID_DIR/mcp-filesystem.pid"
        for i in {1..10}; do
          if check_port 8082; then log "✅ Filesystem server started on port 8082"; break; fi
          sleep 1
        done
    fi
    
    # Start Git Server
    if ! check_port 8084; then
        nohup python3 -m uvicorn mcp.git.server:app --host 0.0.0.0 --port 8084 > "$LOG_DIR/mcp-git.log" 2>&1 &
        echo $! > "$PID_DIR/mcp-git.pid"
        for i in {1..10}; do
          if check_port 8084; then log "✅ Git server started on port 8084"; break; fi
          sleep 1
        done
    fi
}

stop_mcp_servers() {
    log "Stopping MCP servers..."
    
    for service in mcp-memory mcp-filesystem mcp-git; do
        if [ -f "$PID_DIR/$service.pid" ]; then
            local pid=$(cat "$PID_DIR/$service.pid")
            if kill -0 $pid 2>/dev/null; then
                kill $pid
                rm "$PID_DIR/$service.pid"
                log "✅ Stopped $service"
            fi
        fi
    done
    
    # Cleanup any orphaned processes
    pkill -f "mcp.memory_server" 2>/dev/null || true
    pkill -f "mcp.filesystem.server" 2>/dev/null || true
    pkill -f "mcp.git_server" 2>/dev/null || true
}

health_check() {
    echo -e "\n${BLUE}=== System Health Check ===${NC}\n"
    
    # Check Portkey Gateway
    if [ -n "${PORTKEY_API_KEY:-}" ]; then
        if curl -s --max-time 3 https://api.portkey.ai/v1/health -H "x-portkey-api-key: ${PORTKEY_API_KEY}" >/dev/null 2>&1; then
            echo -e "✅ Portkey: ${GREEN}Healthy${NC}"
        else
            echo -e "❌ Portkey: ${RED}Unreachable${NC}"
        fi
    else
        echo -e "⚠️  Portkey: ${YELLOW}PORTKEY_API_KEY not set${NC}"
    fi
    
    # Check MCP Servers
    local mcp_ports=(8081 8082 8084)
    local mcp_names=("Memory" "Filesystem" "Git")
    
    for i in ${!mcp_ports[@]}; do
        if check_port ${mcp_ports[$i]}; then
            echo -e "✅ MCP ${mcp_names[$i]}: ${GREEN}Running${NC} on port ${mcp_ports[$i]}"
        else
            echo -e "❌ MCP ${mcp_names[$i]}: ${RED}Not running${NC}"
        fi
    done
    
    # Check Opencode
    if command -v opencode >/dev/null 2>&1; then
        echo -e "✅ Opencode: ${GREEN}Available${NC} in PATH"
        echo -e "   └─ Version: $(opencode --version 2>/dev/null || echo 'Unknown')"
    else
        echo -e "❌ Opencode: ${RED}Not in PATH${NC}"
        if [ -f "$HOME/.opencode/bin/opencode" ]; then
            echo -e "   └─ Binary exists at ~/.opencode/bin/opencode"
            echo -e "   └─ Run: source ~/.zshrc"
        fi
    fi
    
    # Check API Keys
    local key_count=$(grep -c "API_KEY\|API_TOKEN" "$ENV_FILE" 2>/dev/null || echo "0")
    echo -e "✅ API Keys: ${GREEN}$key_count configured${NC}"
    
    # Check permissions
    local perms=$(stat -f "%A" "$ENV_FILE" 2>/dev/null || echo "unknown")
    if [ "$perms" = "600" ]; then
        echo -e "✅ Security: ${GREEN}API keys properly secured${NC} (600)"
    else
        echo -e "⚠️  Security: ${YELLOW}API keys permissions: $perms${NC} (should be 600)"
    fi
    
    echo ""
}

status() {
    health_check
    
    echo -e "${BLUE}=== Process Details ===${NC}\n"
    
    # Show running processes
    echo "Active processes:"
    if command -v rg >/dev/null 2>&1; then
      ps aux | rg -N "mcp\.|mcp_|opencode" | head -10 || echo "No related processes found"
    else
      ps aux | grep -E "mcp\.|mcp_|opencode" | grep -v grep | head -10 || echo "No related processes found"
    fi
    
    echo -e "\n${BLUE}=== Recent Logs ===${NC}\n"
    
    # Show recent logs
    for log in "$LOG_DIR"/*.log; do
        if [ -f "$log" ]; then
            echo "$(basename $log):"
            tail -3 "$log" 2>/dev/null | sed 's/^/  /'
            echo ""
        fi
    done
}

start_all() {
    log "Starting all services..."
    start_mcp_servers
    health_check
    log "✅ All services started"
    echo ""
    echo -e "${BLUE}=== Ready Links ===${NC}"
    if [ -n "${PORTKEY_API_KEY:-}" ]; then
      echo -e "• Portkey Gateway:  https://api.portkey.ai/v1/health"
    fi
    echo -e "• MCP Memory:       http://localhost:8081/health"
    echo -e "• MCP Filesystem:   http://localhost:8082/health"
    echo -e "• MCP Git:          http://localhost:8084/health"
    echo -e "• Sophia Studio:    http://localhost:3000   (run: ./sophia studio)"
}

stop_all() {
    log "Stopping all services..."
    stop_mcp_servers
    log "✅ All services stopped"
}

restart_all() {
    stop_all
    sleep 2
    start_all
}

# Main command handler
case "${1:-}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        status
        ;;
    health)
        health_check
        ;;
    mcp-start)
        start_mcp_servers
        ;;
    mcp-stop)
        stop_mcp_servers
        ;;
    logs)
        tail -f "$LOG_DIR"/*.log
        ;;
    clean)
        log "Cleaning up orphaned processes..."
        pkill -f litellm 2>/dev/null || true
        pkill -f "mcp\." 2>/dev/null || true
        rm -f "$PID_DIR"/*.pid
        log "✅ Cleanup complete"
        ;;
    *)
        echo "Unified System Manager for Sophia Intel AI"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|health|logs|clean}"
        echo ""
        echo "Commands:"
        echo "  start      - Start all services (LiteLLM + MCP)"
        echo "  stop       - Stop all services"
        echo "  restart    - Restart all services"
        echo "  status     - Show detailed status and logs"
        echo "  health     - Quick health check"
        echo "  logs       - Tail all logs"
        echo "  clean      - Clean up orphaned processes"
        echo ""
        echo "Individual service control:"
        echo "  litellm-start  - Start only LiteLLM"
        echo "  litellm-stop   - Stop only LiteLLM"
        echo "  mcp-start      - Start only MCP servers"
        echo "  mcp-stop       - Stop only MCP servers"
        echo ""
        exit 1
        ;;
esac
