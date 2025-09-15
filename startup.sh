#!/bin/bash

# Sophia Intel AI - Enhanced Smart Startup Script
# Production-ready with persistence, deduplication, health checks, and rollback

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"
BACKUP_DIR="$SCRIPT_DIR/backups"
REDIS_DATA_DIR="$SCRIPT_DIR/redis-data"
STARTUP_LOG="$LOG_DIR/startup-$(date +%Y%m%d-%H%M%S).log"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR" "$BACKUP_DIR" "$REDIS_DATA_DIR" "$LOG_DIR/pm2"

# Logging function
log() {
    echo -e "$1" | tee -a "$STARTUP_LOG"
}

# Rollback state file
ROLLBACK_STATE="$BACKUP_DIR/rollback-state-$(date +%Y%m%d-%H%M%S).json"

# Save current state for rollback
save_rollback_state() {
    cat > "$ROLLBACK_STATE" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "pids": {
        "redis": $(pgrep redis-server 2>/dev/null || echo "null"),
        "mcp_memory": $(cat $PID_DIR/mcp-memory.pid 2>/dev/null || echo "null"),
        "mcp_filesystem": $(cat $PID_DIR/mcp-filesystem.pid 2>/dev/null || echo "null"),
        "mcp_git": $(cat $PID_DIR/mcp-git.pid 2>/dev/null || echo "null")
    },
    "services_running": {
        "redis": $(redis-cli ping >/dev/null 2>&1 && echo "true" || echo "false"),
        "mcp_memory": $(curl -s http://localhost:8081/health >/dev/null 2>&1 && echo "true" || echo "false"),
        "mcp_filesystem": $(curl -s http://localhost:8082/health >/dev/null 2>&1 && echo "true" || echo "false"),
        "mcp_git": $(curl -s http://localhost:8084/health >/dev/null 2>&1 && echo "true" || echo "false")
    }
}
EOF
    log "${CYAN}Saved rollback state to: $ROLLBACK_STATE${NC}"
}

# Rollback function
rollback() {
    log "${RED}ROLLBACK: Startup failed, reverting to previous state...${NC}"
    
    # Kill any processes we started
    for pid_file in $PID_DIR/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                log "  Stopping process $pid from $(basename $pid_file)"
                kill "$pid" 2>/dev/null || true
            fi
            rm "$pid_file"
        fi
    done
    
    # Stop any Redis we might have started
    if [ -f "$PID_DIR/redis.pid" ]; then
        redis-cli shutdown 2>/dev/null || true
        rm "$PID_DIR/redis.pid"
    fi
    
    log "${YELLOW}Rollback complete. Please check logs for issues.${NC}"
    exit 1
}

# Trap errors for rollback
trap 'rollback' ERR

log "${BLUE}================================${NC}"
log "${BLUE}Sophia Intel AI - Enhanced Startup${NC}"
log "${BLUE}================================${NC}\n"

# Save current state
save_rollback_state

# 1. NPM Process Deduplication
log "${YELLOW}1. Deduplicating NPM processes...${NC}"

# Kill duplicate NPM MCP servers
for pkg in "@modelcontextprotocol/server-memory" \
           "@modelcontextprotocol/server-sequential-thinking" \
           "@apify/actors-mcp-server" \
           "@modelcontextprotocol/server-brave-search" \
           "exa-mcp-server"; do
    pids=$(pgrep -f "$pkg" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        count=$(echo "$pids" | wc -w)
        if [ "$count" -gt 1 ]; then
            log "   Found $count instances of $pkg, keeping newest..."
            echo "$pids" | head -n -1 | xargs -r kill 2>/dev/null || true
        fi
    fi
done

# Kill zombie MCP processes
log "   Cleaning up zombie processes..."
pkill -f "mcp.*server" 2>/dev/null || true
sleep 2

log "   ${GREEN}✅ Process deduplication complete${NC}"

# 2. Environment Setup
log "\n${YELLOW}2. Setting up environment...${NC}"

# Check environment
if [ ! -f .env.master ]; then
    log "${RED}   ERROR: .env.master not found${NC}"
    log "   Creating from environment..."
    cat > .env.master << 'EOF'
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}"
OPENAI_API_KEY="${OPENAI_API_KEY}"
XAI_API_KEY="${XAI_API_KEY}"
GROQ_API_KEY="${GROQ_API_KEY}"
DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY}"
MISTRAL_API_KEY="${MISTRAL_API_KEY}"
PERPLEXITY_API_KEY="${PERPLEXITY_API_KEY}"
OPENROUTER_API_KEY="${OPENROUTER_API_KEY}"
TOGETHER_API_KEY="${TOGETHER_API_KEY}"
APIFY_API_TOKEN="${APIFY_API_TOKEN}"
BRAVE_SEARCH_API_KEY="${BRAVE_SEARCH_API_KEY}"
EXA_API_KEY="${EXA_API_KEY}"
GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_PERSONAL_ACCESS_TOKEN}"
EOF
    # Expand variables
    envsubst < .env.master > .env.master.tmp
    mv .env.master.tmp .env.master
    chmod 600 .env.master
