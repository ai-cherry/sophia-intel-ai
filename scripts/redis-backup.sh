#!/bin/bash

# Redis Backup and Persistence Script for Sophia Intel AI Platform
# Provides automated backup, restore, and persistence management

set -euo pipefail

# Configuration
REDIS_CLI="/opt/homebrew/bin/redis-cli"
BACKUP_DIR="/opt/homebrew/var/backups/redis"
DATA_DIR="/opt/homebrew/var/db/redis"
REDIS_CONF="/Users/lynnmusil/sophia-intel-ai/config/redis.conf"
LOG_FILE="/opt/homebrew/var/log/redis/backup.log"

# Backup settings
BACKUP_RETENTION_DAYS=30
MAX_BACKUPS=50
COMPRESSION=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${BLUE}${message}${NC}"
    echo "$message" >> "$LOG_FILE"
}

warn() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1"
    echo -e "${YELLOW}${message}${NC}"
    echo "$message" >> "$LOG_FILE"
}

error() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1"
    echo -e "${RED}${message}${NC}"
    echo "$message" >> "$LOG_FILE"
    exit 1
}

success() {
    local message="[$(date +'%Y-%m-%d %H:%M:%S')] $1"
    echo -e "${GREEN}${message}${NC}"
    echo "$message" >> "$LOG_FILE"
}

# Setup backup directories
setup_directories() {
    log "Setting up backup directories..."

    mkdir -p "$BACKUP_DIR" || error "Failed to create backup directory: $BACKUP_DIR"
    mkdir -p "$(dirname "$LOG_FILE")" || error "Failed to create log directory"

    # Set permissions
    chmod 750 "$BACKUP_DIR"
    chmod 644 "$LOG_FILE" 2>/dev/null || touch "$LOG_FILE"

    success "Backup directories setup completed"
}

# Check Redis connectivity
check_redis() {
    log "Checking Redis connectivity..."

    if ! "$REDIS_CLI" ping > /dev/null 2>&1; then
        error "Redis is not responding. Cannot proceed with backup operations."
    fi

    success "Redis connectivity confirmed"
}

# Get Redis info
get_redis_info() {
    local info_section="$1"
    "$REDIS_CLI" info "$info_section" 2>/dev/null || echo ""
}

# Create full backup
create_backup() {
    local backup_type="${1:-scheduled}"
    local timestamp=$(date +'%Y%m%d_%H%M%S')
    local backup_name="redis_backup_${timestamp}"
    local backup_path="$BACKUP_DIR/$backup_name"

    log "Starting Redis backup: $backup_name (type: $backup_type)"

    # Create backup directory
    mkdir -p "$backup_path"

    # Get Redis info before backup
    local redis_info=$(get_redis_info "server")
    local memory_info=$(get_redis_info "memory")
    local keyspace_info=$(get_redis_info "keyspace")

    # Save backup metadata
    cat > "$backup_path/backup_metadata.json" << EOF
{
    "backup_timestamp": "$(date -Iseconds)",
    "backup_type": "$backup_type",
    "redis_version": "$(echo "$redis_info" | grep "redis_version:" | cut -d: -f2 | tr -d '\r')",
    "used_memory": "$(echo "$memory_info" | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')",
    "databases": $(echo "$keyspace_info" | grep -c "^db[0-9]*:" || echo "0"),
    "backup_method": "RDB + AOF + Config",
    "hostname": "$(hostname)",
    "backup_path": "$backup_path"
}
EOF

    # Trigger RDB save
    log "Triggering RDB snapshot..."
    "$REDIS_CLI" bgsave > /dev/null

    # Wait for background save to complete
    local save_time=0
    while [ "$("$REDIS_CLI" lastsave)" = "$("$REDIS_CLI" lastsave)" ] && [ $save_time -lt 300 ]; do
        sleep 2
        save_time=$((save_time + 2))
    done

    if [ $save_time -ge 300 ]; then
        warn "Background save took longer than expected, continuing anyway"
    fi

    # Copy RDB file
    if [ -f "$DATA_DIR/sophia-intel-ai.rdb" ]; then
        cp "$DATA_DIR/sophia-intel-ai.rdb" "$backup_path/"
        success "RDB file backed up"
    else
        warn "RDB file not found, skipping"
    fi

    # Copy AOF file if it exists
    if [ -f "$DATA_DIR/sophia-intel-ai.aof" ]; then
        cp "$DATA_DIR/sophia-intel-ai.aof" "$backup_path/"
        success "AOF file backed up"
    else
        log "AOF file not found (may be disabled)"
    fi

    # Copy configuration
    if [ -f "$REDIS_CONF" ]; then
        cp "$REDIS_CONF" "$backup_path/redis.conf"
        success "Configuration file backed up"
    else
        warn "Redis configuration file not found"
    fi

    # Export Redis data as text (for easy inspection)
    log "Exporting Redis data as text dump..."
    "$REDIS_CLI" --scan | head -10000 | while read key; do
        key_type=$("$REDIS_CLI" type "$key" | tr -d '\r')
        case "$key_type" in
            "string")
                echo "SET \"$key\" \"$("$REDIS_CLI" get "$key")\""
                ;;
            "hash")
                "$REDIS_CLI" hgetall "$key" | paste - - | sed 's/^/HSET "'"$key"'" /'
                ;;
            "list")
                "$REDIS_CLI" lrange "$key" 0 -1 | sed 's/^/LPUSH "'"$key"'" /'
                ;;
            "set")
                "$REDIS_CLI" smembers "$key" | sed 's/^/SADD "'"$key"'" /'
                ;;
            "zset")
                "$REDIS_CLI" zrange "$key" 0 -1 withscores | paste - - | sed 's/^/ZADD "'"$key"'" /'
                ;;
        esac
    done > "$backup_path/data_dump.redis" 2>/dev/null || true

    # Get database statistics
    cat > "$backup_path/database_stats.txt" << EOF
