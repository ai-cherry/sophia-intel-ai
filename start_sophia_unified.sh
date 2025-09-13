#!/bin/bash

# Sophia Intel AI - Unified Start Script
# This script starts all required services using the Service Orchestrator

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SOPHIA_HOME="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$SOPHIA_HOME/logs"
PID_DIR="$SOPHIA_HOME/pids"
CONFIG_DIR="$HOME/.config/sophia"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR" "$CONFIG_DIR"

# Source port management library
if [ -f "$SOPHIA_HOME/scripts/lib/ports.sh" ]; then
    source "$SOPHIA_HOME/scripts/lib/ports.sh"
else
    echo -e "${RED}Error: Port management library not found${NC}"
    exit 1
fi

echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     SOPHIA INTEL AI - UNIFIED LAUNCHER      ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start a service
start_service() {
    local name=$1
    local command=$2
    local port=$3
    local log_file="$LOG_DIR/${name}.log"
    local pid_file="$PID_DIR/${name}.pid"
    
    echo -n -e "${YELLOW}Starting ${name}...${NC}"
    
    # Check if already running
    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo -e " ${GREEN}[ALREADY RUNNING]${NC}"
        return 0
    fi
    
    # Check if port is already in use
    if [ -n "$port" ] && check_port "$port"; then
        echo -e " ${RED}[PORT $port IN USE]${NC}"
        return 1
    fi
    
    # Start the service
    nohup $command > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Wait a moment and check if it started
    sleep 2
    if kill -0 $pid 2>/dev/null; then
        echo -e " ${GREEN}[OK] (PID: $pid)${NC}"
        return 0
    else
        echo -e " ${RED}[FAILED]${NC}"
        rm -f "$pid_file"
        return 1
    fi
}

# Run preflight validation
echo -e "${YELLOW}1. Running Preflight Validation...${NC}"
if [ -f "$SOPHIA_HOME/scripts/startup-validator.py" ]; then
    echo -e "   Running startup validation checks..."
    if python3 "$SOPHIA_HOME/scripts/startup-validator.py" --timeout 120; then
        echo -e "   ${GREEN}✓ Preflight validation passed${NC}"
    else
        validation_status=$?
        if [ $validation_status -eq 2 ]; then
            echo -e "   ${YELLOW}⚠ Validation passed with warnings${NC}"
        else
            echo -e "   ${RED}✗ Preflight validation failed${NC}"
            echo -e "   ${RED}  Check validation report for details${NC}"
            exit 1
        fi
    fi
else
    echo -e "   ${YELLOW}⚠ Startup validator not found, skipping preflight checks${NC}"
fi

# Check for environment configuration
echo ""
echo -e "${YELLOW}2. Loading Configuration...${NC}"
if [ -f "$CONFIG_DIR/env" ]; then
    echo -e "   ${GREEN}✓ Secure environment found${NC}"
    export $(grep -v '^#' "$CONFIG_DIR/env" | xargs)
else
    echo -e "   ${YELLOW}⚠ No secure environment found at $CONFIG_DIR/env${NC}"
    echo -e "   ${YELLOW}  Copy .env.example to $CONFIG_DIR/env and configure${NC}"
    
    # Check if we have minimal config in regular .env
    if [ -f "$SOPHIA_HOME/.env" ]; then
        echo -e "   ${YELLOW}  Using .env file (not recommended for production)${NC}"
        export $(grep -v '^#' "$SOPHIA_HOME/.env" | xargs)
    fi
fi

# Check External Services First
echo ""
echo -e "${YELLOW}3. Checking External Services...${NC}"
echo -e "   Checking for required external services..."

# Use orchestrator to check external services
if python3 "$SOPHIA_HOME/scripts/orchestrate.py" check postgres; then
    echo -e "   ${GREEN}✓ PostgreSQL is available${NC}"