fi

# Source environment
source .env.master
log "   ${GREEN}✅ Environment configured${NC}"

# 3. Start Redis with Persistence
log "\n${YELLOW}3. Starting Redis with persistence...${NC}"

if ! redis-cli ping >/dev/null 2>&1; then
    log "   Starting Redis with production config..."
    
    # Check if custom config exists
    if [ -f "$SCRIPT_DIR/config/redis.conf" ]; then
        redis-server "$SCRIPT_DIR/config/redis.conf" \
            --daemonize yes \
            --dir "$REDIS_DATA_DIR" \
            --logfile "$LOG_DIR/redis.log" \
            --pidfile "$PID_DIR/redis.pid"
        log "   Using production Redis configuration"
    else
        # Fallback to basic config
        redis-server \
            --daemonize yes \
            --dir "$REDIS_DATA_DIR" \
            --logfile "$LOG_DIR/redis.log" \
            --pidfile "$PID_DIR/redis.pid" \
            --save 900 1 \
            --save 300 10 \
            --save 60 10000 \
            --appendonly yes
        log "   Using default Redis configuration"
    fi
    
    # Wait for Redis to start
    for i in {1..10}; do
        if redis-cli ping >/dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    
    # Verify Redis is running
    if ! redis-cli ping >/dev/null 2>&1; then
        log "${RED}   ❌ Failed to start Redis${NC}"
        exit 1
    fi
fi

# Check Redis persistence status
REDIS_INFO=$(redis-cli INFO persistence)
if echo "$REDIS_INFO" | grep -q "aof_enabled:1"; then
    log "   ${GREEN}✅ Redis running with AOF persistence${NC}"
else
    log "   ${YELLOW}⚠️  Redis running without AOF persistence${NC}"
fi

# 4. Start MCP Servers with Health Checks
log "\n${YELLOW}4. Starting MCP Servers with health validation...${NC}"

# Function to start and validate a server
start_mcp_server() {
    local name=$1
    local port=$2
    local module=$3
    local pid_file=$4
    local log_file=$5
    
    if ! curl -s "http://localhost:$port/health" >/dev/null 2>&1; then
        log "   Starting $name..."
        
        # Start the server
        nohup python3 -m uvicorn "$module" \
            --host 0.0.0.0 --port "$port" \
            > "$log_file" 2>&1 &
        local pid=$!
        echo $pid > "$pid_file"
        
        # Wait for server to be healthy
        local retries=0
        local max_retries=30
        while [ $retries -lt $max_retries ]; do
            if curl -s "http://localhost:$port/health" 2>/dev/null | grep -q "healthy"; then
                log "   ${GREEN}✅ $name started and healthy on port $port${NC}"
                return 0
            fi
            sleep 1
            retries=$((retries + 1))
        done
        
        # Server didn't become healthy
        log "   ${RED}❌ $name failed health check after $max_retries seconds${NC}"
        kill $pid 2>/dev/null || true
        rm "$pid_file"
        return 1
    else
        log "   ${GREEN}✅ $name already running on port $port${NC}"
        return 0
    fi
}

# Start each MCP server with validation
start_mcp_server "Memory Server" 8081 "mcp.memory_server:app" \
    "$PID_DIR/mcp-memory.pid" "$LOG_DIR/mcp-memory.log" || \
    log "   ${YELLOW}⚠️  Continuing without Memory Server${NC}"

