#!/bin/bash
# =============================================================================
# Sophia AI Platform v3.2 - Unified Management Script
# =============================================================================

# -----------------------------------------------------------------------------
# SHARED CONFIGURATION
# -----------------------------------------------------------------------------
SOPHIA_HOME="/opt/sophia"
SOPHIA_MAIN="/home/ubuntu/sophia-main"
LOGS_DIR="$SOPHIA_HOME/logs"
PIDS_DIR="$SOPHIA_HOME/pids"
SECRETS_DIR="$SOPHIA_HOME/secrets"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# VALIDATION FUNCTIONS
# -----------------------------------------------------------------------------
validate_platform() {
    echo -e "${BLUE}=== SOPHIA AI PLATFORM v3.2 VALIDATION ===${NC}"
    echo "=========================================="
    
    local TOTAL_CHECKS=0
    local PASSED_CHECKS=0
    local CRITICAL_FAILURES=()
    
    # Function to check and report
    check_item() {
        local description="$1"
        local condition="$2"
        local critical="${3:-false}"
        
        ((TOTAL_CHECKS++))
        if eval "$condition"; then
            echo -e "${GREEN}✅${NC} $description"
            ((PASSED_CHECKS++))
            return 0
        else
            echo -e "${RED}❌${NC} $description"
            if [ "$critical" = "true" ]; then
                CRITICAL_FAILURES+=("$description")
            fi
            return 1
        fi
    }
    
    # 1. Check UV environments
    echo -e "\n${YELLOW}1️⃣ UV ENVIRONMENTS:${NC}"
        # Note: Virtual environment management removed - use system Python
        check_item "System Python available" "command -v python3 >/dev/null"
    
    # 2. Verify encrypted environment
    echo -e "\n${YELLOW}2️⃣ ENCRYPTED ENVIRONMENT:${NC}"
    check_item "Encrypted environment file" "[ -f '$SECRETS_DIR/.env.encrypted' ]" true
    if [ -f "$SECRETS_DIR/.env.encrypted" ]; then
        local perms=$(stat -c %a "$SECRETS_DIR/.env.encrypted" 2>/dev/null)
        check_item "Encrypted env permissions (600)" "[ '$perms' = '600' ]" true
    fi
    
    # 3. Test credential decryption
    echo -e "\n${YELLOW}3️⃣ CREDENTIAL SYSTEM:${NC}"
    if [ -f "$SECRETS_DIR/env_manager.py" ]; then
        if python3 -c "
import sys
sys.path.append('$SECRETS_DIR')
try:
    from env_manager import SecureEnvManager
    manager = SecureEnvManager()
    exit(0 if manager.verify_env() else 1)
except:
    exit(2)
" 2>/dev/null; then
            check_item "Credential validation" "true"
        else
            check_item "Credential validation" "false" true
        fi
    else
        check_item "env_manager.py exists" "false" true
    fi
    
    # 4. Test AI router
    echo -e "\n${YELLOW}4️⃣ AI ROUTER:${NC}"
    check_item "ai_router.py exists" "[ -f '$SOPHIA_MAIN/ai_router.py' ]"
    
    # 5. Check Lambda Labs connectivity
    echo -e "\n${YELLOW}5️⃣ LAMBDA LABS:${NC}"
    if command -v curl &> /dev/null; then
        if [ -n "$LAMBDA_API_KEY" ]; then
            response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $LAMBDA_API_KEY" \
                      "https://cloud.lambdalabs.com/api/v1/instances" 2>/dev/null | tail -n1)
            check_item "Lambda Labs API accessible" "[ '$response' = '200' ]"
        else
            echo -e "${YELLOW}⚠️${NC} Lambda API key not loaded"
        fi
    fi
    
    # 6. Security checks
    echo -e "\n${YELLOW}6️⃣ SECURITY:${NC}"
    check_item "Secrets directory permissions (700)" \
               "[ $(stat -c %a '$SECRETS_DIR' 2>/dev/null) = '700' ]" true
    check_item "No plaintext .env file" "[ ! -f '$SECRETS_DIR/.env' ]" true
    check_item "PID directory exists" "[ -d '$PIDS_DIR' ]"
    check_item "Logs directory exists" "[ -d '$LOGS_DIR' ]"
    
    # 7. Port availability
    echo -e "\n${YELLOW}7️⃣ PORT AVAILABILITY:${NC}"
    for port in 8000 8001 3000; do
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            check_item "Port $port available" "true"
        else
            check_item "Port $port available" "false"
            echo -e "  ${YELLOW}↳ Process using port:${NC} $(lsof -Pi :$port -sTCP:LISTEN 2>/dev/null | tail -n1)"
        fi
    done
    
    # 8. Service status
    echo -e "\n${YELLOW}8️⃣ SERVICE STATUS:${NC}"
    for service in api mcp router; do
        if [ -f "$PIDS_DIR/$service.pid" ]; then
            pid=$(cat "$PIDS_DIR/$service.pid")
            if ps -p $pid > /dev/null 2>&1; then
                check_item "$service service running (PID: $pid)" "true"
            else
                check_item "$service service running" "false"
                rm -f "$PIDS_DIR/$service.pid"
            fi
        else
            echo -e "${YELLOW}○${NC} $service service not started"
        fi
    done
    
    # 9. Dependencies check
    echo -e "\n${YELLOW}9️⃣ DEPENDENCIES:${NC}"
    check_item "Python 3 installed" "command -v python3 &> /dev/null"
    check_item "Docker installed" "command -v docker &> /dev/null"
    check_item "UV installed" "command -v uv &> /dev/null || [ -f '$HOME/.cargo/bin/uv' ]"
    
    # Final report
    echo -e "\n${BLUE}=== VALIDATION SUMMARY ===${NC}"
    local percentage=$((PASSED_CHECKS * 100 / TOTAL_CHECKS))
    echo -e "Score: ${PASSED_CHECKS}/${TOTAL_CHECKS} (${percentage}%)"
    
    if [ ${#CRITICAL_FAILURES[@]} -gt 0 ]; then
        echo -e "\n${RED}CRITICAL FAILURES:${NC}"
        for failure in "${CRITICAL_FAILURES[@]}"; do
            echo -e "  ${RED}•${NC} $failure"
        done
    fi
    
    if [ $percentage -ge 90 ]; then
        echo -e "\n${GREEN}🎉 PLATFORM READY FOR PRODUCTION!${NC}"
        return 0
    elif [ $percentage -ge 70 ]; then
        echo -e "\n${YELLOW}⚡ Platform mostly ready, minor fixes needed${NC}"
        return 1
    else
        echo -e "\n${RED}🔧 Platform needs significant setup${NC}"
        return 2
    fi
}

# -----------------------------------------------------------------------------
# PRODUCTION LAUNCH FUNCTIONS
# -----------------------------------------------------------------------------
launch_production() {
    echo -e "${BLUE}🚀 LAUNCHING SOPHIA AI PLATFORM v3.2${NC}"
    echo "===================================="
    
    # Pre-flight checks
    echo -e "\n${YELLOW}Running pre-flight checks...${NC}"
    
    # Create necessary directories
    mkdir -p "$LOGS_DIR" "$PIDS_DIR"
    
    # Check if already running
    local services_running=false
    for service in api mcp router; do
        if [ -f "$PIDS_DIR/$service.pid" ]; then
            pid=$(cat "$PIDS_DIR/$service.pid")
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}⚠️  $service already running (PID: $pid)${NC}"
                services_running=true
            fi
        fi
    done
    
    if [ "$services_running" = true ]; then
        read -p "Some services are already running. Stop them first? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_services
        else
            echo -e "${RED}Aborting launch${NC}"
            return 1
        fi
    fi
    
    # Load secure environment
    echo -e "\n${YELLOW}🔐 Loading secure environment...${NC}"
    if [ -f "$SECRETS_DIR/activate_env.sh" ]; then
        cd "$SECRETS_DIR"
        source activate_env.sh production
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Secure environment loaded${NC}"
        else
            echo -e "${RED}❌ Failed to load environment${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Environment activation script not found${NC}"
        return 1
    fi
    
    # Start services with proper error handling
    cd "$SOPHIA_HOME"
    
    # Function to start a service (uses system Python, no venv)
    start_service() {
        local name="$1"
        local command="$2"
        local port="${3:-}"
        
        echo -e "\n${YELLOW}Starting $name...${NC}"
        
        # Check port if specified
        if [ -n "$port" ]; then
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                echo -e "${RED}❌ Port $port already in use${NC}"
                return 1
            fi
        fi
        
        # Start service with system Python (no venv activation)
        eval "$command" > "$LOGS_DIR/$name.log" 2>&1 &
        local pid=$!
        echo $pid > "$PIDS_DIR/$name.pid"
        
        # Wait a moment and check if process started
        sleep 2
        if ps -p $pid > /dev/null; then
            echo -e "${GREEN}✅ $name started (PID: $pid)${NC}"
            [ -n "$port" ] && echo -e "   ${BLUE}→ Available at: http://localhost:$port${NC}"
            return 0
        else
            echo -e "${RED}❌ $name failed to start${NC}"
            echo -e "   Check logs: $LOGS_DIR/$name.log"
            rm -f "$PIDS_DIR/$name.pid"
            return 1
        fi
    }
    
    # Start services
    if [ -f "backend/main.py" ]; then
        start_service "api" "uvicorn backend.main:app --host ${BIND_IP} --port 8000" "8000"
    fi
    
    if [ -f "mcp_servers/master_mcp_server.py" ]; then
        start_service "mcp" "python mcp_servers/master_mcp_server.py" "8001"
    fi
    
    if [ -f "$SOPHIA_MAIN/ai_router.py" ]; then
        (cd "$SOPHIA_MAIN" && start_service "router" "python ai_router.py" "")
    fi
    
    # Start monitoring if available
    if [ -f "docker-compose.yml" ] && command -v docker-compose &> /dev/null; then
        echo -e "\n${YELLOW}Starting monitoring services...${NC}"
        docker-compose up -d prometheus grafana 2>/dev/null && \
            echo -e "${GREEN}✅ Monitoring started${NC}" || \
            echo -e "${YELLOW}⚠️  Monitoring not available${NC}"
    fi
    
    # Final status
    echo -e "\n${GREEN}🎉 LAUNCH COMPLETE!${NC}"
    echo "============================="
    show_status
}

# -----------------------------------------------------------------------------
# SERVICE MANAGEMENT FUNCTIONS
# -----------------------------------------------------------------------------
stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    
    for service in api mcp router; do
        if [ -f "$PIDS_DIR/$service.pid" ]; then
            pid=$(cat "$PIDS_DIR/$service.pid")
            if ps -p $pid > /dev/null 2>&1; then
                kill $pid
                echo -e "${GREEN}✅${NC} Stopped $service (PID: $pid)"
            fi
            rm -f "$PIDS_DIR/$service.pid"
        fi
    done
    
    # Stop docker services if running
    if command -v docker-compose &> /dev/null; then
        cd "$SOPHIA_HOME"
        docker-compose down 2>/dev/null
    fi
}

