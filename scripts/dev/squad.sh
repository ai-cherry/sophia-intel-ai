#!/bin/bash
# Sophia Squad Development Orchestrator
# Enhanced script with proper MCP paths and environment handling

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
PROJECT_DIR="${SOPHIA_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
LOG_DIR="${PROJECT_DIR}/logs/squad"
CONFIG_DIR="${HOME}/.config/sophia"
ENV_FILE="${CONFIG_DIR}/env"

# MCP Server Configuration
MCP_MEMORY_PORT="${MCP_MEMORY_PORT:-8081}"
MCP_FS_PORT="${MCP_FS_PORT:-8082}"
MCP_GIT_PORT="${MCP_GIT_PORT:-8084}"

# Export workspace for filesystem server
export WORKSPACE_PATH="${PROJECT_DIR}"
export WORKSPACE_NAME="sophia"

# Function: Print colored message
print_msg() {
    local color=$1
    shift
    echo -e "${color}${*}${NC}"
}

# Function: Load environment variables
load_environment() {
    print_msg "${CYAN}" "Loading environment configuration..."
    
    # Check for environment file
    if [ -f "${ENV_FILE}" ]; then
        # Source environment file safely
        set -a
        source "${ENV_FILE}"
        set +a
        print_msg "${GREEN}" "✓ Environment loaded from ${ENV_FILE}"
    elif [ -f "${PROJECT_DIR}/.env" ]; then
        # Fallback to project .env
        set -a
        source "${PROJECT_DIR}/.env"
        set +a
        print_msg "${YELLOW}" "⚠ Using project .env file (consider using ~/.config/sophia/env)"
    else
        print_msg "${RED}" "✗ No environment file found"
        print_msg "${YELLOW}" "Create one with: cp ${PROJECT_DIR}/.env.example ${ENV_FILE}"
        return 1
    fi
    
    # Validate required variables
    if [ -z "${AIMLAPI_API_KEY:-}" ] || [ "${AIMLAPI_API_KEY}" = "CHANGEME" ]; then
        print_msg "${RED}" "✗ AIMLAPI_API_KEY not configured"
        return 1
    fi
}

# Function: Ensure directories exist
setup_directories() {
    mkdir -p "${LOG_DIR}"
    mkdir -p "${CONFIG_DIR}"
}

