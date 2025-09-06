#!/bin/bash
# ==============================================
# SOPHIA INTEL AI - UNIVERSAL STARTUP MANAGER
# Cross-platform automation for development and production
# ==============================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CONFIG_DIR="${PROJECT_ROOT}/automation/config"
LOGS_DIR="${PROJECT_ROOT}/logs"

# Default values
MODE="development"
ENVIRONMENT="local" 
AUTO_RECOVERY="true"
ACTION="start"
VERBOSE="false"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_file="${LOGS_DIR}/startup-manager.log"
    
    # Ensure logs directory exists
    mkdir -p "${LOGS_DIR}"
    
    case $level in
        "INFO")  echo -e "${BLUE}[${timestamp}] INFO: ${message}${NC}" | tee -a "$log_file" ;;
        "SUCCESS") echo -e "${GREEN}[${timestamp}] SUCCESS: ${message}${NC}" | tee -a "$log_file" ;;
        "WARNING") echo -e "${YELLOW}[${timestamp}] WARNING: ${message}${NC}" | tee -a "$log_file" ;;
        "ERROR")   echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" | tee -a "$log_file" ;;
        "DEBUG")   [[ "$VERBOSE" == "true" ]] && echo -e "${PURPLE}[${timestamp}] DEBUG: ${message}${NC}" | tee -a "$log_file" ;;
    esac
}

# Platform detection
detect_platform() {
    case "$(uname -s)" in
        "Darwin") echo "macos" ;;
        "Linux") echo "linux" ;;
        "MINGW"*|"CYGWIN"*|"MSYS"*) echo "windows" ;;
        *) echo "unknown" ;;
    esac
}

# Environment detection
detect_environment() {
    if [[ -n "${KUBERNETES_SERVICE_HOST:-}" ]]; then
        echo "kubernetes"
    elif [[ -n "${DOCKER_HOST:-}" ]] || [[ -f "/.dockerenv" ]]; then
        echo "docker"
    elif [[ "$USER" == "root" ]] && [[ -d "/opt" ]]; then
        echo "production"
    else
        echo "development"
    fi
}

# Configuration loader
load_config() {
    local config_file="${CONFIG_DIR}/startup-${ENVIRONMENT}.yaml"
    
    if [[ -f "$config_file" ]]; then
        log "INFO" "Loading configuration from $config_file"
        # Simple YAML parsing for shell (basic key: value pairs)
        while IFS=': ' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] || [[ -z "$key" ]] && continue
            # Remove quotes from values
            value=$(echo "$value" | tr -d '"'"'"'')
            # Export as environment variable
            export "SOPHIA_$(echo "$key" | tr '[:lower:]' '[:upper:]')"="$value"
            log "DEBUG" "Set SOPHIA_$(echo "$key" | tr '[:lower:]' '[:upper:]')=$value"
        done < "$config_file"
    else
        log "WARNING" "Configuration file $config_file not found, using defaults"
    fi
}