else
    echo -e "   ${RED}✗ PostgreSQL is not available${NC}"
    echo -e "   ${RED}  Please start PostgreSQL before continuing${NC}"
fi

if python3 "$SOPHIA_HOME/scripts/orchestrate.py" check redis; then
    echo -e "   ${GREEN}✓ Redis is available${NC}"
else
    echo -e "   ${RED}✗ Redis is not available${NC}"
    echo -e "   ${RED}  Please start Redis before continuing${NC}"
fi

# Start Core Services
echo ""
echo -e "${YELLOW}4. Starting Core Services...${NC}"
echo -e "   Using Service Orchestrator for coordinated startup..."

# Determine service types to start
SERVICE_TYPES="core"
if [ "$1" == "--with-dev" ]; then
    SERVICE_TYPES="core dev"
    echo -e "   ${BLUE}Including development services${NC}"
elif [ "$1" == "--with-optional" ]; then
    SERVICE_TYPES="core optional"
    echo -e "   ${BLUE}Including optional services${NC}"
elif [ "$1" == "--all" ]; then
    SERVICE_TYPES="core optional dev"
    echo -e "   ${BLUE}Including all service types${NC}"
fi

# Start services using orchestrator
cd "$SOPHIA_HOME"
echo -e "   Starting services of types: $SERVICE_TYPES"

if python3 "$SOPHIA_HOME/scripts/orchestrate.py" start --type $SERVICE_TYPES; then
    echo -e "   ${GREEN}✓ Core services started successfully${NC}"
else
    echo -e "   ${RED}✗ Failed to start some services${NC}"
    echo -e "   ${YELLOW}  Run 'python3 scripts/orchestrate.py status' for details${NC}"
fi

# Start Agent UI separately if requested
if [ "$1" == "--with-ui" ]; then
    echo ""
    echo -e "${YELLOW}5. Starting Agent UI (Development)...${NC}"
    
    if python3 "$SOPHIA_HOME/scripts/orchestrate.py" start agent_ui; then
        echo -e "   ${GREEN}✓ Agent UI started successfully${NC}"
    else
        echo -e "   ${YELLOW}⚠ Failed to start Agent UI${NC}"
        echo -e "   ${YELLOW}  You may need to install dependencies first${NC}"
        echo -e "   ${YELLOW}  Run: cd sophia-intel-app && npm install${NC}"
    fi
fi

# Wait for services to be ready
echo ""
echo -e "${YELLOW}5. Waiting for Services...${NC}"
echo -e "   Waiting for core services to become healthy..."

# Wait for unified API
if wait_for_service unified_api 60; then
    echo -e "   ${GREEN}✓ Unified API is ready${NC}"
else
    echo -e "   ${RED}✗ Unified API failed to start${NC}"
fi

# Health Check
echo ""
echo -e "${YELLOW}6. Running Health Checks...${NC}"
echo -e "   Performing comprehensive health checks..."

if python3 "$SOPHIA_HOME/scripts/orchestrate.py" check; then
    echo -e "   ${GREEN}✓ All services are healthy${NC}"
else
    echo -e "   ${YELLOW}⚠ Some services may have health issues${NC}"
    echo -e "   ${YELLOW}  Run 'python3 scripts/orchestrate.py status' for details${NC}"
fi

# Integration Status Check
if [ -n "$SOPHIA_API_PORT" ]; then
    api_port=$SOPHIA_API_PORT
else
    api_port=8000  # Default unified API port
fi

echo ""
echo -e "${YELLOW}7. Integration Status:${NC}"

