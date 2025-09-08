#!/bin/bash
set -euo pipefail

# Emergency Shutdown Script for Sophia AI Lambda Labs Instances
# Audit-compliant shutdown with comprehensive cleanup and validation

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/shutdown-production.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [INSTANCE_ID]

Emergency shutdown script for Sophia AI Lambda Labs instances.

OPTIONS:
    -a, --all           Shutdown all Sophia AI instances
    -f, --force         Force shutdown without confirmation
    -h, --help          Show this help message
    -l, --list          List all running instances
    -s, --save-data     Save instance data before shutdown

EXAMPLES:
    $0 instance-123                    # Shutdown specific instance
    $0 --all                          # Shutdown all instances (with confirmation)
    $0 --all --force                  # Shutdown all instances (no confirmation)
    $0 --list                         # List all running instances
    $0 --save-data instance-123       # Save data before shutdown

ENVIRONMENT VARIABLES:
    LAMBDA_API_KEY                    # Required: Lambda Labs API key
    SLACK_WEBHOOK_URL                 # Optional: Slack notifications

EOF
}

# Validate environment
validate_environment() {
    if [[ -z "${LAMBDA_API_KEY:-}" ]]; then
        error_exit "LAMBDA_API_KEY environment variable is required"
    fi
    
    # Test API connectivity
    local api_response
    api_response=$(curl -s -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
        "https://cloud.lambdalabs.com/api/v1/instances" || echo "")
    
    if [[ -z "$api_response" ]] || echo "$api_response" | jq -e '.error' > /dev/null 2>&1; then
        error_exit "Lambda Labs API validation failed"
    fi
    
    log "✅ Environment validation complete"
}

# Get all Sophia AI instances
get_sophia_instances() {
    log "Fetching Sophia AI instances..."
    
    local api_response
    api_response=$(curl -s -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
        "https://cloud.lambdalabs.com/api/v1/instances")
    
    if echo "$api_response" | jq -e '.error' > /dev/null 2>&1; then
        error_exit "Failed to fetch instances: $(echo "$api_response" | jq -r '.error.message')"
    fi
    
    # Filter for Sophia AI instances
    echo "$api_response" | jq -r '.data[] | select(.name | startswith("sophia-ai")) | .id'
}

# Get instance details
get_instance_details() {
    local instance_id="$1"
    
    local api_response
    api_response=$(curl -s -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
        "https://cloud.lambdalabs.com/api/v1/instances")
    
    echo "$api_response" | jq -r ".data[] | select(.id == \"$instance_id\")"
}

# List all instances
list_instances() {
    log "Listing all Sophia AI instances..."
    
    local instances
    instances=$(get_sophia_instances)
    
    if [[ -z "$instances" ]]; then
        log "No Sophia AI instances found"
        return 0
    fi
    
    echo ""
    echo "┌─────────────────────────────────────┬──────────────────┬─────────────────┬──────────────┬─────────────┐"
    echo "│ Instance ID                         │ Name             │ IP Address      │ Type         │ Status      │"
    echo "├─────────────────────────────────────┼──────────────────┼─────────────────┼──────────────┼─────────────┤"
    
    while IFS= read -r instance_id; do
        if [[ -n "$instance_id" ]]; then
            local details
            details=$(get_instance_details "$instance_id")
            
            local name ip instance_type status
            name=$(echo "$details" | jq -r '.name // "unknown"')
            ip=$(echo "$details" | jq -r '.ip // "pending"')
            instance_type=$(echo "$details" | jq -r '.instance_type.name // "unknown"')
            status=$(echo "$details" | jq -r '.status // "unknown"')
            
            printf "│ %-35s │ %-16s │ %-15s │ %-12s │ %-11s │\n" \
                "$instance_id" "$name" "$ip" "$instance_type" "$status"
        fi
    done <<< "$instances"
    
    echo "└─────────────────────────────────────┴──────────────────┴─────────────────┴──────────────┴─────────────┘"
    echo ""
}