# Health check function
health_check() {
    local service=$1
    local endpoint=$2
    local timeout=${3:-10}
    
    log "DEBUG" "Checking health of $service at $endpoint"
    
    if [[ "$endpoint" == http* ]]; then
        if timeout "$timeout" curl -sf "$endpoint" >/dev/null 2>&1; then
            log "SUCCESS" "$service is healthy"
            return 0
        else
            log "ERROR" "$service health check failed"
            return 1
        fi
    elif [[ "$endpoint" == tcp* ]]; then
        # TCP health check
        local host_port=${endpoint#tcp://}
        local host=${host_port%:*}
        local port=${host_port#*:}
        
        if timeout "$timeout" bash -c "</dev/tcp/${host}/${port}" 2>/dev/null; then
            log "SUCCESS" "$service is healthy (TCP)"
            return 0
        else
            log "ERROR" "$service TCP health check failed"
            return 1
        fi
    fi
    
    return 1
}

# Dependency checker
check_dependencies() {
    log "INFO" "Checking system dependencies for $MODE mode"
    
    local required_commands=()
    local missing_commands=()
    
    case "$MODE" in
        "development")
            required_commands=("docker" "docker-compose" "python3" "curl")
            ;;
        "production")
            required_commands=("docker" "python3" "curl" "systemctl")
            ;;
        "kubernetes")
            required_commands=("kubectl" "curl")
            ;;
    esac
    
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_commands+=("$cmd")
            log "ERROR" "Missing required command: $cmd"
        else
            log "DEBUG" "Found required command: $cmd"
        fi
    done
    
    if [[ ${#missing_commands[@]} -gt 0 ]]; then
        log "ERROR" "Missing dependencies: ${missing_commands[*]}"
        return 1
    fi
    
    log "SUCCESS" "All dependencies are available"
    return 0
}

# Docker Compose management
manage_docker_compose() {
    local action=$1
    local compose_file
    
    case "$ENVIRONMENT" in
        "local"|"development")
            compose_file="docker-compose.yml"
            ;;
        "staging")
            compose_file="docker-compose.staging.yml"
            ;;
        "production")
            compose_file="docker-compose.production.yml"
            ;;
        *)
            compose_file="docker-compose.yml"
            ;;
    esac
    
    local full_compose_path="${PROJECT_ROOT}/${compose_file}"
    
    if [[ ! -f "$full_compose_path" ]]; then
        log "ERROR" "Docker Compose file not found: $full_compose_path"
        return 1
    fi
    
    cd "$PROJECT_ROOT"
    
    case "$action" in
        "start")
            log "INFO" "Starting services with $compose_file"
            docker-compose -f "$compose_file" up -d --remove-orphans
            
            # Wait for services to be ready
            log "INFO" "Waiting for services to be ready..."
            sleep 30
            
            # Health check critical services
            local services=("redis:redis://localhost:6380" "weaviate:http://localhost:8081/v1/.well-known/ready")
            for service_endpoint in "${services[@]}"; do
                local service_name=${service_endpoint%:*}
                local endpoint=${service_endpoint#*:}
                health_check "$service_name" "$endpoint"
            done
            ;;
        "stop")
            log "INFO" "Stopping services with $compose_file"
            docker-compose -f "$compose_file" down
            ;;
        "restart")
            log "INFO" "Restarting services with $compose_file"
            docker-compose -f "$compose_file" restart
            ;;
        "status")
            docker-compose -f "$compose_file" ps
            ;;
    esac
}

# Kubernetes management
manage_kubernetes() {
    local action=$1
    local namespace="${SOPHIA_NAMESPACE:-sophia-intel-ai}"
    
    case "$action" in
        "start")
            log "INFO" "Deploying to Kubernetes namespace: $namespace"
            kubectl apply -k "${PROJECT_ROOT}/k8s/overlays/${ENVIRONMENT}"
            
            # Wait for deployments
            log "INFO" "Waiting for deployments to be ready..."
            kubectl wait --for=condition=available --timeout=300s deployment --all -n "$namespace"
            ;;
        "stop")
            log "INFO" "Stopping Kubernetes deployment in namespace: $namespace"
            kubectl delete -k "${PROJECT_ROOT}/k8s/overlays/${ENVIRONMENT}"
            ;;
        "status")
            kubectl get all -n "$namespace"
            ;;
    esac
}

# Recovery mechanism
auto_recovery() {
    if [[ "$AUTO_RECOVERY" != "true" ]]; then
        return 0
    fi
    
    log "INFO" "Starting auto-recovery monitoring"
    
    while true; do
        sleep 60  # Check every minute
        
        case "$MODE" in
            "development")
                # Check if Docker containers are running
                if ! docker-compose -f "${PROJECT_ROOT}/docker-compose.yml" ps -q | grep -q .; then
                    log "WARNING" "Services appear to be down, attempting recovery"
                    manage_docker_compose "start"
                fi
                ;;
            "kubernetes")
                # Check if pods are running
                local failed_pods=$(kubectl get pods -n "${SOPHIA_NAMESPACE:-sophia-intel-ai}" --field-selector=status.phase!=Running -o name | wc -l)
                if [[ "$failed_pods" -gt 0 ]]; then
                    log "WARNING" "Found $failed_pods failed pods, attempting recovery"
                    manage_kubernetes "start"
                fi
                ;;
        esac
    done
}

