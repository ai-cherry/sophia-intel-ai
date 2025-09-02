#!/bin/bash
# ==============================================
# SOPHIA INTEL AI - LOCAL DEVELOPMENT STARTUP
# Production Ready with Real APIs - No Mocks
#
# Following ADR-006: Configuration Management Standardization
# - Uses enhanced EnvLoader with Pulumi ESC integration
# - Environment-aware configuration loading
# - Proper secret management and validation
# ==============================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/startup.log"
VALIDATION_RESULTS="${SCRIPT_DIR}/api_validation_results.json"

# Functions
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%H:%M:%S')
    
    case $level in
        "INFO")  echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "SUCCESS") echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "WARNING") echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "ERROR")   echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" | tee -a "$LOG_FILE" ;;
        "HEADER")  echo -e "${PURPLE}[${timestamp}] ${message}${NC}" | tee -a "$LOG_FILE" ;;
    esac
}

show_banner() {
    echo -e "${CYAN}"
    echo "════════════════════════════════════════════════════════════════"
    echo "  🧠 SOPHIA INTEL AI - LOCAL DEVELOPMENT ENVIRONMENT"
    echo "  🚀 Production Ready with Real APIs - No Mocks"
    echo "  🔧 ADR-006: Enhanced Configuration Management"
    echo "  📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${NC}"
    
    # Show configuration source
    if python3 -c "
from app.config.env_loader import get_env_config
try:
    config = get_env_config()
    print(f'📂 Configuration: {config.loaded_from}')
    print(f'🌍 Environment: {config.environment_name} ({config.environment_type})')
    print(f'🆔 Config Hash: {config.config_hash}')
except:
    print('📂 Configuration: fallback (.env files)')
" 2>/dev/null; then
        :
    else
        echo "📂 Configuration: Loading..."
    fi
    echo -e "${CYAN}════════════════════════════════════════════════════════════════${NC}"
}

check_dependencies() {
    log "INFO" "Checking system dependencies..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log "ERROR" "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log "ERROR" "Python 3 is not installed. Please install Python 3.11+ first."
        exit 1
    fi
    
    # Check required files
    required_files=(".env.local" "docker-compose.local.yml" "scripts/validate-apis.py")
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log "ERROR" "Required file missing: $file"
            exit 1
        fi
    done
    
    log "SUCCESS" "All system dependencies are available"
}

validate_configuration() {
    log "HEADER" "🔍 VALIDATING ENHANCED CONFIGURATION (ADR-006)"
    
    # Install validation dependencies
    pip3 install -q python-dotenv httpx redis || {
        log "ERROR" "Failed to install validation dependencies"
        exit 1
    }
    
    # Test enhanced EnvLoader configuration
    log "INFO" "Testing enhanced EnvLoader with Pulumi ESC integration..."
    if python3 -c "
from app.config.env_loader import get_env_config, validate_environment, print_env_status
import sys

try:
    config = get_env_config()
    validation = validate_environment()
    
    print(f'Configuration loaded from: {config.loaded_from}')
    print(f'Environment: {config.environment_name} ({config.environment_type})')
    print(f'Overall status: {validation.get(\"overall_status\")}')
    
    if validation.get('overall_status') == 'unhealthy':
        print('❌ Configuration validation failed')
        for issue in validation.get('critical_issues', []):
            print(f'  • {issue}')
        sys.exit(1)
    else:
        print('✅ Enhanced configuration validation successful')
        
except Exception as e:
    print(f'❌ Configuration loading failed: {e}')
    sys.exit(1)
"; then
        log "SUCCESS" "✅ Enhanced configuration system validated"
    else
        log "ERROR" "❌ Enhanced configuration validation failed"
        exit 1
    fi
    
    # Run traditional API validation
    log "INFO" "Testing all API connections with real keys..."
    if python3 scripts/validate-apis.py; then
        log "SUCCESS" "✅ All APIs validated successfully"
    else
        log "ERROR" "❌ API validation failed. Check your configuration"
        log "ERROR" "Review the validation results in: $VALIDATION_RESULTS"
        exit 1
    fi
}

