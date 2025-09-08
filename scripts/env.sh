#!/bin/bash
# Shared Environment Loader for Sophia Intel AI
# Sets common environment and loads .env files
# Used by all shell scripts to ensure consistency

set -euo pipefail

# Colors for output
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[0;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export NC='\033[0m' # No Color

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Load environment files if they exist
load_env_file() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        # Export variables while filtering comments and empty lines
        set -a
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            if [[ ! "$key" =~ ^# ]] && [[ -n "$key" ]]; then
                # Remove leading/trailing whitespace
                key=$(echo "$key" | xargs)
                value=$(echo "$value" | xargs)
                if [ -n "$key" ] && [ -n "$value" ]; then
                    export "$key=$value"
                fi
            fi
        done < "$env_file"
        set +a
        echo -e "${GREEN}✓${NC} Loaded: $env_file"
    fi
}

# Load environment files in order of precedence
cd "$PROJECT_ROOT"
load_env_file ".env"
load_env_file ".env.mcp"
load_env_file ".env.sophia"
# Note: .env.artemis should be in Artemis CLI repo, not here

# Set default environment variables
export ENVIRONMENT="${ENVIRONMENT:-development}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export MCP_MEMORY_HOST="${MCP_MEMORY_HOST:-localhost}"
export MCP_MEMORY_PORT="${MCP_MEMORY_PORT:-8765}"
export MCP_BRIDGE_PORT="${MCP_BRIDGE_PORT:-8766}"

# Ensure Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Verify no virtual environments are active
if [ -n "${VIRTUAL_ENV:-}" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment detected: $VIRTUAL_ENV${NC}"
    echo -e "${YELLOW}   Deactivating to use system Python...${NC}"
    deactivate 2>/dev/null || true
    unset VIRTUAL_ENV
fi

# Function to check for virtual environments in repo
check_no_venv() {
    local venv_count=$(find "$PROJECT_ROOT" -name "venv" -o -name ".venv" -o -name "pyvenv.cfg" 2>/dev/null | wc -l)
    if [ "$venv_count" -gt 0 ]; then
        echo -e "${RED}⚠️  WARNING: Virtual environments detected in repository!${NC}"
        echo -e "${RED}   Run 'make clean-venv' to remove them${NC}"
        return 1
    fi
    return 0
}

# Print environment summary (redact secrets)
print_env_summary() {
    echo -e "\n${CYAN}Environment Summary:${NC}"
    echo "  • Environment: $ENVIRONMENT"
    echo "  • Python: $(python3 --version)"
    echo "  • Project Root: $PROJECT_ROOT"
    echo "  • MCP Memory: $MCP_MEMORY_HOST:$MCP_MEMORY_PORT"
    echo "  • MCP Bridge: $MCP_MEMORY_HOST:$MCP_BRIDGE_PORT"
    echo "  • Log Level: $LOG_LEVEL"
    
    # Show loaded API keys (redacted)
    echo -e "\n${CYAN}API Keys Status:${NC}"
    
    # Business keys (should be in Sophia)
    for key in APOLLO_API_KEY SLACK_API_TOKEN SALESFORCE_CLIENT_ID ASANA_API_TOKEN LINEAR_API_KEY HUBSPOT_API_KEY LOOKER_CLIENT_ID NETSUITE_CLIENT_ID; do
        if [ -n "${!key:-}" ]; then
            echo "  • $key: ***$(echo ${!key} | tail -c 5)"
        fi
    done
    
    # AI model keys (should NOT be in Sophia)
    local ai_keys_found=false
    for key in ANTHROPIC_API_KEY OPENAI_API_KEY GROQ_API_KEY GROK_API_KEY DEEPSEEK_API_KEY; do
        if [ -n "${!key:-}" ]; then
            echo -e "  ${RED}• $key: FOUND (should be in Artemis only!)${NC}"
            ai_keys_found=true
        fi
    done
    
    if [ "$ai_keys_found" = true ]; then
        echo -e "${YELLOW}⚠️  AI model keys detected in Sophia environment${NC}"
    fi
    
    echo ""
}

# Export utility functions
export -f load_env_file
export -f check_no_venv
export -f print_env_summary

# Common logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

export -f log_info
export -f log_success
export -f log_warning
export -f log_error