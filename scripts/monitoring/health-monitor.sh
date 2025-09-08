#!/bin/bash
set -euo pipefail

# Comprehensive Health Monitoring Script for Sophia AI
# Real-time health checks with timeout logic and alerting

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/sophia-health-monitor.log"
HEALTH_CHECK_INTERVAL=30
ALERT_THRESHOLD=3
TIMEOUT_PER_CHECK=10
MAX_CONSECUTIVE_FAILURES=5

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Global state tracking
declare -A SERVICE_FAILURES
declare -A SERVICE_STATUS
declare -A LAST_ALERT_TIME

# Services to monitor
declare -A SERVICES=(
    ["postgresql"]="docker exec sophia-postgres pg_isready -U postgres"
    ["redis"]="docker exec sophia-redis redis-cli ping"
    ["qdrant"]="curl -f -m 5 http://localhost:6333/health"
    ["neo4j"]="docker exec sophia-neo4j cypher-shell -u neo4j -p password 'RETURN 1'"
    ["backend-api"]="curl -f -m 5 http://localhost:8000/health"
    ["mcp-server"]="curl -f -m 5 http://localhost:8001/health"
    ["lambda-manager"]="curl -f -m 5 http://localhost:8002/health"
    ["frontend"]="curl -f -m 5 ${SOPHIA_FRONTEND_ENDPOINT}"
)

# Logging with timestamps
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case "$level" in
        "INFO")
            echo -e "${GREEN}[${timestamp}] INFO: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
        "WARN")
            echo -e "${YELLOW}[${timestamp}] WARN: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}] ERROR: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
        "DEBUG")
            echo -e "${BLUE}[${timestamp}] DEBUG: ${message}${NC}" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Send alert notification
send_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    local current_time=$(date +%s)
    
    # Check alert cooldown (5 minutes)
    local last_alert=${LAST_ALERT_TIME[$service]:-0}
    if [ $((current_time - last_alert)) -lt 300 ]; then
        log "DEBUG" "Alert cooldown active for $service, skipping notification"
        return 0
    fi
    
    LAST_ALERT_TIME[$service]=$current_time
    
    # Log alert
    log "ERROR" "ALERT: $service - $status - $message"
    
    # Send to Slack if webhook is configured
    if [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
        send_slack_alert "$service" "$status" "$message"
    fi
    
    # Send email if configured
    if [ -n "${ALERT_EMAIL:-}" ]; then
        send_email_alert "$service" "$status" "$message"
    fi
}

# Send Slack notification
send_slack_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    local color="#ff0000"  # Red for errors
    if [ "$status" == "recovered" ]; then
        color="#36a64f"  # Green for recovery
    elif [ "$status" == "degraded" ]; then
        color="#ff9500"  # Orange for warnings
    fi
    
    local payload=$(cat << EOF
{
    "attachments": [{
        "color": "$color",
        "title": "Sophia AI Health Alert: $service",
        "text": "$message",
        "fields": [
            {"title": "Service", "value": "$service", "short": true},
            {"title": "Status", "value": "$status", "short": true},
            {"title": "Timestamp", "value": "$(date -Iseconds)", "short": true}
        ],
        "footer": "Sophia AI Health Monitor"
    }]
}
EOF
    )
    
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$SLACK_WEBHOOK_URL" > /dev/null || log "WARN" "Failed to send Slack alert"
}

# Send email alert
send_email_alert() {
    local service="$1"
    local status="$2"
    local message="$3"
    
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "Sophia AI Alert: $service - $status" "$ALERT_EMAIL" || \
            log "WARN" "Failed to send email alert"
    else
        log "WARN" "Mail command not available for email alerts"
    fi
}