Redis Database Statistics - $(date)
=====================================

Server Info:
$(get_redis_info "server" | grep -E "(redis_version|uptime_in_seconds|tcp_port)")

Memory Info:
$(get_redis_info "memory" | grep -E "(used_memory|used_memory_human|maxmemory)")

Keyspace Info:
$(get_redis_info "keyspace")

Client Info:
$(get_redis_info "clients" | grep -E "(connected_clients|blocked_clients)")

Stats:
$(get_redis_info "stats" | grep -E "(total_commands_processed|keyspace_hits|keyspace_misses)")
EOF

    # Compress backup if enabled
    if [ "$COMPRESSION" = true ]; then
        log "Compressing backup..."
        cd "$BACKUP_DIR"
        tar -czf "${backup_name}.tar.gz" "$backup_name"
        rm -rf "$backup_name"
        backup_path="${backup_path}.tar.gz"
        success "Backup compressed to ${backup_name}.tar.gz"
    fi

    # Calculate backup size
    local backup_size=$(du -h "$backup_path" | cut -f1)

    success "Redis backup completed: $backup_name"
    log "Backup size: $backup_size"
    log "Backup location: $backup_path"

    # Update backup index
    update_backup_index "$backup_name" "$backup_size" "$backup_type"

    # Cleanup old backups
    cleanup_old_backups

    echo "$backup_path"
}

# Update backup index
update_backup_index() {
    local backup_name="$1"
    local backup_size="$2"
    local backup_type="$3"
    local index_file="$BACKUP_DIR/backup_index.txt"

    local entry="$(date -Iseconds),$backup_name,$backup_size,$backup_type"
    echo "$entry" >> "$index_file"

    # Keep only last 100 entries
    if [ -f "$index_file" ]; then
        tail -n 100 "$index_file" > "${index_file}.tmp"
        mv "${index_file}.tmp" "$index_file"
    fi
}

# List backups
list_backups() {
    log "Available Redis backups:"
    echo "========================="

    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR" 2>/dev/null)" ]; then
        echo "No backups found"
        return 0
    fi

    # Show backup index if available
    if [ -f "$BACKUP_DIR/backup_index.txt" ]; then
        echo "Date                     | Backup Name              | Size    | Type"
        echo "-------------------------|--------------------------|---------|----------"
        tail -n 20 "$BACKUP_DIR/backup_index.txt" | while IFS=',' read -r date name size type; do
            printf "%-24s | %-24s | %-7s | %-8s\n" "$date" "$name" "$size" "$type"
        done
    else
        # Fallback to directory listing
        ls -la "$BACKUP_DIR" | grep -E "(redis_backup_|\.tar\.gz$)" | while read -r line; do
            echo "$line"
        done
    fi

    echo "========================="
    local total_backups=$(find "$BACKUP_DIR" -name "redis_backup_*" | wc -l)
    log "Total backups: $total_backups"
}