cleanup_previous() {
    log "INFO" "Cleaning up previous deployment..."
    
    # Stop and remove containers
    docker-compose -f docker-compose.local.yml down --remove-orphans || true
    
    # Remove dangling images (optional)
    docker image prune -f || true
    
    log "SUCCESS" "Previous deployment cleaned up"
}

build_services() {
    log "HEADER" "🏗️  BUILDING SERVICES"
    
    # Create necessary directories
    mkdir -p monitoring/prometheus monitoring/grafana/dashboards monitoring/grafana/datasources
    
    # Build all services
    log "INFO" "Building Docker images..."
    if docker-compose -f docker-compose.local.yml build --no-cache; then
        log "SUCCESS" "All services built successfully"
    else
        log "ERROR" "Service build failed"
        exit 1
    fi
}

start_infrastructure() {
    log "HEADER" "🛠️  STARTING INFRASTRUCTURE"
    
    # Start infrastructure services first (databases, etc.)
    log "INFO" "Starting Weaviate vector database..."
    docker-compose -f docker-compose.local.yml up -d weaviate
    
    log "INFO" "Starting PostgreSQL database..."
    docker-compose -f docker-compose.local.yml up -d postgres
    
    log "INFO" "Starting Redis cache..."
    docker-compose -f docker-compose.local.yml up -d redis
    
    # Wait for services to be healthy
    log "INFO" "Waiting for infrastructure services to be ready..."
    sleep 30
    
    # Check health
    if docker-compose -f docker-compose.local.yml ps | grep -q "unhealthy"; then
        log "WARNING" "Some infrastructure services may not be fully ready"
        docker-compose -f docker-compose.local.yml ps
    else
        log "SUCCESS" "Infrastructure services are running"
    fi
}

start_application_services() {
    log "HEADER" "🚀 STARTING APPLICATION SERVICES"
    
    # Start application services
    log "INFO" "Starting unified API server..."
    docker-compose -f docker-compose.local.yml up -d unified-api
    
    log "INFO" "Starting MCP server..."
    docker-compose -f docker-compose.local.yml up -d mcp-server
    
    log "INFO" "Starting vector store service..."
    docker-compose -f docker-compose.local.yml up -d vector-store
    
    log "INFO" "Starting Agno bridge..."
    docker-compose -f docker-compose.local.yml up -d agno-bridge
    
    # Wait for application services
    log "INFO" "Waiting for application services to be ready..."
    sleep 45
    
    log "SUCCESS" "Application services are running"
}

start_monitoring() {
    log "INFO" "Starting monitoring services..."
    docker-compose -f docker-compose.local.yml up -d prometheus grafana || {
        log "WARNING" "Monitoring services failed to start (optional)"
    }
}

health_check() {
    log "HEADER" "🩺 HEALTH CHECK"
    
    # Define service endpoints
    declare -A endpoints=(
        ["Weaviate"]="http://localhost:8080/v1/.well-known/ready"
        ["PostgreSQL"]="postgresql://sophia:sophia_secure_password_2024@localhost:5432/sophia"
        ["Redis"]="redis://localhost:6379"
        ["Unified API"]="http://localhost:8003/healthz"
        ["MCP Server"]="http://localhost:8004/health"
        ["Vector Store"]="http://localhost:8005/health"
        ["Agno Bridge"]="http://localhost:7777/healthz"
    )
    
    local failed_services=()
    
    for service in "${!endpoints[@]}"; do
        endpoint="${endpoints[$service]}"
        log "INFO" "Checking $service..."
        
        if [[ "$endpoint" == http* ]]; then
            if curl -f -s "$endpoint" >/dev/null 2>&1; then
                log "SUCCESS" "✅ $service is healthy"
            else
                log "ERROR" "❌ $service health check failed"
                failed_services+=("$service")
            fi
        elif [[ "$endpoint" == postgresql* ]]; then
            if docker exec sophia-postgres-local pg_isready -U sophia -d sophia >/dev/null 2>&1; then
                log "SUCCESS" "✅ $service is healthy"
            else
                log "ERROR" "❌ $service health check failed"
                failed_services+=("$service")
            fi
        elif [[ "$endpoint" == redis* ]]; then
            if docker exec sophia-redis-local redis-cli -a sophia_redis_2024 ping >/dev/null 2>&1; then
                log "SUCCESS" "✅ $service is healthy"
            else
                log "ERROR" "❌ $service health check failed"  
                failed_services+=("$service")
            fi
        fi
    done
    
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        log "SUCCESS" "🎉 All services are healthy!"
        return 0
    else
        log "ERROR" "❌ Failed services: ${failed_services[*]}"
        return 1
    fi
}