restart_services() {
    echo -e "${YELLOW}Restarting services...${NC}"
    stop_services
    sleep 2
    launch_production
}

show_status() {
    echo -e "\n${BLUE}📊 SERVICE STATUS${NC}"
    echo "=================="
    
    for service in api mcp router; do
        if [ -f "$PIDS_DIR/$service.pid" ]; then
            pid=$(cat "$PIDS_DIR/$service.pid")
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${GREEN}●${NC} $service: Running (PID: $pid)"
            else
                echo -e "${RED}●${NC} $service: Stopped (stale PID file)"
            fi
        else
            echo -e "${YELLOW}○${NC} $service: Not started"
        fi
    done
    
    echo -e "\n${BLUE}📝 RESOURCES${NC}"
    echo "============="
    echo "• Logs: $LOGS_DIR/"
    echo "• PIDs: $PIDS_DIR/"
    echo "• API Docs: http://localhost:8000/docs"
    echo "• MCP Server: http://localhost:8001"
    echo "• Grafana: ${SOPHIA_FRONTEND_ENDPOINT}"
}

show_logs() {
    local service="${1:-api}"
    if [ -f "$LOGS_DIR/$service.log" ]; then
        tail -f "$LOGS_DIR/$service.log"
    else
        echo -e "${RED}No logs found for $service${NC}"
    fi
}

# -----------------------------------------------------------------------------
# MAIN COMMAND ROUTER
# -----------------------------------------------------------------------------
case "$1" in
    validate)
        validate_platform
        ;;
    launch|start)
        launch_production
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    *)
        echo "Sophia AI Platform v3.2 Management Script"
        echo "========================================="
        echo "Usage: $0 {validate|launch|stop|restart|status|logs [service]}"
        echo ""
        echo "Commands:"
        echo "  validate - Run comprehensive system validation"
        echo "  launch   - Start all services in production mode"
        echo "  stop     - Stop all running services"
        echo "  restart  - Restart all services"
        echo "  status   - Show current service status"
        echo "  logs     - Tail logs (default: api, or specify service)"
        echo ""
        echo "Examples:"
        echo "  $0 validate        # Check system readiness"
        echo "  $0 launch          # Start production services"
        echo "  $0 logs mcp        # View MCP server logs"
        ;;
esac