# Function: Check dependencies
check_dependencies() {
    local missing=()
    
    for cmd in python3 tmux curl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done
    
    if [ ${#missing[@]} -gt 0 ]; then
        print_msg "${RED}" "Missing dependencies: ${missing[*]}"
        print_msg "${YELLOW}" "Install with: brew install ${missing[*]}"
        return 1
    fi
    
    # Check Python packages
    if ! python3 -c "import uvicorn" 2>/dev/null; then
        print_msg "${YELLOW}" "Installing uvicorn..."
        pip3 install uvicorn
    fi
}

# Function: Wait for service with retries
wait_for_service() {
    local url=$1
    local name=$2
    local max_retries=20
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        if curl -sf "${url}/health" > /dev/null 2>&1; then
            print_msg "${GREEN}" "✓ ${name} is ready"
            return 0
        fi
        retry=$((retry + 1))
        sleep 0.5
    done
    
    print_msg "${RED}" "✗ ${name} failed to start"
    return 1
}

# Function: Start MCP server
start_mcp_server() {
    local name=$1
    local module=$2
    local port=$3
    local extra_env=${4:-}
    
    local url="http://localhost:${port}"
    
    # Check if already running
    if curl -sf "${url}/health" > /dev/null 2>&1; then
        print_msg "${GREEN}" "✓ ${name} already running on port ${port}"
        return 0
    fi
    
    print_msg "${YELLOW}" "Starting ${name}..."
    
    # Start server with proper module path
    cd "${PROJECT_DIR}"
    if [ -n "${extra_env}" ]; then
        export ${extra_env}
    fi
    
    python3 -m uvicorn "${module}" \
        --host 0.0.0.0 \
        --port "${port}" \
        --reload \
        > "${LOG_DIR}/${name}.log" 2>&1 &
    
    # Wait for service to be ready
    wait_for_service "${url}" "${name}"
}

# Function: Start all MCP servers
start_mcp_servers() {
    print_msg "${CYAN}" "${BOLD}Starting MCP servers..."
    
    # Memory server
    start_mcp_server \
        "MCP-Memory" \
        "mcp.memory.server:app" \
        "${MCP_MEMORY_PORT}"
    
    # Filesystem server (needs WORKSPACE_PATH)
    start_mcp_server \
        "MCP-Filesystem" \
        "mcp.filesystem.server:app" \
        "${MCP_FS_PORT}" \
        "WORKSPACE_PATH=${PROJECT_DIR}"
    
    # Git server
    start_mcp_server \
        "MCP-Git" \
        "mcp.git.server:app" \
        "${MCP_GIT_PORT}"
    
    print_msg "${GREEN}" "${BOLD}✓ All MCP servers ready"
}

# Function: Stop MCP servers
stop_mcp_servers() {
    print_msg "${YELLOW}" "Stopping MCP servers..."
    
    for port in ${MCP_MEMORY_PORT} ${MCP_FS_PORT} ${MCP_GIT_PORT}; do
        # Find and kill processes on port
        if lsof -ti:${port} > /dev/null 2>&1; then
            lsof -ti:${port} | xargs kill -9 2>/dev/null || true
            print_msg "${GREEN}" "✓ Stopped service on port ${port}"
        fi
    done
}

# Function: Monitor logs
monitor_logs() {
    print_msg "${CYAN}" "Monitoring MCP server logs..."
    
    # Use tmux for log monitoring
    if command -v tmux &> /dev/null; then
        tmux new-session -d -s "sophia-logs" \
            "tail -f ${LOG_DIR}/*.log"
        print_msg "${GREEN}" "✓ Log monitoring started in tmux session 'sophia-logs'"
        print_msg "${CYAN}" "Attach with: tmux attach -t sophia-logs"
    else
        # Fallback to tail
        tail -f "${LOG_DIR}"/*.log
    fi
}

# Function: Test MCP endpoints
test_mcp_endpoints() {
    print_msg "${CYAN}" "${BOLD}Testing MCP endpoints..."
    
    # Test memory server
    print_msg "${YELLOW}" "Testing Memory Server..."
    curl -X POST "http://localhost:${MCP_MEMORY_PORT}/memory/store" \
        -H "Content-Type: application/json" \
        -d '{"namespace": "test", "content": "test data", "metadata": {}}' \
        -s -o /dev/null -w "Status: %{http_code}\n"
    
    # Test filesystem server
    print_msg "${YELLOW}" "Testing Filesystem Server..."
    curl -X POST "http://localhost:${MCP_FS_PORT}/repo/list" \
        -H "Content-Type: application/json" \
        -d '{"root": ".", "globs": ["*.py"], "limit": 5}' \
        -s | python3 -m json.tool | head -20
    
    # Test git server
    print_msg "${YELLOW}" "Testing Git Server..."
    curl -X POST "http://localhost:${MCP_GIT_PORT}/git/status" \
        -H "Content-Type: application/json" \
        -d '{"repo": "sophia"}' \
        -s | python3 -m json.tool | head -20
    
    print_msg "${GREEN}" "${BOLD}✓ MCP endpoints tested"
}

# Function: Improve file with context
improve_file() {
    local file_path=$1
    
    if [ ! -f "${PROJECT_DIR}/${file_path}" ]; then
        print_msg "${RED}" "File not found: ${file_path}"
        return 1
    fi
    
    print_msg "${CYAN}" "Analyzing ${file_path} with MCP context..."
    
    # Create improvement request
    cat > "${LOG_DIR}/improve_request.json" << EOF
{
    "messages": [
        {
            "role": "user",
            "content": "Analyze and suggest improvements for ${file_path}"
        }
    ],
    "model": "sophia-reviewer",
    "include_context": true,
    "stream": false
}
EOF
    
    # Send to AIML enhanced API
    curl -X POST "http://localhost:8003/api/aiml/chat" \
        -H "Content-Type: application/json" \
        -d @"${LOG_DIR}/improve_request.json" \
        -s | python3 -m json.tool
}

# Function: Show usage
show_usage() {
    cat << EOF
${BOLD}Sophia Squad Development Orchestrator${NC}

${BOLD}Usage:${NC}
    $0 <command> [options]

${BOLD}Commands:${NC}
    start       Start all MCP servers
    stop        Stop all MCP servers
    restart     Restart all MCP servers
    monitor     Monitor server logs
    test        Test MCP endpoints
    improve     Analyze and improve a file
    help        Show this help message

${BOLD}Examples:${NC}
    $0 start                    # Start all servers
    $0 monitor                  # Monitor logs
    $0 improve app/main.py      # Analyze a file
    $0 test                     # Test endpoints

${BOLD}Environment:${NC}
    Config file: ${ENV_FILE}
    Project dir: ${PROJECT_DIR}
    Log dir:     ${LOG_DIR}
EOF
}

# Main execution
main() {
    local command=${1:-help}
    shift || true
    
    # Setup
    setup_directories
    
    case "${command}" in
        start)
            check_dependencies
            load_environment
            start_mcp_servers
            print_msg "${GREEN}" "${BOLD}Squad ready! Test with: $0 test"
            ;;
        stop)
            stop_mcp_servers
            ;;
        restart)
            stop_mcp_servers
            sleep 1
            check_dependencies
            load_environment
            start_mcp_servers
            ;;
        monitor)
            monitor_logs
            ;;
        test)
            test_mcp_endpoints
            ;;
        improve)
            if [ $# -eq 0 ]; then
                print_msg "${RED}" "Usage: $0 improve <file_path>"
                exit 1
            fi
            load_environment
            improve_file "$1"
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_msg "${RED}" "Unknown command: ${command}"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"