# Main startup function
start_services() {
    log "INFO" "Starting Sophia Intel AI in $MODE mode (environment: $ENVIRONMENT)"
    
    # Load configuration
    load_config
    
    # Check dependencies
    if ! check_dependencies; then
        log "ERROR" "Dependency check failed"
        return 1
    fi
    
    # Start services based on mode
    case "$MODE" in
        "development")
            manage_docker_compose "start"
            ;;
        "kubernetes")
            manage_kubernetes "start"
            ;;
        "production")
            # Production mode could use either Docker Compose or Kubernetes
            if [[ "$ENVIRONMENT" == "kubernetes" ]]; then
                manage_kubernetes "start"
            else
                manage_docker_compose "start"
            fi
            ;;
    esac
    
    log "SUCCESS" "Sophia Intel AI started successfully"
    
    # Start auto-recovery in background if enabled
    if [[ "$AUTO_RECOVERY" == "true" ]]; then
        auto_recovery &
        local recovery_pid=$!
        echo "$recovery_pid" > "${LOGS_DIR}/recovery.pid"
        log "INFO" "Auto-recovery monitoring started (PID: $recovery_pid)"
    fi
}

# Stop services
stop_services() {
    log "INFO" "Stopping Sophia Intel AI services"
    
    # Stop auto-recovery if running
    if [[ -f "${LOGS_DIR}/recovery.pid" ]]; then
        local recovery_pid=$(cat "${LOGS_DIR}/recovery.pid")
        if kill -0 "$recovery_pid" 2>/dev/null; then
            log "INFO" "Stopping auto-recovery (PID: $recovery_pid)"
            kill "$recovery_pid"
            rm -f "${LOGS_DIR}/recovery.pid"
        fi
    fi
    
    # Stop services
    case "$MODE" in
        "development")
            manage_docker_compose "stop"
            ;;
        "kubernetes")
            manage_kubernetes "stop"
            ;;
        "production")
            if [[ "$ENVIRONMENT" == "kubernetes" ]]; then
                manage_kubernetes "stop"
            else
                manage_docker_compose "stop"
            fi
            ;;
    esac
    
    log "SUCCESS" "Sophia Intel AI stopped successfully"
}

# Status check
check_status() {
    log "INFO" "Checking Sophia Intel AI status"
    
    case "$MODE" in
        "development")
            manage_docker_compose "status"
            ;;
        "kubernetes")
            manage_kubernetes "status"
            ;;
    esac
}

# Signal handlers
handle_signal() {
    local signal=$1
    log "INFO" "Received signal: $signal"
    
    case "$signal" in
        "TERM"|"INT")
            stop_services
            exit 0
            ;;
        "HUP")
            log "INFO" "Reloading configuration"
            load_config
            ;;
    esac
}

# Set up signal handlers
trap 'handle_signal TERM' TERM
trap 'handle_signal INT' INT
trap 'handle_signal HUP' HUP

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode=*)
            MODE="${1#*=}"
            shift
            ;;
        --environment=*)
            ENVIRONMENT="${1#*=}"
            shift
            ;;
        --auto-recovery=*)
            AUTO_RECOVERY="${1#*=}"
            shift
            ;;
        --action=*)
            ACTION="${1#*=}"
            shift
            ;;
        --verbose)
            VERBOSE="true"
            shift
            ;;
        --help|-h)
            echo "Sophia Intel AI Startup Manager"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode=MODE           Set deployment mode (development|production|kubernetes)"
            echo "  --environment=ENV     Set environment (local|staging|production)"
            echo "  --auto-recovery=BOOL  Enable auto-recovery (true|false)"
            echo "  --action=ACTION       Action to perform (start|stop|status|restart)"
            echo "  --verbose             Enable verbose logging"
            echo "  --help, -h            Show this help message"
            exit 0
            ;;
        *)
            log "ERROR" "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Auto-detect if not specified
if [[ "$MODE" == "auto" ]]; then
    MODE=$(detect_environment)
    log "INFO" "Auto-detected mode: $MODE"
fi

PLATFORM=$(detect_platform)
log "INFO" "Platform: $PLATFORM, Mode: $MODE, Environment: $ENVIRONMENT"

# Main execution
case "$ACTION" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 5
        start_services
        ;;
    "status")
        check_status
        ;;
    *)
        log "ERROR" "Unknown action: $ACTION"
        exit 1
        ;;
esac