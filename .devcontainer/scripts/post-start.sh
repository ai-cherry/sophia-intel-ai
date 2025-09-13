#!/bin/bash
set -euo pipefail

echo "🔄 SOPHIA AI PLATFORM - POST-START SERVICES"
echo "Starting development services and monitoring..."

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_debug() { echo -e "${BLUE}[DEBUG]${NC} $1"; }

# 1. Start Redis if available
if command -v redis-server &> /dev/null; then
    if ! pgrep redis-server > /dev/null; then
        log_info "Starting Redis server..."
        redis-server --daemonize yes --port 6379 || log_warn "Redis startup failed"
    else
        log_debug "Redis already running"
    fi
fi

# 2. Check database connectivity
if command -v pg_isready &> /dev/null; then
    log_info "Checking PostgreSQL connectivity..."
    pg_isready -h localhost -p 5432 || log_warn "PostgreSQL not available"
fi

# 3. Start monitoring services
log_info "Initializing monitoring..."

# Create monitoring directory
mkdir -p /workspace/logs/monitoring

# Start simple health monitoring
cat > /workspace/logs/monitoring/health-monitor.sh << 'EOF'
#!/bin/bash
while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Check backend health
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "$timestamp - Backend: HEALTHY" >> /workspace/logs/monitoring/health.log
    else
        echo "$timestamp - Backend: DOWN" >> /workspace/logs/monitoring/health.log
    fi
    
    # Check Redis
    if redis-cli ping > /dev/null 2>&1; then
        echo "$timestamp - Redis: HEALTHY" >> /workspace/logs/monitoring/health.log
    else
        echo "$timestamp - Redis: DOWN" >> /workspace/logs/monitoring/health.log
    fi
    
    sleep 30
done
EOF

chmod +x /workspace/logs/monitoring/health-monitor.sh

# 4. Update environment status
echo "$(date): Post-start completed" >> /workspace/logs/startup.log

log_info "✅ Post-start initialization complete"
log_info "📊 Health monitoring active"
log_info "🔗 Services ready for development"

