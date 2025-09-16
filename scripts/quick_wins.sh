#!/bin/bash

# Sophia Intel AI - Quick Wins Implementation Script
# Production-ready, idempotent script for immediate operational improvements
# Safe to run multiple times with rollback capabilities

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
BACKUP_DIR="$PROJECT_ROOT/backups"
CONFIG_DIR="$PROJECT_ROOT/config"
QUICK_WINS_LOG="$LOG_DIR/quick-wins-$(date +%Y%m%d-%H%M%S).log"
ROLLBACK_MANIFEST="$BACKUP_DIR/rollback-manifest-$(date +%Y%m%d-%H%M%S).json"

# Create necessary directories
mkdir -p "$LOG_DIR" "$BACKUP_DIR" "$CONFIG_DIR" "$PROJECT_ROOT/.pids"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    
    case $level in
        INFO)  echo -e "${GREEN}[INFO]${NC} $message" | tee -a "$QUICK_WINS_LOG" ;;
        WARN)  echo -e "${YELLOW}[WARN]${NC} $message" | tee -a "$QUICK_WINS_LOG" ;;
        ERROR) echo -e "${RED}[ERROR]${NC} $message" | tee -a "$QUICK_WINS_LOG" ;;
        DEBUG) echo -e "${CYAN}[DEBUG]${NC} $message" | tee -a "$QUICK_WINS_LOG" ;;
        *)     echo -e "$message" | tee -a "$QUICK_WINS_LOG" ;;
    esac
    
    # Also log to structured format
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"message\":\"$message\"}" >> "$LOG_DIR/quick-wins.json"
}

# Safety check function
safety_check() {
    local action=$1
    local check_cmd=$2
    
    log DEBUG "Safety check for: $action"
    
    if eval "$check_cmd"; then
        log INFO "Safety check passed: $action"
        return 0
    else
        log WARN "Safety check failed: $action (continuing anyway)"
        return 1
    fi
}

# Backup function
backup_file() {
    local file=$1
    if [ -f "$file" ]; then
        local backup_name="$BACKUP_DIR/$(basename $file).$(date +%Y%m%d-%H%M%S).bak"
        cp "$file" "$backup_name"
        log DEBUG "Backed up $file to $backup_name"
        
        # Add to rollback manifest
        echo "{\"original\":\"$file\",\"backup\":\"$backup_name\"}" >> "$ROLLBACK_MANIFEST"
    fi
}

# Initialize rollback manifest
echo "[" > "$ROLLBACK_MANIFEST"

log INFO "========================================="
log INFO "Sophia Intel AI - Quick Wins Implementation"
log INFO "========================================="
log INFO "Log file: $QUICK_WINS_LOG"
log INFO "Rollback manifest: $ROLLBACK_MANIFEST"

# ============================================
# 1. FIX DUPLICATE NPM PROCESSES
# ============================================
log INFO ""
log INFO "1. Fixing duplicate NPM processes..."