# Health check with timeout
health_check_with_timeout() {
    local service="$1"
    local command="$2"
    local timeout="$3"
    
    # Use timeout command to limit execution time
    if timeout "$timeout" bash -c "$command" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Check individual service health
check_service_health() {
    local service="$1"
    local command="$2"
    local start_time=$(date +%s.%N)
    
    log "DEBUG" "Checking health of $service..."
    
    if health_check_with_timeout "$service" "$command" "$TIMEOUT_PER_CHECK"; then
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc)
        
        # Service is healthy
        if [ "${SERVICE_STATUS[$service]:-unknown}" != "healthy" ]; then
            log "INFO" "✅ $service recovered (${duration}s)"
            send_alert "$service" "recovered" "$service is now healthy (response time: ${duration}s)"
        fi
        
        SERVICE_STATUS[$service]="healthy"
        SERVICE_FAILURES[$service]=0
        
        return 0
    else
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc)
        
        # Service is unhealthy
        local failures=${SERVICE_FAILURES[$service]:-0}
        ((failures++))
        SERVICE_FAILURES[$service]=$failures
        SERVICE_STATUS[$service]="unhealthy"
        
        log "WARN" "❌ $service health check failed (attempt $failures, ${duration}s)"
        
        # Send alert if threshold reached
        if [ $failures -ge $ALERT_THRESHOLD ]; then
            send_alert "$service" "critical" "$service has failed $failures consecutive health checks"
        fi
        
        # Emergency actions for critical failures
        if [ $failures -ge $MAX_CONSECUTIVE_FAILURES ]; then
            log "ERROR" "CRITICAL: $service has failed $failures consecutive checks, taking emergency action"
            emergency_action "$service"
        fi
        
        return 1
    fi
}

# Emergency actions for critical service failures
emergency_action() {
    local service="$1"
    
    case "$service" in
        "postgresql"|"redis"|"qdrant"|"neo4j")
            log "INFO" "Attempting to restart $service container..."
            docker restart "sophia-$service" 2>/dev/null || \
                log "ERROR" "Failed to restart $service container"
            ;;
        "backend-api"|"mcp-server"|"lambda-manager")
            log "INFO" "Service $service requires manual intervention"
            send_alert "$service" "critical" "$service requires immediate manual intervention"
            ;;
        "frontend")
            log "INFO" "Frontend service $service may need restart"
            ;;
    esac
}

# Generate health report
generate_health_report() {
    local report_file="/tmp/sophia-health-report.json"
    local timestamp=$(date -Iseconds)
    
    # Calculate overall health score
    local healthy_services=0
    local total_services=${#SERVICES[@]}
    
    for service in "${!SERVICES[@]}"; do
        if [ "${SERVICE_STATUS[$service]:-unknown}" == "healthy" ]; then
            ((healthy_services++))
        fi
    done
    
    local health_score=$((healthy_services * 100 / total_services))
    
    # Generate JSON report
    cat > "$report_file" << EOF
{
    "timestamp": "$timestamp",
    "overall_health_score": $health_score,
    "healthy_services": $healthy_services,
    "total_services": $total_services,
    "services": {
EOF
    
    local first=true
    for service in "${!SERVICES[@]}"; do
        if [ "$first" = true ]; then
            first=false
        else
            echo "," >> "$report_file"
        fi
        
        local status=${SERVICE_STATUS[$service]:-unknown}
        local failures=${SERVICE_FAILURES[$service]:-0}
        
        cat >> "$report_file" << EOF
        "$service": {
            "status": "$status",
            "consecutive_failures": $failures,
            "last_check": "$timestamp"
        }
EOF
    done
    
    cat >> "$report_file" << EOF
    },
    "system_info": {
        "uptime": "$(uptime -p)",
        "load_average": "$(uptime | awk -F'load average:' '{print $2}')",
        "disk_usage": "$(df -h /workspaces | awk 'NR==2 {print $5}')",
        "memory_usage": "$(free | awk 'NR==2{printf \"%.1f%%\", $3*100/$2}')"
    }
}
EOF
    
    log "INFO" "Health report generated: $report_file (Score: $health_score%)"
}

# Display real-time status
display_status() {
    clear
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                        Sophia AI Health Monitor                              ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║ Timestamp: $(date '+%Y-%m-%d %H:%M:%S')                                    ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    
    local healthy_count=0
    local total_count=${#SERVICES[@]}
    
    for service in "${!SERVICES[@]}"; do
        local status=${SERVICE_STATUS[$service]:-unknown}
        local failures=${SERVICE_FAILURES[$service]:-0}
        local status_icon="❓"
        local status_color="$NC"
        
        case "$status" in
            "healthy")
                status_icon="✅"
                status_color="$GREEN"
                ((healthy_count++))
                ;;
            "unhealthy")
                status_icon="❌"
                status_color="$RED"
                ;;
            "unknown")
                status_icon="❓"
                status_color="$YELLOW"
                ;;
        esac
        
        printf "║ %-20s %s %-10s Failures: %-3d                        ║\n" \
            "$service" "$status_icon" "$status" "$failures"
    done
    
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    
    local health_percentage=$((healthy_count * 100 / total_count))
    printf "║ Overall Health: %d%% (%d/%d services healthy)                           ║\n" \
        "$health_percentage" "$healthy_count" "$total_count"
    
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║ System Info:                                                                 ║"
    echo "║ Uptime: $(uptime -p | cut -c1-60)                                    ║"
    echo "║ Load: $(uptime | awk -F'load average:' '{print $2}' | cut -c1-60)                                      ║"
    echo "║ Memory: $(free | awk 'NR==2{printf "%.1f%%", $3*100/$2}')                                                           ║"
    echo "║ Disk: $(df -h /workspaces | awk 'NR==2 {print $5}')                                                             ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Press Ctrl+C to stop monitoring..."
}