# Save instance data
save_instance_data() {
    local instance_id="$1"
    local instance_ip="$2"
    
    log "Saving instance data for $instance_id..."
    
    local backup_dir="/tmp/sophia-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Save instance details
    get_instance_details "$instance_id" > "$backup_dir/instance-details.json"
    
    # Save monitoring data if available
    if [[ -n "$instance_ip" && "$instance_ip" != "pending" ]]; then
        log "Downloading monitoring data from $instance_ip..."
        
        # Save monitoring report
        curl -s "http://$instance_ip:9090/metrics" > "$backup_dir/final-metrics.json" 2>/dev/null || true
        
        # Save cost analysis
        curl -s "http://$instance_ip:8002/cost-analysis" > "$backup_dir/cost-analysis.json" 2>/dev/null || true
        
        # Save service logs if SSH is available
        if command -v ssh &> /dev/null && [[ -f ~/.ssh/lambda_key ]]; then
            log "Downloading service logs..."
            
            ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
                -i ~/.ssh/lambda_key "ubuntu@$instance_ip" \
                "tar -czf /tmp/sophia-logs.tar.gz /var/log/sophia-*.log 2>/dev/null || true" 2>/dev/null || true
            
            scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 \
                -i ~/.ssh/lambda_key "ubuntu@$instance_ip:/tmp/sophia-logs.tar.gz" \
                "$backup_dir/service-logs.tar.gz" 2>/dev/null || true
        fi
    fi
    
    log "✅ Instance data saved to $backup_dir"
    echo "$backup_dir"
}

# Send shutdown notification
send_notification() {
    local instance_id="$1"
    local reason="$2"
    
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        log "Sending shutdown notification..."
        
        local payload
        payload=$(jq -n \
            --arg instance_id "$instance_id" \
            --arg reason "$reason" \
            --arg timestamp "$(date -Iseconds)" \
            '{
                attachments: [{
                    color: "#ff9500",
                    title: "Sophia AI Instance Shutdown",
                    fields: [
                        {title: "Instance ID", value: $instance_id, short: true},
                        {title: "Reason", value: $reason, short: true},
                        {title: "Timestamp", value: $timestamp, short: true}
                    ],
                    footer: "Sophia AI Production Monitor"
                }]
            }')
        
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -d "$payload" \
            "$SLACK_WEBHOOK_URL" > /dev/null || true
    fi
}

# Terminate instance
terminate_instance() {
    local instance_id="$1"
    local reason="${2:-Manual shutdown}"
    
    log "Terminating instance $instance_id..."
    
    # Get instance details before termination
    local details
    details=$(get_instance_details "$instance_id")
    
    if [[ -z "$details" || "$details" == "null" ]]; then
        error_exit "Instance $instance_id not found"
    fi
    
    local instance_name instance_ip instance_type
    instance_name=$(echo "$details" | jq -r '.name // "unknown"')
    instance_ip=$(echo "$details" | jq -r '.ip // "pending"')
    instance_type=$(echo "$details" | jq -r '.instance_type.name // "unknown"')
    
    log "Instance details:"
    log "  Name: $instance_name"
    log "  IP: $instance_ip"
    log "  Type: $instance_type"
    
    # Send notification
    send_notification "$instance_id" "$reason"
    
    # Terminate instance
    local terminate_response
    terminate_response=$(curl -s -X POST \
        -H "Authorization: Bearer ${LAMBDA_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"instance_ids\": [\"$instance_id\"]}" \
        "https://cloud.lambdalabs.com/api/v1/instance-operations/terminate")
    
    if echo "$terminate_response" | jq -e '.error' > /dev/null 2>&1; then
        error_exit "Termination failed: $(echo "$terminate_response" | jq -r '.error.message')"
    fi
    
    log "✅ Instance $instance_id termination initiated"
    
    # Wait for termination confirmation
    log "Waiting for termination confirmation..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local current_status
        current_status=$(get_instance_details "$instance_id" | jq -r '.status // "terminated"')
        
        if [[ "$current_status" == "terminated" || "$current_status" == "null" ]]; then
            log "✅ Instance $instance_id successfully terminated"
            return 0
        fi
        
        log "Attempt $attempt/$max_attempts: Status is $current_status, waiting..."
        sleep 10
        ((attempt++))
    done
    
    log "⚠️  Termination confirmation timeout, but termination was initiated"
}

