#!/bin/bash
# Sophia Business Intelligence - One-Command Startup Script
# Starts all necessary services for local development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SOPHIA_API_PORT=8003
SOPHIA_UI_PORT=3000
REDIS_PORT=6379
POSTGRES_PORT=5432
WEAVIATE_PORT=8080

echo -e "${BLUE}🎯 SOPHIA BUSINESS INTELLIGENCE - RAPID START${NC}"
echo "============================================="
echo ""

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for a service
wait_for_service() {
    local name=$1
    local check_cmd=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "  Waiting for $name"
    while [ $attempt -lt $max_attempts ]; do
        if eval $check_cmd >/dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

# Function to check required environment variables
check_environment() {
    echo -e "${YELLOW}📋 Checking environment...${NC}"
    
    # Create secure config directory if not exists
    if [ ! -d ~/.config/sophia ]; then
        mkdir -p ~/.config/sophia
        chmod 700 ~/.config/sophia
    fi
    
    # Create config template if not exists
    if [ ! -f ~/.config/sophia/env ]; then
        cat > ~/.config/sophia/env <<'EOF'
# Sophia Business Intelligence Configuration
# Add your real API keys here

# Core Business Integrations (REQUIRED for full functionality)
GONG_ACCESS_KEY=
GONG_ACCESS_SECRET=
SALESFORCE_CLIENT_ID=
SALESFORCE_CLIENT_SECRET=
SALESFORCE_USERNAME=
SALESFORCE_PASSWORD=
SALESFORCE_SECURITY_TOKEN=
SALESFORCE_INSTANCE_URL=
HUBSPOT_API_KEY=
LOOKERSDK_BASE_URL=
LOOKERSDK_CLIENT_ID=
LOOKERSDK_CLIENT_SECRET=
SLACK_BOT_TOKEN=
SLACK_USER_TOKEN=
ASANA_ACCESS_TOKEN=
ASANA_WORKSPACE_ID=
LINEAR_API_KEY=
LINEAR_TEAM_ID=
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=

# Infrastructure (defaults work for local dev)
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://sophia:sophia@localhost:5432/sophia
WEAVIATE_URL=http://localhost:8080

# AI Providers (optional but recommended)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
PORTKEY_API_KEY=

# Security
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
EOF
        chmod 600 ~/.config/sophia/env
        echo -e "  ${GREEN}✓${NC} Created config template at ~/.config/sophia/env"
        echo -e "  ${YELLOW}⚠${NC}  Please add your API keys to this file and run again"
        exit 1
    fi
    
    # Load environment
    if [ -f scripts/env.sh ]; then
        source scripts/env.sh --quiet
    else
        # Fallback to manual loading
        export $(grep -v '^#' ~/.config/sophia/env | xargs) 2>/dev/null || true
        export $(grep -v '^#' .env 2>/dev/null | xargs) 2>/dev/null || true
        export $(grep -v '^#' .env.local 2>/dev/null | xargs) 2>/dev/null || true
    fi
    
    # Check for at least one integration configured
    local has_integration=false
    if [ -n "${GONG_ACCESS_KEY:-}" ] || [ -n "${SLACK_BOT_TOKEN:-}" ] || [ -n "${SALESFORCE_CLIENT_ID:-}" ]; then
        has_integration=true
    fi
    
    if [ "$has_integration" = false ]; then
        echo -e "  ${YELLOW}⚠${NC}  No integrations configured (optional for basic testing)"
        echo "     Add API keys to ~/.config/sophia/env for full functionality"
    else
        echo -e "  ${GREEN}✓${NC} Environment configured"
    fi
}

# Function to start infrastructure
start_infrastructure() {
    echo -e "${YELLOW}🐳 Starting infrastructure services...${NC}"
    
    # Check if docker-compose file exists
    if [ ! -f docker-compose.dev.yml ]; then
        echo -e "  ${RED}✗${NC} docker-compose.dev.yml not found"
        exit 1
    fi
    
    # Start core services
    echo "  Starting Redis, PostgreSQL, and Weaviate..."
    docker-compose -f docker-compose.dev.yml up -d redis postgres weaviate 2>/dev/null || {
        echo -e "  ${RED}✗${NC} Failed to start infrastructure"
        echo "     Make sure Docker is running"
        exit 1
    }
    
    # Wait for services
    wait_for_service "Redis" "redis-cli -p $REDIS_PORT ping"
    wait_for_service "PostgreSQL" "docker exec sophia-postgres pg_isready -U sophia"
    wait_for_service "Weaviate" "curl -sf http://localhost:$WEAVIATE_PORT/v1/.well-known/ready"
    
    echo -e "  ${GREEN}✓${NC} Infrastructure ready"
}

# Function to start the API
start_api() {
    echo -e "${YELLOW}🚀 Starting Sophia API...${NC}"
    
    # Kill existing API if running
    if check_port $SOPHIA_API_PORT; then
        echo "  Stopping existing API on port $SOPHIA_API_PORT..."
        pkill -f "uvicorn.*$SOPHIA_API_PORT" 2>/dev/null || true
        sleep 2
    fi
    
    # Check if production server exists
    if [ -f app/api/production_server.py ]; then
        echo "  Starting production server on port $SOPHIA_API_PORT..."
        nohup uvicorn app.api.production_server:create_production_app \
            --host 0.0.0.0 \
            --port $SOPHIA_API_PORT \
            --reload \
            --log-level info > logs/sophia-api.log 2>&1 &
        
        # Wait for API to start
        wait_for_service "API" "curl -sf http://localhost:$SOPHIA_API_PORT/health"
        echo -e "  ${GREEN}✓${NC} API ready at http://localhost:$SOPHIA_API_PORT"
        echo -e "     API Docs: http://localhost:$SOPHIA_API_PORT/docs"
    else
        echo -e "  ${YELLOW}⚠${NC}  Production server not found, using fallback"
        # Fallback to unified server or other
        if [ -f app/api/unified_server.py ]; then
            nohup python -m uvicorn app.api.unified_server:app \
                --host 0.0.0.0 \
                --port $SOPHIA_API_PORT \
                --reload > logs/sophia-api.log 2>&1 &
        fi
    fi
}

# Function to start the UI
start_ui() {
    echo -e "${YELLOW}🎨 Starting Sophia Dashboard...${NC}"
    
    # Check if agent-ui directory exists
    if [ ! -d agent-ui ]; then
        echo -e "  ${YELLOW}⚠${NC}  agent-ui directory not found"
        echo "     Dashboard will not be available"
        return
    fi
    
    cd agent-ui
    
    # Create UI environment file if needed
    if [ ! -f .env.local ]; then
        echo "NEXT_PUBLIC_API_URL=http://localhost:$SOPHIA_API_PORT" > .env.local
        echo -e "  ${GREEN}✓${NC} Created UI environment file"
    fi
    
    # Install dependencies if needed
    if [ ! -d node_modules ]; then
        echo "  Installing UI dependencies..."
        if command -v pnpm &> /dev/null; then
            pnpm install > /dev/null 2>&1
        elif command -v npm &> /dev/null; then
            npm install > /dev/null 2>&1
        else
            echo -e "  ${RED}✗${NC} No package manager found (pnpm or npm required)"
            cd ..
            return
        fi
    fi
    
    # Kill existing UI if running
    if check_port $SOPHIA_UI_PORT; then
        echo "  Stopping existing UI on port $SOPHIA_UI_PORT..."
        pkill -f "next.*dev" 2>/dev/null || true
        sleep 2
    fi
    
    # Start UI
    echo "  Starting Next.js dashboard..."
    if command -v pnpm &> /dev/null; then
        nohup pnpm dev > ../logs/sophia-ui.log 2>&1 &
    else
        nohup npm run dev > ../logs/sophia-ui.log 2>&1 &
    fi
    
    cd ..
    
    # Wait for UI
    sleep 5
    if check_port $SOPHIA_UI_PORT; then
        echo -e "  ${GREEN}✓${NC} Dashboard ready at http://localhost:$SOPHIA_UI_PORT"
    else
        echo -e "  ${YELLOW}⚠${NC}  Dashboard may still be starting..."
    fi
}

# Function to run health check
run_health_check() {
    echo -e "${YELLOW}🏥 Running health checks...${NC}"
    
    # Check basic API health
    if curl -sf http://localhost:$SOPHIA_API_PORT/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} API is healthy"
    else
        echo -e "  ${RED}✗${NC} API health check failed"
    fi
    
    # Check integration health
    echo "  Checking integrations..."
    local health_response=$(curl -sf http://localhost:$SOPHIA_API_PORT/health/integrations 2>/dev/null || echo "{}")
    
    if command -v jq &> /dev/null && [ -n "$health_response" ]; then
        local overall=$(echo "$health_response" | jq -r '.overall // "unknown"')
        local healthy=$(echo "$health_response" | jq -r '.healthy_count // 0')
        local total=$(echo "$health_response" | jq -r '.total_integrations // 0')
        
        if [ "$overall" = "healthy" ]; then
            echo -e "  ${GREEN}✓${NC} All integrations healthy ($healthy/$total)"
        elif [ "$overall" = "degraded" ]; then
            echo -e "  ${YELLOW}⚠${NC}  Some integrations degraded ($healthy/$total healthy)"
        else
            echo -e "  ${YELLOW}⚠${NC}  Integration status: $overall ($healthy/$total healthy)"
        fi
    else
        echo "  Integration health endpoint: http://localhost:$SOPHIA_API_PORT/health/integrations"
    fi
}

# Function to display final status
display_status() {
    echo ""
    echo -e "${GREEN}✅ SOPHIA IS READY!${NC}"
    echo ""
    echo "📚 Quick Links:"
    echo "  Dashboard:    http://localhost:$SOPHIA_UI_PORT"
    echo "  API:          http://localhost:$SOPHIA_API_PORT"
    echo "  API Docs:     http://localhost:$SOPHIA_API_PORT/docs"
    echo "  Health:       http://localhost:$SOPHIA_API_PORT/health/integrations"
    echo ""
    echo "📋 Available Commands:"
    echo "  make sophia-health   - Check system health"
    echo "  make sophia-logs     - View logs"
    echo "  make sophia-stop     - Stop all services"
    echo ""
    echo "📝 Logs:"
    echo "  API: logs/sophia-api.log"
    echo "  UI:  logs/sophia-ui.log"
    echo ""
}

# Main execution
main() {
    # Create logs directory
    mkdir -p logs
    
    # Run startup sequence
    check_environment
    start_infrastructure
    start_api
    start_ui
    
    # Give services time to stabilize
    sleep 3
    
    # Run health check
    run_health_check
    
    # Display status
    display_status
}

# Handle script termination
trap 'echo -e "\n${YELLOW}Startup interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"