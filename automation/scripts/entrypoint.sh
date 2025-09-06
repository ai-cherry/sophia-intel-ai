#!/bin/bash
# ==============================================
# SOPHIA INTEL AI - DOCKER ENTRYPOINT
# Handles initialization, health checks, and graceful shutdown
# ==============================================

set -euo pipefail

# Configuration
SERVICE_NAME=${SOPHIA_SERVICE_NAME:-"sophia-service"}
LOG_LEVEL=${LOG_LEVEL:-"INFO"}
SOPHIA_ENVIRONMENT=${SOPHIA_ENVIRONMENT:-"development"}

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[${timestamp}] [${SERVICE_NAME}] ${level}: ${message}"
}

# Wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-60}
    
    log "INFO" "Waiting for $service_name at $host:$port"
    
    local counter=0
    while ! nc -z "$host" "$port" 2>/dev/null; do
        if [ $counter -gt $timeout ]; then
            log "ERROR" "Timeout waiting for $service_name"
            return 1
        fi
        
        log "DEBUG" "Waiting for $service_name... ($counter/$timeout)"
        sleep 1
        counter=$((counter + 1))
    done
    
    log "SUCCESS" "$service_name is ready"
    return 0
}

# Wait for database services
wait_for_dependencies() {
    log "INFO" "Waiting for dependent services"
    
    # Wait for Redis if configured
    if [[ -n "${REDIS_URL:-}" ]]; then
        local redis_host=$(echo "$REDIS_URL" | sed -n 's|redis://\([^:]*\):\([0-9]*\).*|\1|p')
        local redis_port=$(echo "$REDIS_URL" | sed -n 's|redis://\([^:]*\):\([0-9]*\).*|\2|p')
        wait_for_service "${redis_host:-redis}" "${redis_port:-6379}" "Redis"
    fi
    
    # Wait for PostgreSQL if configured
    if [[ -n "${POSTGRES_URL:-}" ]]; then
        local pg_host=$(echo "$POSTGRES_URL" | sed -n 's|postgresql://[^@]*@\([^:]*\):\([0-9]*\)/.*|\1|p')
        local pg_port=$(echo "$POSTGRES_URL" | sed -n 's|postgresql://[^@]*@\([^:]*\):\([0-9]*\)/.*|\2|p')
        wait_for_service "${pg_host:-postgres}" "${pg_port:-5432}" "PostgreSQL"
    fi
    
    # Wait for Weaviate if configured
    if [[ -n "${WEAVIATE_URL:-}" ]]; then
        local weaviate_host=$(echo "$WEAVIATE_URL" | sed -n 's|http://\([^:]*\):\([0-9]*\).*|\1|p')
        local weaviate_port=$(echo "$WEAVIATE_URL" | sed -n 's|http://\([^:]*\):\([0-9]*\).*|\2|p')
        wait_for_service "${weaviate_host:-weaviate}" "${weaviate_port:-8080}" "Weaviate"
    fi
    
    log "SUCCESS" "All dependencies are ready"
}

# Initialize service
initialize_service() {
    log "INFO" "Initializing $SERVICE_NAME"
    
    # Create necessary directories
    mkdir -p /app/logs
    mkdir -p /app/data
    
    # Set appropriate permissions
    chown -R sophia:sophia /app/logs /app/data 2>/dev/null || true
    
    # Run any initialization scripts
    if [[ -f "/app/automation/scripts/init-service.py" ]]; then
        log "INFO" "Running service initialization script"
        python /app/automation/scripts/init-service.py
    fi
    
    log "SUCCESS" "$SERVICE_NAME initialized"
}

# Run database migrations
run_migrations() {
    if [[ "$SOPHIA_ENVIRONMENT" != "development" ]] && [[ -f "/app/migrations/run_migrations.py" ]]; then
        log "INFO" "Running database migrations"
        python /app/migrations/run_migrations.py
        log "SUCCESS" "Database migrations completed"
    fi
}

# Signal handlers for graceful shutdown
shutdown_handler() {
    local signal=$1
    log "INFO" "Received $signal signal, initiating graceful shutdown"
    
    # Kill child processes
    jobs -p | xargs -r kill -TERM
    
    # Wait for processes to exit
    wait
    
    log "INFO" "$SERVICE_NAME shutdown complete"
    exit 0
}

# Set up signal handlers
trap 'shutdown_handler SIGTERM' SIGTERM
trap 'shutdown_handler SIGINT' SIGINT

# Health check endpoint setup
setup_health_checks() {
    if [[ "$SERVICE_NAME" == *"api"* ]]; then
        log "INFO" "Setting up health check endpoints"
        # Health checks are handled by the application itself
    fi
}

# Main execution
main() {
    log "INFO" "Starting $SERVICE_NAME in $SOPHIA_ENVIRONMENT environment"
    
    # Wait for dependencies
    wait_for_dependencies
    
    # Initialize service
    initialize_service
    
    # Run migrations if needed
    run_migrations
    
    # Setup health checks
    setup_health_checks
    
    log "INFO" "Starting main application: $*"
    
    # Execute the main command
    exec "$@" &
    local app_pid=$!
    
    # Wait for the application to finish
    wait $app_pid
}

# Parse command line arguments for specific actions
case "${1:-start}" in
    "health-check")
        python /app/health-check.py --service="$SERVICE_NAME" --port="${2:-8000}"
        ;;
    "init-only")
        initialize_service
        log "INFO" "Initialization complete, exiting"
        ;;
    *)
        main "$@"
        ;;
esac