# Try to get integration status from API
if curl -s -f "http://localhost:$api_port/api/integrations/status" > /dev/null 2>&1; then
    integrations=$(curl -s "http://localhost:$api_port/api/integrations/status" 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "{}")
    
    if echo "$integrations" | grep -q '"slack".*"enabled": true'; then
        echo -e "   ${GREEN}✓ Slack integration enabled${NC}"
    else
        echo -e "   ${YELLOW}○ Slack integration disabled${NC}"
    fi
    
    if echo "$integrations" | grep -q '"asana".*"enabled": true'; then
        echo -e "   ${GREEN}✓ Asana integration enabled${NC}"
    else
        echo -e "   ${YELLOW}○ Asana integration disabled${NC}"
    fi
    
    if echo "$integrations" | grep -q '"linear".*"enabled": true'; then
        echo -e "   ${GREEN}✓ Linear integration enabled${NC}"
    else
        echo -e "   ${YELLOW}○ Linear integration disabled${NC}"
    fi
else
    echo -e "   ${YELLOW}⚠ Could not retrieve integration status${NC}"
fi

# Summary
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              STARTUP COMPLETE                ║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║  Dashboard:  ${GREEN}http://localhost:$api_port${BLUE}                   ║${NC}"
echo -e "${BLUE}║  API Docs:   ${GREEN}http://localhost:$api_port/docs${BLUE}              ║${NC}"
echo -e "${BLUE}║  Health:     ${GREEN}http://localhost:$api_port/api/health${BLUE}        ║${NC}"
echo -e "${BLUE}║  Services:   ${GREEN}http://localhost:$api_port/api/services${BLUE}      ║${NC}"
if [ "$1" == "--with-ui" ]; then
echo -e "${BLUE}║  Agent UI:   ${GREEN}http://localhost:3000${BLUE}                       ║${NC}"
fi
echo -e "${BLUE}╠══════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║  Management Commands:                        ║${NC}"
echo -e "${BLUE}║  Status:     ${YELLOW}python3 scripts/orchestrate.py status${BLUE}  ║${NC}"
echo -e "${BLUE}║  Stop All:   ${YELLOW}python3 scripts/orchestrate.py stop --all${BLUE}║${NC}"
echo -e "${BLUE}║  Restart:    ${YELLOW}python3 scripts/orchestrate.py restart <svc>${BLUE}║${NC}"
echo -e "${BLUE}║  Health:     ${YELLOW}python3 scripts/orchestrate.py check${BLUE}      ║${NC}"
echo -e "${BLUE}╠══════════════════════════════════════════════╣${NC}"
echo -e "${BLUE}║  Legacy:     ${YELLOW}./stop_sophia_unified.sh${BLUE}                 ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════╝${NC}"

# Show final service status
echo ""
echo -e "${YELLOW}Final Service Status:${NC}"
python3 "$SOPHIA_HOME/scripts/orchestrate.py" status

# Save startup state using orchestrator
echo ""
echo -e "${YELLOW}Saving startup state...${NC}"
python3 -c "
import json
import subprocess
import sys
from datetime import datetime

try:
    # Get service status from orchestrator
    result = subprocess.run([
        'python3', '$SOPHIA_HOME/scripts/orchestrate.py', 'status', '--json'
    ], capture_output=True, text=True, cwd='$SOPHIA_HOME')
    
    if result.returncode == 0:
        # Parse orchestrator output if available
        startup_state = {
            'started_at': datetime.now().isoformat(),
            'startup_method': 'orchestrator',
            'orchestrator_available': True,
            'api_port': $api_port,
            'service_types_started': '$SERVICE_TYPES'.split()
        }
    else:
        # Fallback state
        startup_state = {
            'started_at': datetime.now().isoformat(),
            'startup_method': 'legacy',
            'orchestrator_available': False,
            'api_port': $api_port
        }
    
    with open('$SOPHIA_HOME/.sophia-state.json', 'w') as f:
        json.dump(startup_state, f, indent=2)
    
    print('✓ Startup state saved to .sophia-state.json')
    
except Exception as e:
    print(f'Warning: Could not save startup state: {e}', file=sys.stderr)
"

echo -e "${GREEN}Startup process completed!${NC}"
echo -e "Use ${YELLOW}python3 scripts/orchestrate.py --help${NC} for service management options"

exit 0