# Restore from backup
restore_backup() {
    local backup_name="$1"
    local force="${2:-false}"

    if [ -z "$backup_name" ]; then
        error "Backup name is required for restore operation"
    fi

    log "Starting Redis restore from backup: $backup_name"

    # Find backup file
    local backup_path=""
    if [ -f "$BACKUP_DIR/${backup_name}.tar.gz" ]; then
        backup_path="$BACKUP_DIR/${backup_name}.tar.gz"
    elif [ -d "$BACKUP_DIR/$backup_name" ]; then
        backup_path="$BACKUP_DIR/$backup_name"
    else
        error "Backup not found: $backup_name"
    fi

    # Confirm restore operation
    if [ "$force" != "true" ]; then
        echo -n "This will overwrite current Redis data. Continue? [y/N]: "
        read -r confirm
        if [[ ! $confirm =~ ^[Yy]$ ]]; then
            log "Restore operation cancelled"
            exit 0
        fi
    fi

    # Stop Redis for restore
    log "Stopping Redis for restore..."
    local redis_pid=""
    if pgrep -f "redis-server" > /dev/null; then
        redis_pid=$(pgrep -f "redis-server")
        kill "$redis_pid" || warn "Failed to stop Redis gracefully"
        sleep 5

        # Force kill if still running
        if pgrep -f "redis-server" > /dev/null; then
            pkill -9 -f "redis-server" || true
            sleep 2
        fi
    fi

    # Extract compressed backup if needed
    local restore_dir="$backup_path"
    if [[ "$backup_path" == *.tar.gz ]]; then
        log "Extracting compressed backup..."
        restore_dir="$BACKUP_DIR/${backup_name}_restore_temp"
        mkdir -p "$restore_dir"
        tar -xzf "$backup_path" -C "$restore_dir" --strip-components=1
    fi

    # Backup current data
    local current_backup_name="pre_restore_$(date +'%Y%m%d_%H%M%S')"
    log "Creating backup of current data: $current_backup_name"
    mkdir -p "$BACKUP_DIR/$current_backup_name"

    if [ -f "$DATA_DIR/sophia-intel-ai.rdb" ]; then
        cp "$DATA_DIR/sophia-intel-ai.rdb" "$BACKUP_DIR/$current_backup_name/"
    fi
    if [ -f "$DATA_DIR/sophia-intel-ai.aof" ]; then
        cp "$DATA_DIR/sophia-intel-ai.aof" "$BACKUP_DIR/$current_backup_name/"
    fi

    # Restore data files
    log "Restoring data files..."

    if [ -f "$restore_dir/sophia-intel-ai.rdb" ]; then
        cp "$restore_dir/sophia-intel-ai.rdb" "$DATA_DIR/"
        success "RDB file restored"
    fi

    if [ -f "$restore_dir/sophia-intel-ai.aof" ]; then
        cp "$restore_dir/sophia-intel-ai.aof" "$DATA_DIR/"
        success "AOF file restored"
    fi

    # Set proper permissions
    chown redis:redis "$DATA_DIR"/* 2>/dev/null || true
    chmod 660 "$DATA_DIR"/* 2>/dev/null || true

    # Cleanup temporary extraction
    if [[ "$backup_path" == *.tar.gz ]]; then
        rm -rf "$restore_dir"
    fi

    success "Redis restore completed from backup: $backup_name"
    log "Current data backed up to: $current_backup_name"
    warn "Please restart Redis to load the restored data"
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up old backups..."

    # Remove backups older than retention period
    find "$BACKUP_DIR" -name "redis_backup_*" -type f -mtime +$BACKUP_RETENTION_DAYS -delete 2>/dev/null || true
    find "$BACKUP_DIR" -name "redis_backup_*" -type d -mtime +$BACKUP_RETENTION_DAYS -exec rm -rf {} \; 2>/dev/null || true

    # Keep only the most recent backups if we have too many
    local backup_count=$(find "$BACKUP_DIR" -name "redis_backup_*" | wc -l)
    if [ "$backup_count" -gt "$MAX_BACKUPS" ]; then
        local excess_count=$((backup_count - MAX_BACKUPS))
        find "$BACKUP_DIR" -name "redis_backup_*" -printf '%T@ %p\n' | sort -n | head -n "$excess_count" | cut -d' ' -f2- | xargs rm -rf
        log "Removed $excess_count old backups"
    fi

    success "Backup cleanup completed"
}

# Verify backup integrity
verify_backup() {
    local backup_name="$1"

    if [ -z "$backup_name" ]; then
        error "Backup name is required for verification"
    fi

    log "Verifying backup integrity: $backup_name"

    # Find backup
    local backup_path=""
    if [ -f "$BACKUP_DIR/${backup_name}.tar.gz" ]; then
        backup_path="$BACKUP_DIR/${backup_name}.tar.gz"
    elif [ -d "$BACKUP_DIR/$backup_name" ]; then
        backup_path="$BACKUP_DIR/$backup_name"
    else
        error "Backup not found: $backup_name"
    fi

    # Verify compressed backup
    if [[ "$backup_path" == *.tar.gz ]]; then
        if tar -tzf "$backup_path" > /dev/null 2>&1; then
            success "Compressed backup archive is valid"
        else
            error "Compressed backup archive is corrupted"
        fi

        # Extract to temporary location for further verification
        local temp_dir=$(mktemp -d)
        tar -xzf "$backup_path" -C "$temp_dir"
        backup_path="$temp_dir/$(basename "$backup_name")"
    fi

    # Verify metadata
    if [ -f "$backup_path/backup_metadata.json" ]; then
        if jq empty "$backup_path/backup_metadata.json" 2>/dev/null; then
            success "Backup metadata is valid"
        else
            warn "Backup metadata is invalid or corrupted"
        fi
    else
        warn "Backup metadata not found"
    fi

    # Verify RDB file
    if [ -f "$backup_path/sophia-intel-ai.rdb" ]; then
        if redis-check-rdb "$backup_path/sophia-intel-ai.rdb" 2>/dev/null; then
            success "RDB file is valid"
        else
            warn "RDB file validation failed"
        fi
    else
        warn "RDB file not found in backup"
    fi

    # Verify AOF file if present
    if [ -f "$backup_path/sophia-intel-ai.aof" ]; then
        if redis-check-aof "$backup_path/sophia-intel-ai.aof" 2>/dev/null; then
            success "AOF file is valid"
        else
            warn "AOF file validation failed"
        fi
    fi

    # Cleanup temporary extraction
    if [[ "$backup_path" == /tmp/* ]]; then
        rm -rf "$(dirname "$backup_path")"
    fi

    success "Backup verification completed"
}

# Show help
show_help() {
    cat << EOF
Redis Backup and Persistence Script for Sophia Intel AI Platform

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    backup [type]              Create a new backup (type: manual, scheduled, pre-upgrade)
    list                       List all available backups
    restore <backup_name>      Restore from a specific backup
    verify <backup_name>       Verify backup integrity
    cleanup                    Remove old backups based on retention policy
    help                       Show this help message

Options:
    --force                    Force operations without confirmation (for restore)

Examples:
    $0 backup manual           Create manual backup
    $0 list                    Show all backups
    $0 restore redis_backup_20240101_120000
    $0 verify redis_backup_20240101_120000
    $0 cleanup                 Remove old backups

Configuration:
    Backup Directory: $BACKUP_DIR
    Retention Days: $BACKUP_RETENTION_DAYS
    Max Backups: $MAX_BACKUPS
    Compression: $COMPRESSION

EOF
}

# Main execution
main() {
    local command="${1:-help}"

    # Setup logging and directories
    setup_directories

    case "$command" in
        backup)
            check_redis
            local backup_type="${2:-scheduled}"
            create_backup "$backup_type"
            ;;
        list)
            list_backups
            ;;
        restore)
            local backup_name="$2"
            local force="false"
            [[ "${3:-}" == "--force" ]] && force="true"
            restore_backup "$backup_name" "$force"
            ;;
        verify)
            local backup_name="$2"
            verify_backup "$backup_name"
            ;;
        cleanup)
            cleanup_old_backups
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Handle script arguments
main "$@"