# Shutdown all instances
shutdown_all() {
    local force="$1"
    
    local instances
    instances=$(get_sophia_instances)
    
    if [[ -z "$instances" ]]; then
        log "No Sophia AI instances found to shutdown"
        return 0
    fi
    
    local instance_count
    instance_count=$(echo "$instances" | wc -l)
    
    log "Found $instance_count Sophia AI instances to shutdown"
    
    if [[ "$force" != "true" ]]; then
        echo ""
        echo "⚠️  WARNING: This will shutdown ALL Sophia AI instances!"
        echo ""
        list_instances
        echo ""
        read -p "Are you sure you want to continue? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "Shutdown cancelled by user"
            exit 0
        fi
    fi
    
    log "Proceeding with shutdown of all instances..."
    
    while IFS= read -r instance_id; do
        if [[ -n "$instance_id" ]]; then
            log "Shutting down instance: $instance_id"
            terminate_instance "$instance_id" "Bulk shutdown"
        fi
    done <<< "$instances"
    
    log "✅ All instances shutdown complete"
}

# Main function
main() {
    local instance_id=""
    local shutdown_all_flag=false
    local force_flag=false
    local list_flag=false
    local save_data_flag=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--all)
                shutdown_all_flag=true
                shift
                ;;
            -f|--force)
                force_flag=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -l|--list)
                list_flag=true
                shift
                ;;
            -s|--save-data)
                save_data_flag=true
                shift
                ;;
            -*)
                error_exit "Unknown option: $1"
                ;;
            *)
                if [[ -z "$instance_id" ]]; then
                    instance_id="$1"
                else
                    error_exit "Multiple instance IDs provided"
                fi
                shift
                ;;
        esac
    done
    
    log "🚨 Starting Sophia AI emergency shutdown script..."
    
    # Validate environment
    validate_environment
    
    # Handle list option
    if [[ "$list_flag" == true ]]; then
        list_instances
        exit 0
    fi
    
    # Handle shutdown all option
    if [[ "$shutdown_all_flag" == true ]]; then
        shutdown_all "$force_flag"
        exit 0
    fi
    
    # Handle single instance shutdown
    if [[ -z "$instance_id" ]]; then
        error_exit "Instance ID required. Use --help for usage information."
    fi
    
    # Save data if requested
    if [[ "$save_data_flag" == true ]]; then
        local details
        details=$(get_instance_details "$instance_id")
        local instance_ip
        instance_ip=$(echo "$details" | jq -r '.ip // "pending"')
        
        local backup_dir
        backup_dir=$(save_instance_data "$instance_id" "$instance_ip")
        log "Data backup completed: $backup_dir"
    fi
    
    # Confirm shutdown if not forced
    if [[ "$force_flag" != true ]]; then
        echo ""
        echo "⚠️  WARNING: This will shutdown instance $instance_id"
        echo ""
        
        # Show instance details
        local details
        details=$(get_instance_details "$instance_id")
        if [[ -n "$details" && "$details" != "null" ]]; then
            echo "Instance Details:"
            echo "  ID: $instance_id"
            echo "  Name: $(echo "$details" | jq -r '.name // "unknown"')"
            echo "  IP: $(echo "$details" | jq -r '.ip // "pending"')"
            echo "  Type: $(echo "$details" | jq -r '.instance_type.name // "unknown"')"
            echo "  Status: $(echo "$details" | jq -r '.status // "unknown"')"
        fi
        
        echo ""
        read -p "Are you sure you want to shutdown this instance? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log "Shutdown cancelled by user"
            exit 0
        fi
    fi
    
    # Terminate the instance
    terminate_instance "$instance_id" "Manual shutdown"
    
    log "✅ Shutdown complete"
}

# Execute main function
main "$@"