show_status() {
    log "HEADER" "📊 DEPLOYMENT STATUS"
    
    echo -e "${CYAN}Service Status:${NC}"
    docker-compose -f docker-compose.local.yml ps
    
    echo -e "\n${CYAN}Access URLs:${NC}"
    echo "🌐 Unified API:      http://localhost:8003"
    echo "🌐 Agno Bridge:      http://localhost:7777"
    echo "🌐 MCP Server:       http://localhost:8004"
    echo "🌐 Vector Store:     http://localhost:8005"
    echo "🗄️  Weaviate:        http://localhost:8080"
    echo "📊 Prometheus:       http://localhost:9090"
    echo "📈 Grafana:          http://localhost:3001"
    
    echo -e "\n${CYAN}Health Endpoints:${NC}"
    echo "• GET http://localhost:8003/healthz - Unified API health"
    echo "• GET http://localhost:7777/healthz - Agno Bridge health"  
    echo "• GET http://localhost:8004/health - MCP Server health"
    echo "• GET http://localhost:8005/health - Vector Store health"
    echo "• GET http://localhost:8080/v1/.well-known/ready - Weaviate health"
    
    echo -e "\n${CYAN}Next Steps:${NC}"
    echo "1. Test API endpoints with: curl http://localhost:8003/healthz"
    echo "2. View logs with: docker-compose -f docker-compose.local.yml logs -f"
    echo "3. Stop services with: docker-compose -f docker-compose.local.yml down"
    echo "4. View service status: docker-compose -f docker-compose.local.yml ps"
}

show_logs() {
    echo -e "\n${YELLOW}📋 Recent logs (last 50 lines):${NC}"
    docker-compose -f docker-compose.local.yml logs --tail=50
}

main() {
    # Clear log file
    > "$LOG_FILE"
    
    show_banner
    
    log "HEADER" "🔧 PRE-DEPLOYMENT CHECKS"
    check_dependencies
    validate_configuration
    
    log "HEADER" "🧹 CLEANUP"
    cleanup_previous
    
    log "HEADER" "🏗️  BUILD & DEPLOY"
    build_services
    start_infrastructure
    start_application_services
    start_monitoring
    
    log "HEADER" "🩺 HEALTH VERIFICATION"
    if health_check; then
        log "SUCCESS" "🎉 SOPHIA INTEL AI DEPLOYED SUCCESSFULLY!"
        show_status
    else
        log "ERROR" "❌ Deployment completed with issues"
        show_logs
        exit 1
    fi
    
    log "INFO" "📋 Full deployment log saved to: $LOG_FILE"
}

# Handle script termination
trap 'log "WARNING" "🛑 Deployment interrupted by user"; exit 130' INT TERM

# Parse command line arguments
case "${1:-start}" in
    "start")
        main
        ;;
    "stop")
        log "INFO" "Stopping all services..."
        docker-compose -f docker-compose.local.yml down
        log "SUCCESS" "All services stopped"
        ;;
    "restart")
        log "INFO" "Restarting all services..."
        docker-compose -f docker-compose.local.yml restart
        health_check
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose -f docker-compose.local.yml logs -f
        ;;
    "health")
        health_check
        ;;
    "validate")
        validate_apis
        ;;
    "clean")
        log "INFO" "Cleaning up everything..."
        docker-compose -f docker-compose.local.yml down --volumes --remove-orphans
        docker system prune -f
        log "SUCCESS" "Cleanup completed"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|health|validate|clean}"
        echo ""
        echo "  start     - Deploy all services (default)"
        echo "  stop      - Stop all services"
        echo "  restart   - Restart all services"
        echo "  status    - Show service status and URLs"
        echo "  logs      - Follow service logs"
        echo "  health    - Run health checks"
        echo "  validate  - Validate API connections"
        echo "  clean     - Clean up all containers and volumes"
        exit 1
        ;;
esac