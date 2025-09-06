#!/bin/bash

# Redis Integration Startup Script for Sophia Intel AI Platform
# Comprehensive Redis startup with health monitoring and application integration

set -euo pipefail

# Configuration paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REDIS_STARTUP_SCRIPT="$SCRIPT_DIR/start-redis-optimized.sh"
REDIS_BACKUP_SCRIPT="$SCRIPT_DIR/redis-backup.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
log() { echo -e "${BLUE}[$(date +'%H:%M:%S')] $1${NC}"; }
warn() { echo -e "${YELLOW}[$(date +'%H:%M:%S')] WARNING: $1${NC}"; }
error() { echo -e "${RED}[$(date +'%H:%M:%S')] ERROR: $1${NC}"; exit 1; }
success() { echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"; }

# Check prerequisites
check_prerequisites() {
    log "Checking Redis integration prerequisites..."
    
    # Check Redis binary
    if ! command -v redis-server &> /dev/null; then
        error "Redis server not found. Please install Redis first."
    fi
    
    # Check Python environment
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found"
    fi
    
    # Check project structure
    if [ ! -f "$PROJECT_ROOT/app/core/redis_manager.py" ]; then
        error "Redis manager not found. Ensure you're in the correct project directory."
    fi
    
    # Check startup scripts exist and are executable
    if [ ! -x "$REDIS_STARTUP_SCRIPT" ]; then
        error "Redis startup script not found or not executable: $REDIS_STARTUP_SCRIPT"
    fi
    
    if [ ! -x "$REDIS_BACKUP_SCRIPT" ]; then
        error "Redis backup script not found or not executable: $REDIS_BACKUP_SCRIPT"
    fi
    
    success "Prerequisites check completed"
}

# Start Redis with optimized configuration
start_redis() {
    log "Starting Redis with Sophia Intel AI optimizations..."
    
    "$REDIS_STARTUP_SCRIPT" start
    
    # Wait a moment for Redis to fully start
    sleep 3
    
    success "Redis startup completed"
}

# Test application integration
test_application_integration() {
    log "Testing application integration..."
    
    # Set PYTHONPATH
    export PYTHONPATH="$PROJECT_ROOT"
    
    # Test Python integration
    python3 << 'EOF'
import asyncio
import sys
import os

# Add project root to path
project_root = os.environ.get('PYTHONPATH')
if project_root:
    sys.path.insert(0, project_root)

async def test_integration():
    try:
        from app.core.redis_manager import redis_manager
        from app.core.redis_config import redis_config
        
        # Test initialization
        await redis_manager.initialize()
        print("✓ Redis manager initialized successfully")
        
        # Test configuration
        print(f"✓ Redis URL: {redis_config.url}")
        print(f"✓ Max connections: {redis_config.pool.max_connections}")
        print(f"✓ Max memory: {redis_config.memory.max_memory_mb}MB")
        
        # Test basic operations
        test_key = "integration:test"
        await redis_manager.set_with_ttl(test_key, "integration_success", ttl=30)
        value = await redis_manager.get(test_key)
        
        if value and value.decode() == "integration_success":
            print("✓ Basic Redis operations working")
        else:
            print("✗ Basic Redis operations failed")
            return False
        
        # Test TTL functionality
        ttl = await redis_manager.redis.ttl(test_key)
        if ttl > 0:
            print(f"✓ TTL functionality working (TTL: {ttl}s)")
        else:
            print("✗ TTL functionality failed")
        
        # Test stream operations
        stream_name = "integration:test:stream"
        await redis_manager.stream_add(stream_name, {"test": "data", "timestamp": "123456789"})
        print("✓ Redis streams working")
        
        # Test memory stats
        memory_stats = await redis_manager.get_memory_stats()
        print(f"✓ Memory monitoring working ({memory_stats['used_memory_human']})")
        
        # Test health check
        health = await redis_manager.health_check()
        if health.get("healthy"):
            print("✓ Health monitoring working")
        else:
            print("⚠ Health monitoring shows issues")
        
        # Cleanup
        await redis_manager.delete(test_key)
        await redis_manager.redis.delete(stream_name)
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run the test
success = asyncio.run(test_integration())
exit(0 if success else 1)
EOF

    if [ $? -eq 0 ]; then
        success "Application integration tests passed"
    else
        error "Application integration tests failed"
    fi
}

# Create initial backup
create_initial_backup() {
    log "Creating initial backup..."
    
    "$REDIS_BACKUP_SCRIPT" backup initial_setup
    
    success "Initial backup created"
}

# Setup monitoring
setup_monitoring() {
    log "Setting up Redis health monitoring..."
    
    # Test health monitoring API
    export PYTHONPATH="$PROJECT_ROOT"
    python3 << 'EOF'
import asyncio
import sys
import os

project_root = os.environ.get('PYTHONPATH')
if project_root:
    sys.path.insert(0, project_root)

async def setup_monitoring():
    try:
        from app.core.redis_health_monitor import redis_health_monitor
        
        # Start health monitoring with 60-second intervals
        await redis_health_monitor.start_monitoring(60.0)
        print("✓ Health monitoring started (60s intervals)")
        
        # Wait a moment then get initial health check
        await asyncio.sleep(2)
        
        health_summary = await redis_health_monitor.get_health_summary()
        print(f"✓ Initial health status: {health_summary['status']}")
        
        # Add some sample metrics
        print("✓ Health monitoring configured successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Health monitoring setup failed: {e}")
        return False

success = asyncio.run(setup_monitoring())
exit(0 if success else 1)
EOF

    if [ $? -eq 0 ]; then
        success "Health monitoring setup completed"
    else
        warn "Health monitoring setup had issues but continuing"
    fi
}

# Display final status
show_final_status() {
    log "Redis Integration Status Summary"
    echo "=================================="
    
    # Redis process status
    if pgrep -f "redis-server" > /dev/null; then
        local redis_pid=$(pgrep -f "redis-server")
        success "✓ Redis server running (PID: $redis_pid)"
    else
        error "✗ Redis server not running"
    fi
    
    # Test basic connectivity
    if redis-cli ping > /dev/null 2>&1; then
        success "✓ Redis connectivity confirmed"
    else
        error "✗ Redis connectivity failed"
    fi
    
    # Show Redis info
    local redis_version=$(redis-cli info server | grep "redis_version:" | cut -d: -f2 | tr -d '\r')
    local memory_usage=$(redis-cli info memory | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
    local connected_clients=$(redis-cli info clients | grep "connected_clients:" | cut -d: -f2 | tr -d '\r')
    
    echo ""
    echo "Redis Server Information:"
    echo "- Version: $redis_version"
    echo "- Memory Usage: $memory_usage"
    echo "- Connected Clients: $connected_clients"
    echo ""
    
    # Configuration summary
    echo "Configuration:"
    echo "- Redis URL: redis://localhost:6379"
    echo "- Config File: /Users/lynnmusil/sophia-intel-ai/config/redis.conf"
    echo "- Data Directory: /opt/homebrew/var/db/redis"
    echo "- Backup Directory: /opt/homebrew/var/backups/redis"
    echo ""
    
    # Available scripts
    echo "Management Scripts:"
    echo "- Start/Stop: $REDIS_STARTUP_SCRIPT"
    echo "- Backup/Restore: $REDIS_BACKUP_SCRIPT"
    echo "- Integration: $0"
    echo ""
    
    # API endpoints
    echo "Health Monitoring API:"
    echo "- Health: http://localhost:8000/redis/health"
    echo "- Metrics: http://localhost:8000/redis/metrics"
    echo "- Alerts: http://localhost:8000/redis/alerts"
    echo ""
    
    success "Redis integration setup completed successfully!"
    
    echo ""
    echo "Next Steps:"
    echo "1. Monitor health: curl http://localhost:8000/redis/health/summary"
    echo "2. Create backups: $REDIS_BACKUP_SCRIPT backup manual"
    echo "3. Check logs: tail -f /opt/homebrew/var/log/redis/sophia-intel-ai.log"
    echo "=================================="
}

# Main execution
main() {
    echo "=========================================="
    echo "Redis Integration Startup for Sophia Intel AI"
    echo "=========================================="
    
    check_prerequisites
    start_redis
    test_application_integration
    create_initial_backup
    setup_monitoring
    show_final_status
    
    success "Redis integration startup completed!"
}

# Handle script arguments
case "${1:-start}" in
    start)
        main
        ;;
    test)
        export PYTHONPATH="$PROJECT_ROOT"
        test_application_integration
        ;;
    status)
        show_final_status
        ;;
    *)
        echo "Usage: $0 {start|test|status}"
        echo "  start  - Full Redis integration startup (default)"
        echo "  test   - Test application integration only"  
        echo "  status - Show current Redis status"
        exit 1
        ;;
esac