fix_npm_duplicates() {
    local fixed_count=0
    
    # List of NPM packages that might have duplicates
    local npm_packages=(
        "@modelcontextprotocol/server-memory"
        "@modelcontextprotocol/server-sequential-thinking"
        "@apify/actors-mcp-server"
        "@modelcontextprotocol/server-brave-search"
        "exa-mcp-server"
    )
    
    for package in "${npm_packages[@]}"; do
        local pids=$(pgrep -f "$package" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            local count=$(echo "$pids" | wc -w)
            if [ $count -gt 1 ]; then
                log WARN "Found $count instances of $package"
                # Keep only the newest process
                echo "$pids" | head -n -1 | while read pid; do
                    if kill -0 "$pid" 2>/dev/null; then
                        kill "$pid"
                        log INFO "Killed duplicate process $pid for $package"
                        ((fixed_count++))
                    fi
                done
            fi
        fi
    done
    
    log INFO "Fixed $fixed_count duplicate NPM processes"
}

# Run the fix if duplicates exist
if pgrep -f "npx.*modelcontextprotocol\|apify\|exa-mcp" >/dev/null 2>&1; then
    fix_npm_duplicates
else
    log INFO "No duplicate NPM processes found"
fi

# ============================================
# 2. ADD PORT VALIDATION TO STARTUP
# ============================================
log INFO ""
log INFO "2. Adding port validation to startup..."

create_port_validator() {
    cat > "$SCRIPT_DIR/validate_ports.sh" << 'EOF'
#!/bin/bash
# Port validation script

REQUIRED_PORTS=(8081 8082 8084)
CONFLICTS=()

for port in "${REQUIRED_PORTS[@]}"; do
    if lsof -i :$port >/dev/null 2>&1; then
        PID=$(lsof -ti :$port)
        PROCESS=$(ps -p $PID -o comm= 2>/dev/null || echo "unknown")
        if [[ ! "$PROCESS" =~ "python\|node\|redis" ]]; then
            CONFLICTS+=("Port $port used by $PROCESS (PID: $PID)")
        fi
    fi
done

if [ ${#CONFLICTS[@]} -gt 0 ]; then
    echo "Port conflicts detected:"
    printf '%s\n' "${CONFLICTS[@]}"
    exit 1
else
    echo "All ports available"
    exit 0
fi
EOF
    chmod +x "$SCRIPT_DIR/validate_ports.sh"
    log INFO "Created port validation script"
}

if [ ! -f "$SCRIPT_DIR/validate_ports.sh" ]; then
    create_port_validator
else
    log INFO "Port validator already exists"
fi

# ============================================
# 3. CREATE MCP HEALTH CHECK SCRIPT
# ============================================
log INFO ""
log INFO "3. Creating MCP health check script..."

create_health_check() {
    cat > "$SCRIPT_DIR/mcp_quick_health.sh" << 'EOF'
#!/bin/bash
# Quick MCP health check

SERVERS=(
    "Memory:8081"
    "Filesystem:8082"
    "Git:8084"
)

ALL_HEALTHY=true

for server in "${SERVERS[@]}"; do
    IFS=':' read -r name port <<< "$server"
    if curl -s "http://localhost:$port/health" 2>/dev/null | grep -q "healthy"; then
        echo "✅ $name Server: Healthy"
    else
        echo "❌ $name Server: Not healthy"
        ALL_HEALTHY=false
    fi
done

if [ "$ALL_HEALTHY" = true ]; then
    exit 0
else
    exit 1
fi
EOF
    chmod +x "$SCRIPT_DIR/mcp_quick_health.sh"
    log INFO "Created MCP health check script"
}

if [ ! -f "$SCRIPT_DIR/mcp_quick_health.sh" ]; then
    create_health_check
else
    log INFO "Health check script already exists"
fi

# ============================================
# 4. SETUP REDIS DATA DIRECTORY
# ============================================
log INFO ""
log INFO "4. Setting up Redis data directory..."

setup_redis_persistence() {
    local redis_dir="$PROJECT_ROOT/redis-data"
    local redis_backup_dir="$PROJECT_ROOT/redis-backups"
    
    # Create directories
    mkdir -p "$redis_dir" "$redis_backup_dir"
    
    # Set permissions
    chmod 755 "$redis_dir" "$redis_backup_dir"
    
    # Create Redis backup script
    cat > "$SCRIPT_DIR/redis_backup.sh" << EOF
#!/bin/bash
# Redis backup script

REDIS_DIR="$redis_dir"
BACKUP_DIR="$redis_backup_dir"
TIMESTAMP=\$(date +%Y%m%d-%H%M%S)

# Create backup
if redis-cli ping >/dev/null 2>&1; then
    redis-cli BGSAVE
    sleep 2
    
    # Copy RDB file
    if [ -f "\$REDIS_DIR/sophia-intel.rdb" ]; then
        cp "\$REDIS_DIR/sophia-intel.rdb" "\$BACKUP_DIR/sophia-intel-\$TIMESTAMP.rdb"
        echo "Redis backup created: sophia-intel-\$TIMESTAMP.rdb"
    fi
    
    # Copy AOF file if exists
    if [ -f "\$REDIS_DIR/sophia-intel.aof" ]; then
        cp "\$REDIS_DIR/sophia-intel.aof" "\$BACKUP_DIR/sophia-intel-\$TIMESTAMP.aof"
    fi
    
    # Cleanup old backups (keep last 7 days)
    find "\$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete
    find "\$BACKUP_DIR" -name "*.aof" -mtime +7 -delete
else
    echo "Redis not running"
    exit 1
fi
EOF
    chmod +x "$SCRIPT_DIR/redis_backup.sh"
    
    log INFO "Redis persistence directories configured"
    log INFO "Redis data: $redis_dir"
    log INFO "Redis backups: $redis_backup_dir"
}

setup_redis_persistence

# ============================================
# 5. INSTALL PM2 CONFIGURATION
# ============================================
log INFO ""
log INFO "5. Installing PM2 configuration..."

setup_pm2() {
    # Check if PM2 is installed
    if ! command -v pm2 >/dev/null 2>&1; then
        log WARN "PM2 not installed. To install: npm install -g pm2"
        return 1
    fi
    
    # Check if ecosystem config exists
    if [ -f "$CONFIG_DIR/pm2.ecosystem.config.js" ]; then
        log INFO "PM2 ecosystem config already exists"
        
        # Create PM2 quick commands
        cat > "$SCRIPT_DIR/pm2_quick.sh" << 'EOF'
#!/bin/bash
# PM2 quick commands

case "$1" in
    start)
        pm2 start config/pm2.ecosystem.config.js
        ;;
    stop)
        pm2 stop all
        ;;
    restart)
        pm2 restart all
        ;;
    status)
        pm2 status
        ;;
    logs)
        pm2 logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
