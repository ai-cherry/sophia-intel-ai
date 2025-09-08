#!/bin/bash

# Redis Startup Script for Sophia Intel AI Platform
# Starts Redis with optimized configuration

set -euo pipefail

# Configuration
REDIS_CONF="/Users/lynnmusil/sophia-intel-ai/config/redis.conf"
REDIS_BINARY="/opt/homebrew/bin/redis-server"
REDIS_CLI="/opt/homebrew/bin/redis-cli"
REDIS_PID_FILE="/opt/homebrew/var/run/redis.pid"
REDIS_LOG_FILE="/opt/homebrew/var/log/redis/sophia-intel-ai.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Check if Redis is already running
check_redis_running() {
    if [ -f "$REDIS_PID_FILE" ]; then
        local pid=$(cat "$REDIS_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0  # Running
        else
            warn "PID file exists but process is not running, cleaning up"
            rm -f "$REDIS_PID_FILE"
            return 1  # Not running
        fi
    fi
    return 1  # Not running
}

# Stop existing Redis processes
stop_existing_redis() {
    log "Checking for existing Redis processes..."

    # Stop via PID file if it exists
    if [ -f "$REDIS_PID_FILE" ]; then
        local pid=$(cat "$REDIS_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "Stopping Redis process (PID: $pid)..."
            kill "$pid" || true
            sleep 2
        fi
        rm -f "$REDIS_PID_FILE"
    fi

    # Stop any other Redis processes on port 6379
    local redis_pids=$(ps aux | grep '[r]edis-server.*:6379' | awk '{print $2}' || true)
    if [ -n "$redis_pids" ]; then
        log "Stopping additional Redis processes: $redis_pids"
        echo "$redis_pids" | xargs kill -TERM || true
        sleep 2

        # Force kill if still running
        redis_pids=$(ps aux | grep '[r]edis-server.*:6379' | awk '{print $2}' || true)
        if [ -n "$redis_pids" ]; then
            warn "Force killing Redis processes: $redis_pids"
            echo "$redis_pids" | xargs kill -KILL || true
        fi
    fi
}

# Create necessary directories
setup_directories() {
    log "Setting up Redis directories..."

    local redis_dir="/opt/homebrew/var/db/redis"
    local log_dir="/opt/homebrew/var/log/redis"

    mkdir -p "$redis_dir" || error "Failed to create Redis data directory: $redis_dir"
    mkdir -p "$log_dir" || error "Failed to create Redis log directory: $log_dir"

    # Set permissions
    chmod 755 "$redis_dir" "$log_dir"

    success "Redis directories created successfully"
}

# Validate configuration
validate_config() {
    log "Validating Redis configuration..."

    if [ ! -f "$REDIS_CONF" ]; then
        error "Redis configuration file not found: $REDIS_CONF"
    fi

    if [ ! -f "$REDIS_BINARY" ]; then
        error "Redis binary not found: $REDIS_BINARY"
    fi

    # Test configuration syntax
    "$REDIS_BINARY" --test-memory 32 --config "$REDIS_CONF" || error "Redis configuration validation failed"

    success "Redis configuration is valid"
}

# Start Redis server
start_redis() {
    log "Starting Redis server with optimized configuration..."

    # Create log file if it doesn't exist
    touch "$REDIS_LOG_FILE"

    # Start Redis with our configuration
    "$REDIS_BINARY" "$REDIS_CONF" \
        --daemonize yes \
        --pidfile "$REDIS_PID_FILE" \
        --logfile "$REDIS_LOG_FILE" \
        --dir "/opt/homebrew/var/db/redis" || error "Failed to start Redis server"

    # Wait for Redis to start
    local attempts=0
    local max_attempts=30

    while [ $attempts -lt $max_attempts ]; do
        if "$REDIS_CLI" ping > /dev/null 2>&1; then
            break
        fi
        sleep 1
        attempts=$((attempts + 1))
    done

    if [ $attempts -ge $max_attempts ]; then
        error "Redis failed to start within 30 seconds"
    fi

    success "Redis server started successfully"
}

# Verify Redis health
verify_health() {
    log "Verifying Redis health..."

    # Basic connectivity test
    "$REDIS_CLI" ping > /dev/null || error "Redis ping test failed"

    # Get Redis info
    local redis_info=$("$REDIS_CLI" info server)
    local redis_version=$(echo "$redis_info" | grep "redis_version:" | cut -d: -f2 | tr -d '\r')
    local redis_mode=$(echo "$redis_info" | grep "redis_mode:" | cut -d: -f2 | tr -d '\r')

    # Check memory configuration
    local maxmemory=$("$REDIS_CLI" config get maxmemory | tail -n1)
    local policy=$("$REDIS_CLI" config get maxmemory-policy | tail -n1)

    log "Redis Version: $redis_version"
    log "Redis Mode: $redis_mode"
    log "Max Memory: $maxmemory"
    log "Eviction Policy: $policy"

    # Test basic operations
    "$REDIS_CLI" set test:startup "$(date)" > /dev/null || error "Redis SET operation failed"
    local test_value=$("$REDIS_CLI" get test:startup)
    "$REDIS_CLI" del test:startup > /dev/null

    if [ -z "$test_value" ]; then
        error "Redis GET operation failed"
    fi

    success "Redis health verification completed successfully"
}

# Configure Redis for Sophia Intel AI
configure_sophia_optimizations() {
    log "Applying Sophia Intel AI specific optimizations..."

    # Enable keyspace notifications for cache invalidation
    "$REDIS_CLI" config set notify-keyspace-events "Ex" > /dev/null

    # Set memory policy optimizations
    "$REDIS_CLI" config set maxmemory-samples 10 > /dev/null

    # Enable lazy freeing for better performance
    "$REDIS_CLI" config set lazyfree-lazy-eviction yes > /dev/null
    "$REDIS_CLI" config set lazyfree-lazy-expire yes > /dev/null
    "$REDIS_CLI" config set lazyfree-lazy-server-del yes > /dev/null
    "$REDIS_CLI" config set lazyfree-lazy-user-del yes > /dev/null

    # Save current configuration
    "$REDIS_CLI" config rewrite > /dev/null || warn "Failed to save Redis configuration changes"

    success "Sophia Intel AI optimizations applied"
}

# Display status
show_status() {
    log "Redis Status Summary:"
    echo "-----------------------------------"

    if check_redis_running; then
        local pid=$(cat "$REDIS_PID_FILE")
        success "✓ Redis is running (PID: $pid)"
        success "✓ Configuration: $REDIS_CONF"
        success "✓ Log file: $REDIS_LOG_FILE"
        success "✓ Data directory: /opt/homebrew/var/db/redis"

        # Show memory usage
        local memory_info=$("$REDIS_CLI" info memory | grep "used_memory_human\|maxmemory_human")
        echo "$memory_info"

        # Show client connections
        local clients=$("$REDIS_CLI" info clients | grep "connected_clients")
        echo "$clients"

    else
        error "✗ Redis is not running"
    fi

    echo "-----------------------------------"
}

# Main execution
main() {
    log "Starting Redis with Sophia Intel AI optimized configuration..."

    # Check if already running
    if check_redis_running; then
        warn "Redis is already running"
        show_status
        exit 0
    fi

    # Setup
    setup_directories
    validate_config
    stop_existing_redis

    # Start Redis
    start_redis
    verify_health
    configure_sophia_optimizations

    # Show final status
    show_status

    success "Redis startup completed successfully!"
    log "You can monitor Redis with: tail -f $REDIS_LOG_FILE"
    log "Connect to Redis with: $REDIS_CLI"
}

# Handle script arguments
case "${1:-start}" in
    start)
        main
        ;;
    stop)
        log "Stopping Redis..."
        stop_existing_redis
        success "Redis stopped"
        ;;
    restart)
        log "Restarting Redis..."
        stop_existing_redis
        sleep 2
        main
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        echo "  start   - Start Redis with optimized configuration (default)"
        echo "  stop    - Stop Redis server"
        echo "  restart - Restart Redis server"
        echo "  status  - Show Redis status"
        exit 1
        ;;
esac
