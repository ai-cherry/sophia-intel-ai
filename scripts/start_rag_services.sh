#!/bin/bash

# RAG Memory Services Startup Script
# Zero-conflict architecture with existing MCP services
# Ports: Sophia=8767, Artemis=8768

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env.sh"

# Establish repository root and use it for paths
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configurations
SERVICES=(
    "sophia:8767:app.memory.sophia_memory:SophiaMemoryService"
    "artemis:8768:app.memory.artemis_memory:ArtemisMemoryService"
)

# Logging directory
LOG_DIR="$REPO_ROOT/logs/rag"
mkdir -p "$LOG_DIR"

# PID file directory
PID_DIR="$REPO_ROOT/.pids"
mkdir -p "$PID_DIR"

# Function to check if Redis is running
check_redis() {
    echo -e "${BLUE}🔍 Checking Redis availability...${NC}"
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis is running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Redis not available - services will use in-memory cache${NC}"
        return 1
    fi
}

# Function to check if Weaviate is running (optional)
check_weaviate() {
    echo -e "${BLUE}🔍 Checking Weaviate availability...${NC}"
    if curl -s http://localhost:8080/v1/.well-known/ready > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Weaviate is running${NC}"
        return 0
    else
        echo -e "${YELLOW}ℹ️  Weaviate not available - using Redis only${NC}"
        return 1
    fi
}

# Function to start a service
start_service() {
    local service_info="$1"
    IFS=':' read -r name port module class <<< "$service_info"
    
    echo -e "${BLUE}🚀 Starting $name memory service on port $port...${NC}"
    
    # Check if already running
    local pid_file="$PID_DIR/rag_${name}.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  $name already running (PID: $pid)${NC}"
            return 0
        fi
    fi
    
    # Start the service
    cd "$SOPHIA_HOME"
    nohup python3 -m "$module" > "$LOG_DIR/${name}.log" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$pid_file"
    
    # Wait for service to be ready
    sleep 2
    
    # Check if service started successfully
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name started successfully (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to start $name${NC}"
        echo -e "${YELLOW}   Check logs at: $LOG_DIR/${name}.log${NC}"
        return 1
    fi
}

# Function to stop a service
stop_service() {
    local name="$1"
    local pid_file="$PID_DIR/rag_${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${BLUE}🛑 Stopping $name (PID: $pid)...${NC}"
            kill "$pid"
            rm -f "$pid_file"
            echo -e "${GREEN}✅ $name stopped${NC}"
        else
            echo -e "${YELLOW}⚠️  $name not running${NC}"
            rm -f "$pid_file"
        fi
    else
        echo -e "${YELLOW}ℹ️  $name not running${NC}"
    fi
}

# Function to check service status
check_status() {
    local name="$1"
    local port="$2"
    local pid_file="$PID_DIR/rag_${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            # Try health check
            if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name: Running (PID: $pid, Port: $port)${NC}"
            else
                echo -e "${YELLOW}⚠️  $name: Process running but not responding (PID: $pid)${NC}"
            fi
        else
            echo -e "${RED}❌ $name: Not running (stale PID file)${NC}"
        fi
    else
        echo -e "${RED}❌ $name: Not running${NC}"
    fi
}

# Main execution
case "${1:-start}" in
    start)
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${BLUE}    RAG Memory Services Startup${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        
        # Check dependencies
        check_redis
        check_weaviate
        
        echo -e "\n${BLUE}Starting services...${NC}"
        
        # Start all services
        for service in "${SERVICES[@]}"; do
            start_service "$service"
        done
        
        echo -e "\n${GREEN}✅ RAG services startup complete${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        ;;
        
    stop)
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${BLUE}    Stopping RAG Memory Services${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        
        for service in "${SERVICES[@]}"; do
            IFS=':' read -r name _ _ _ <<< "$service"
            stop_service "$name"
        done
        
        echo -e "\n${GREEN}✅ All services stopped${NC}"
        ;;
        
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${BLUE}    RAG Memory Services Status${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        
        for service in "${SERVICES[@]}"; do
            IFS=':' read -r name port _ _ <<< "$service"
            check_status "$name" "$port"
        done
        
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        ;;
        
    logs)
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        echo -e "${BLUE}    RAG Service Logs${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════${NC}"
        
        for service in "${SERVICES[@]}"; do
            IFS=':' read -r name _ _ _ <<< "$service"
            log_file="$LOG_DIR/${name}.log"
            if [ -f "$log_file" ]; then
                echo -e "\n${BLUE}--- $name logs (last 20 lines) ---${NC}"
                tail -20 "$log_file"
            else
                echo -e "${YELLOW}No logs found for $name${NC}"
            fi
        done
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