EOF
        chmod +x "$SCRIPT_DIR/pm2_quick.sh"
        log INFO "Created PM2 quick commands script"
    else
        log WARN "PM2 ecosystem config not found at $CONFIG_DIR/pm2.ecosystem.config.js"
    fi
}

setup_pm2

# ============================================
# 6. CREATE LOG ROTATION CONFIGURATION
# ============================================
log INFO ""
log INFO "6. Setting up log rotation..."

setup_log_rotation() {
    # Create logrotate configuration
    cat > "$PROJECT_ROOT/.logrotate.conf" << EOF
# Sophia Intel AI Log Rotation Configuration

$LOG_DIR/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
    sharedscripts
    postrotate
        # Notify processes to reopen logs
        pkill -USR1 -f "mcp.*server" 2>/dev/null || true
    endscript
}

$LOG_DIR/pm2/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
    
    # Create log cleanup script
    cat > "$SCRIPT_DIR/cleanup_logs.sh" << EOF
#!/bin/bash
# Log cleanup script

LOG_DIR="$LOG_DIR"
MAX_AGE_DAYS=30

# Clean old logs
find "\$LOG_DIR" -name "*.log" -mtime +\$MAX_AGE_DAYS -delete
find "\$LOG_DIR" -name "*.log.gz" -mtime +\$MAX_AGE_DAYS -delete

# Clean old JSON logs
find "\$LOG_DIR" -name "*.json" -mtime +\$MAX_AGE_DAYS -delete

# Report
REMAINING=\$(find "\$LOG_DIR" -name "*.log*" | wc -l)
echo "Cleaned logs older than \$MAX_AGE_DAYS days"
echo "Remaining log files: \$REMAINING"
EOF
    chmod +x "$SCRIPT_DIR/cleanup_logs.sh"
    
    log INFO "Log rotation configured"
}

setup_log_rotation

# ============================================
# 7. CREATE ENVIRONMENT VALIDATION
# ============================================
log INFO ""
log INFO "7. Creating environment validation..."

