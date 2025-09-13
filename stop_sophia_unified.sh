#!/bin/bash

# Sophia Intel AI - Unified Stop Script
# This script stops all Sophia services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SOPHIA_HOME="$(cd "$(dirname "$0")" && pwd)"
PID_DIR="$SOPHIA_HOME/pids"

echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      SOPHIA INTEL AI - SHUTDOWN              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

stop_service() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"
    
    echo -n -e "${YELLOW}Stopping ${name}...${NC}"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            kill $pid
            sleep 1
            if kill -0 $pid 2>/dev/null; then
                kill -9 $pid 2>/dev/null
            fi
            rm -f "$pid_file"
            echo -e " ${GREEN}[STOPPED]${NC}"
        else
            rm -f "$pid_file"
            echo -e " ${YELLOW}[NOT RUNNING]${NC}"
        fi
    else
        echo -e " ${YELLOW}[NO PID FILE]${NC}"
    fi
}

# Stop all services
stop_service "sophia-server"
stop_service "mcp-memory"
stop_service "mcp-filesystem"
stop_service "mcp-git"
stop_service "sophia-intel-app"

# Clean up state file
rm -f "$SOPHIA_HOME/.sophia-state.json"

echo ""
echo -e "${GREEN}All services stopped.${NC}"