# Continuous monitoring mode
continuous_monitoring() {
    log "INFO" "Starting continuous health monitoring (interval: ${HEALTH_CHECK_INTERVAL}s)"
    
    # Initialize service states
    for service in "${!SERVICES[@]}"; do
        SERVICE_FAILURES[$service]=0
        SERVICE_STATUS[$service]="unknown"
        LAST_ALERT_TIME[$service]=0
    done
    
    while true; do
        # Check all services
        for service in "${!SERVICES[@]}"; do
            check_service_health "$service" "${SERVICES[$service]}"
        done
        
        # Generate reports
        generate_health_report
        
        # Display status if in interactive mode
        if [ -t 1 ]; then
            display_status
        fi
        
        # Wait for next check
        sleep "$HEALTH_CHECK_INTERVAL"
    done
}

# Single check mode
single_check() {
    log "INFO" "Performing single health check of all services"
    
    local all_healthy=true
    
    for service in "${!SERVICES[@]}"; do
        if check_service_health "$service" "${SERVICES[$service]}"; then
            log "INFO" "✅ $service is healthy"
        else
            log "ERROR" "❌ $service is unhealthy"
            all_healthy=false
        fi
    done
    
    generate_health_report
    
    if [ "$all_healthy" = true ]; then
        log "INFO" "✅ All services are healthy"
        exit 0
    else
        log "ERROR" "❌ One or more services are unhealthy"
        exit 1
    fi
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Comprehensive health monitoring for Sophia AI services.

OPTIONS:
    -c, --continuous        Run continuous monitoring (default)
    -s, --single           Perform single health check and exit
    -i, --interval SECONDS Set monitoring interval (default: $HEALTH_CHECK_INTERVAL)
    -t, --timeout SECONDS  Set timeout per check (default: $TIMEOUT_PER_CHECK)
    -a, --alert-threshold N Set alert threshold (default: $ALERT_THRESHOLD)
    -h, --help             Show this help message

ENVIRONMENT VARIABLES:
    SLACK_WEBHOOK_URL      Slack webhook for alerts
    ALERT_EMAIL           Email address for alerts
    HEALTH_CHECK_INTERVAL  Monitoring interval in seconds
    TIMEOUT_PER_CHECK     Timeout per health check in seconds

EXAMPLES:
    $0                     # Continuous monitoring with defaults
    $0 --single           # Single health check
    $0 -i 60 -t 15        # Custom interval and timeout
    $0 --continuous       # Explicit continuous mode

EOF
}

# Main function
main() {
    local mode="continuous"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--continuous)
                mode="continuous"
                shift
                ;;
            -s|--single)
                mode="single"
                shift
                ;;
            -i|--interval)
                HEALTH_CHECK_INTERVAL="$2"
                shift 2
                ;;
            -t|--timeout)
                TIMEOUT_PER_CHECK="$2"
                shift 2
                ;;
            -a|--alert-threshold)
                ALERT_THRESHOLD="$2"
                shift 2
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    # Override from environment variables
    HEALTH_CHECK_INTERVAL=${HEALTH_CHECK_INTERVAL:-$HEALTH_CHECK_INTERVAL}
    TIMEOUT_PER_CHECK=${TIMEOUT_PER_CHECK:-$TIMEOUT_PER_CHECK}
    
    log "INFO" "🔍 Sophia AI Health Monitor Starting"
    log "INFO" "Mode: $mode"
    log "INFO" "Interval: ${HEALTH_CHECK_INTERVAL}s"
    log "INFO" "Timeout per check: ${TIMEOUT_PER_CHECK}s"
    log "INFO" "Alert threshold: $ALERT_THRESHOLD failures"
    
    # Execute based on mode
    case "$mode" in
        "continuous")
            continuous_monitoring
            ;;
        "single")
            single_check
            ;;
        *)
            echo "Invalid mode: $mode"
            exit 1
            ;;
    esac
}

# Handle interrupts gracefully
trap 'log "INFO" "Health monitoring stopped by user"; exit 0' INT TERM

# Execute main function
main "$@"