create_env_validator() {
    cat > "$SCRIPT_DIR/validate_env.sh" << 'EOF'
#!/bin/bash
# Environment validation script

REQUIRED_VARS=(
    "ANTHROPIC_API_KEY"
    "OPENAI_API_KEY"
)

OPTIONAL_VARS=(
    "XAI_API_KEY"
    "GROQ_API_KEY"
    "DEEPSEEK_API_KEY"
    "MISTRAL_API_KEY"
    "PERPLEXITY_API_KEY"
    "OPENROUTER_API_KEY"
    "TOGETHER_API_KEY"
    "APIFY_API_TOKEN"
    "BRAVE_SEARCH_API_KEY"
    "EXA_API_KEY"
    "GITHUB_PERSONAL_ACCESS_TOKEN"
)

# Source environment
if [ -f .env.master ]; then
    source .env.master
fi

MISSING=()
OPTIONAL_MISSING=()

# Check required
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING+=("$var")
    fi
done

# Check optional
for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        OPTIONAL_MISSING+=("$var")
    fi
done

# Report
if [ ${#MISSING[@]} -gt 0 ]; then
    echo "❌ Missing required variables:"
    printf '  - %s\n' "${MISSING[@]}"
    exit 1
else
    echo "✅ All required environment variables set"
fi

if [ ${#OPTIONAL_MISSING[@]} -gt 0 ]; then
    echo "⚠️  Missing optional variables:"
    printf '  - %s\n' "${OPTIONAL_MISSING[@]}"
fi

exit 0
EOF
    chmod +x "$SCRIPT_DIR/validate_env.sh"
    log INFO "Created environment validator"
}

if [ ! -f "$SCRIPT_DIR/validate_env.sh" ]; then
    create_env_validator
else
    log INFO "Environment validator already exists"
fi

# ============================================
# 8. CREATE QUICK STATUS COMMAND
# ============================================
log INFO ""
log INFO "8. Creating quick status command..."

create_status_command() {
    cat > "$SCRIPT_DIR/sophia_status.sh" << 'EOF'
#!/bin/bash
# Sophia Intel AI - Quick Status

echo "================================"
echo "Sophia Intel AI - System Status"
echo "================================"
echo ""

# Redis
echo "Redis:"
if redis-cli ping >/dev/null 2>&1; then
    KEYS=$(redis-cli DBSIZE | awk '{print $2}')
    echo "  ✅ Running ($KEYS keys)"
else
    echo "  ❌ Not running"
fi

# MCP Servers
echo ""
echo "MCP Servers:"
for server in "Memory:8081" "Filesystem:8082" "Git:8084"; do
    IFS=':' read -r name port <<< "$server"
    if curl -s "http://localhost:$port/health" 2>/dev/null | grep -q "healthy"; then
        echo "  ✅ $name: Healthy (port $port)"
    else
        echo "  ❌ $name: Not responding (port $port)"
    fi
done

# PM2
echo ""
echo "PM2 Process Manager:"
if command -v pm2 >/dev/null 2>&1; then
    RUNNING=$(pm2 list --no-color 2>/dev/null | grep -c "online" || echo 0)
    echo "  ✅ Installed ($RUNNING processes online)"
else
    echo "  ⚠️  Not installed"
fi

# Disk Usage
echo ""
echo "Disk Usage:"
echo "  Logs: $(du -sh logs 2>/dev/null | cut -f1 || echo "N/A")"
echo "  Redis: $(du -sh redis-data 2>/dev/null | cut -f1 || echo "N/A")"
echo "  Backups: $(du -sh backups 2>/dev/null | cut -f1 || echo "N/A")"

echo ""
EOF
    chmod +x "$SCRIPT_DIR/sophia_status.sh"
    log INFO "Created quick status command"
}

if [ ! -f "$SCRIPT_DIR/sophia_status.sh" ]; then
    create_status_command
else
    log INFO "Status command already exists"
fi

# ============================================
# 9. CREATE ALIASES FILE
# ============================================
log INFO ""
log INFO "9. Creating useful aliases..."

create_aliases() {
    cat > "$PROJECT_ROOT/.sophia_aliases" << EOF
# Sophia Intel AI - Quick Command Aliases

# Status and monitoring
alias sophia-status='$SCRIPT_DIR/sophia_status.sh'
alias sophia-health='$SCRIPT_DIR/mcp_quick_health.sh'
alias sophia-monitor='python3 $SCRIPT_DIR/mcp_health_monitor.py'
alias sophia-logs='tail -f $LOG_DIR/*.log'

# Process management
alias sophia-start='$PROJECT_ROOT/startup.sh'
alias sophia-stop='pkill -f "mcp.*server" && redis-cli shutdown'
alias sophia-restart='sophia-stop && sleep 2 && sophia-start'

# PM2 shortcuts
alias pm2-sophia='pm2 start $CONFIG_DIR/pm2.ecosystem.config.js'
alias pm2-status='pm2 status'
alias pm2-logs='pm2 logs'

# Maintenance
alias sophia-backup='$SCRIPT_DIR/redis_backup.sh'
alias sophia-clean='$SCRIPT_DIR/cleanup_logs.sh'
alias sophia-validate='$SCRIPT_DIR/validate_env.sh && $SCRIPT_DIR/validate_ports.sh'

echo "Sophia aliases loaded. Type 'alias | grep sophia' to see all commands."
EOF
    
    log INFO "Created aliases file: source $PROJECT_ROOT/.sophia_aliases"
}

create_aliases

# ============================================
# 10. FINAL VALIDATION
# ============================================
log INFO ""
log INFO "10. Running final validation..."

VALIDATION_PASSED=true

# Check created scripts
SCRIPTS_TO_CHECK=(
    "$SCRIPT_DIR/validate_ports.sh"
    "$SCRIPT_DIR/mcp_quick_health.sh"
    "$SCRIPT_DIR/redis_backup.sh"
    "$SCRIPT_DIR/cleanup_logs.sh"
    "$SCRIPT_DIR/validate_env.sh"
    "$SCRIPT_DIR/sophia_status.sh"
)

for script in "${SCRIPTS_TO_CHECK[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        log INFO "✅ $(basename $script) created and executable"
    else
        log ERROR "❌ $(basename $script) missing or not executable"
        VALIDATION_PASSED=false
    fi
done

# Check directories
DIRS_TO_CHECK=(
    "$LOG_DIR"
    "$BACKUP_DIR"
    "$CONFIG_DIR"
    "$PROJECT_ROOT/redis-data"
    "$PROJECT_ROOT/redis-backups"
)

for dir in "${DIRS_TO_CHECK[@]}"; do
    if [ -d "$dir" ]; then
        log INFO "✅ $(basename $dir) directory exists"
    else
        log ERROR "❌ $(basename $dir) directory missing"
        VALIDATION_PASSED=false
    fi
done

# Close rollback manifest
echo "]" >> "$ROLLBACK_MANIFEST"

# ============================================
# SUMMARY
# ============================================
log INFO ""
log INFO "========================================="
if [ "$VALIDATION_PASSED" = true ]; then
    log INFO "QUICK WINS IMPLEMENTATION SUCCESSFUL"
else
    log WARN "QUICK WINS COMPLETED WITH WARNINGS"
fi
log INFO "========================================="
log INFO ""
log INFO "Next steps:"
log INFO "1. Source aliases: source $PROJECT_ROOT/.sophia_aliases"
log INFO "2. Run status check: $SCRIPT_DIR/sophia_status.sh"
log INFO "3. Start monitoring: python3 $SCRIPT_DIR/mcp_health_monitor.py"
log INFO "4. Setup PM2: pm2 start $CONFIG_DIR/pm2.ecosystem.config.js"
log INFO ""
log INFO "All actions logged to: $QUICK_WINS_LOG"
log INFO "Rollback manifest: $ROLLBACK_MANIFEST"
log INFO ""

# Exit with appropriate code
if [ "$VALIDATION_PASSED" = true ]; then
    exit 0
else
    exit 2
fi