start_mcp_server "Filesystem Server" 8082 "mcp.filesystem.server:app" \
    "$PID_DIR/mcp-filesystem.pid" "$LOG_DIR/mcp-filesystem.log" || \
    log "   ${YELLOW}⚠️  Continuing without Filesystem Server${NC}"

start_mcp_server "Git Server" 8084 "mcp.git.server:app" \
    "$PID_DIR/mcp-git.pid" "$LOG_DIR/mcp-git.log" || \
    log "   ${YELLOW}⚠️  Continuing without Git Server${NC}"

# 5. Comprehensive Validation
log "\n${YELLOW}5. Running comprehensive validation...${NC}"

VALIDATION_PASSED=true

# Check Redis
if redis-cli ping | grep -q PONG 2>/dev/null; then
    REDIS_KEYS=$(redis-cli DBSIZE | awk '{print $2}')
    log "   ${GREEN}✅ Redis: Running with $REDIS_KEYS keys${NC}"
else
    log "   ${RED}❌ Redis: Not responding${NC}"
    VALIDATION_PASSED=false
fi

# Test MCP servers with actual health endpoints
for server in "Memory:8081" "Filesystem:8082" "Git:8084"; do
    IFS=':' read -r name port <<< "$server"
    if response=$(curl -s "http://localhost:$port/health" 2>/dev/null); then
        if echo "$response" | grep -q "healthy"; then
            log "   ${GREEN}✅ $name Server: Healthy${NC}"
        else
            log "   ${YELLOW}⚠️  $name Server: Responding but not healthy${NC}"
        fi
    else
        log "   ${RED}❌ $name Server: Not responding${NC}"
        VALIDATION_PASSED=false
    fi
done

# Check for PM2
if command -v pm2 >/dev/null 2>&1; then
    log "   ${GREEN}✅ PM2: Available for process management${NC}"
else
    log "   ${YELLOW}⚠️  PM2: Not installed (npm install -g pm2)${NC}"
fi

# 6. Optional: Start Health Monitor
log "\n${YELLOW}6. Health Monitoring Setup...${NC}"

if [ -f "$SCRIPT_DIR/scripts/mcp_health_monitor.py" ]; then
    log "   ${CYAN}Health monitor available: python3 scripts/mcp_health_monitor.py${NC}"
    
    # Check if we should auto-start monitor
    if [ "${AUTO_START_MONITOR:-false}" = "true" ]; then
        nohup python3 "$SCRIPT_DIR/scripts/mcp_health_monitor.py" \
            --interval 30 > "$LOG_DIR/health-monitor.log" 2>&1 &
        echo $! > "$PID_DIR/health-monitor.pid"
        log "   ${GREEN}✅ Health monitor started in background${NC}"
    fi
else
    log "   ${YELLOW}⚠️  Health monitor script not found${NC}"
fi

# 7. Final Status
if [ "$VALIDATION_PASSED" = true ]; then
    log "\n${BLUE}================================${NC}"
    log "${GREEN}STARTUP SUCCESSFUL${NC}"
    log "${BLUE}================================${NC}\n"
else
    log "\n${BLUE}================================${NC}"
    log "${YELLOW}STARTUP COMPLETED WITH WARNINGS${NC}"
    log "${BLUE}================================${NC}\n"
fi

# Remove rollback trap since we succeeded
trap - ERR

log "Quick commands:"
log "  ./dev check              - Run health check"
log "  ./dev status             - Detailed status"
log "  python3 scripts/mcp_health_monitor.py --once   - Single health check"
log "  python3 scripts/mcp_health_monitor.py          - Continuous monitoring"
log "  pm2 start config/pm2.ecosystem.config.js       - PM2 process management"
log ""
log "API Endpoints:"
log "  Memory:      http://localhost:8081"
log "  Filesystem:  http://localhost:8082"
log "  Git:         http://localhost:8084"
log ""
log "Logs:"
log "  Startup:     $STARTUP_LOG"
log "  Redis:       $LOG_DIR/redis.log"
log "  MCP Memory:  $LOG_DIR/mcp-memory.log"
log "  MCP FS:      $LOG_DIR/mcp-filesystem.log"
log "  MCP Git:     $LOG_DIR/mcp-git.log"
log ""

# Exit with appropriate code
if [ "$VALIDATION_PASSED" = true ]; then
    exit 0
else
    exit 2  # Exit 2 for partial success
fi
