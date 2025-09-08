#!/bin/bash
# Unified Startup Script for Sophia Intel AI
# Single entry point replacing 14+ fragmented scripts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}    🚀 SOPHIA INTEL AI - UNIFIED STARTUP SYSTEM${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
        exit 1
    fi
    
    # Check for virtual environments (should be NONE)
    VENV_COUNT=$(find . -name "venv" -o -name ".venv" -o -name "pyvenv.cfg" 2>/dev/null | wc -l)
    if [ "$VENV_COUNT" -gt 0 ]; then
        echo -e "${RED}⚠️  WARNING: Virtual environments detected!${NC}"
        echo -e "${RED}   These should be removed for proper operation.${NC}"
        find . -name "venv" -o -name ".venv" -o -name "pyvenv.cfg" 2>/dev/null | head -5
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check environment files
    echo -e "${YELLOW}📋 Checking environment files...${NC}"
    
    if [ ! -f ".env.mcp" ]; then
        echo -e "${YELLOW}   Creating .env.mcp template...${NC}"
        cat > .env.mcp << 'EOF'
# MCP Bridge Configuration
MCP_MEMORY_HOST=0.0.0.0
MCP_MEMORY_PORT=8765
MCP_BRIDGE_PORT=8766
MCP_DOMAIN_ISOLATION=true
MCP_LOG_LEVEL=INFO
EOF
    fi
    
    if [ ! -f ".env.sophia" ]; then
        echo -e "${YELLOW}   Creating .env.sophia template...${NC}"
        cat > .env.sophia << 'EOF'
# Sophia Business Intelligence Keys
# Add your business service API keys here
# APOLLO_API_KEY=
# SLACK_API_TOKEN=
# SALESFORCE_CLIENT_ID=
# ASANA_API_TOKEN=

# Infrastructure
POSTGRES_URL=postgresql://sophia:password@localhost:5432/sophia
REDIS_URL=redis://localhost:6379
EOF
    fi
    
    # Verify key separation
    echo -e "${YELLOW}🔐 Verifying API key separation...${NC}"
    
    # Check for AI keys in Sophia (should not exist)
    if [ -f ".env.sophia" ]; then
        if grep -q "ANTHROPIC\|OPENAI\|GROQ\|GROK" .env.sophia 2>/dev/null; then
            echo -e "${RED}❌ AI model keys detected in .env.sophia!${NC}"
            echo -e "${RED}   These should only be in Artemis CLI environment.${NC}"
            read -p "Continue with contaminated environment? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi
    
    echo -e "${GREEN}✅ Prerequisites check complete${NC}"
    echo ""
}

# Function to display startup options
show_options() {
    echo -e "${BLUE}📊 Startup Configuration:${NC}"
    echo "   Environment: ${ENVIRONMENT:-development}"
    echo "   Config File: ${CONFIG_FILE:-startup-config.yml}"
    echo "   Health Check: ${HEALTH_CHECK:-enabled}"
    echo "   Dry Run: ${DRY_RUN:-false}"
    echo ""
}

# Parse command line arguments
ENVIRONMENT=${ENVIRONMENT:-development}
CONFIG_FILE="startup-config.yml"
HEALTH_CHECK="enabled"
DRY_RUN="false"
EXTRA_ARGS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --no-health-check)
            HEALTH_CHECK="disabled"
            EXTRA_ARGS="$EXTRA_ARGS --no-health-check"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            EXTRA_ARGS="$EXTRA_ARGS --dry-run"
            shift
            ;;
        --help)
            echo "Unified Startup Script for Sophia Intel AI"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --environment ENV      Set environment (development/production)"
            echo "  --config FILE         Use specific config file"
            echo "  --no-health-check     Skip health checks"
            echo "  --dry-run            Show what would be done without starting"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0"
            echo "  $0 --environment production"
            echo "  $0 --dry-run"
            echo ""
            exit 0
            ;;
        *)
            EXTRA_ARGS="$EXTRA_ARGS $1"
            shift
            ;;
    esac
done

# Run prerequisite checks
check_prerequisites

# Show configuration
show_options

# Check if orchestrator exists
if [ ! -f "scripts/unified_orchestrator.py" ]; then
    echo -e "${RED}❌ Unified orchestrator not found!${NC}"
    echo "   Expected at: scripts/unified_orchestrator.py"
    exit 1
fi

# Create startup config if it doesn't exist
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}📝 Creating default startup configuration...${NC}"
    cat > "$CONFIG_FILE" << 'EOF'
version: "2.0"
environment: development

services:
  # Infrastructure Layer
  redis:
    domain: infrastructure
    command: "redis-server"
    port: 6379
    health_check: "redis-cli ping"
    priority: 1
    required: true
    
  # MCP Bridge Layer  
  mcp_memory:
    domain: mcp
    command: "python3 mcp_memory_server/main.py"
    port: 8765
    depends_on: [redis]
    env_file: .env.mcp
    health_endpoint: "/health"
    priority: 2
    required: true
    
  mcp_bridge:
    domain: mcp
    command: "python3 mcp-bridge/server.py"
    port: 8766
    depends_on: [mcp_memory]
    env_file: .env.mcp
    health_endpoint: "/health"
    priority: 2
    required: true
    
  # Sophia Domain
  sophia_backend:
    domain: sophia
    command: "python3 backend/main.py"
    port: 8000
    depends_on: [redis, mcp_bridge]
    env_file: .env.sophia
    health_endpoint: "/health"
    priority: 3
    required: true
EOF
fi

# Start the unified orchestrator
echo -e "${GREEN}🚀 Starting Unified Orchestrator...${NC}"
echo ""

# Export environment variables
export ENVIRONMENT="$ENVIRONMENT"

# Run the orchestrator
if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}🔸 DRY RUN MODE - No services will actually start${NC}"
fi

python3 scripts/unified_orchestrator.py \
    --config "$CONFIG_FILE" \
    --environment "$ENVIRONMENT" \
    $EXTRA_ARGS

# Orchestrator will handle everything from here
# Including keeping services running and graceful shutdown