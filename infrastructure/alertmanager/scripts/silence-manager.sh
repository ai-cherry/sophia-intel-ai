#!/bin/bash

# AlertManager Silence Manager Script
# Manages maintenance windows and alert silencing

set -e

# Configuration
NAMESPACE="${NAMESPACE:-monitoring}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://alertmanager.monitoring:9093}"
ACTION="${ACTION:-list}"  # list, create, delete, expire

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# List all silences
list_silences() {
    log "Listing all silences..."

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    if [[ -z "$pod" ]]; then
        error "No AlertManager pod found"
        return 1
    fi

    # Get silences via API
    local silences=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/api/v2/silences 2>/dev/null)

    if [[ -z "$silences" ]] || [[ "$silences" == "[]" ]]; then
        info "No active silences found"
        return 0
    fi

    # Parse and display silences
    echo "$silences" | jq -r '.[] |
        "ID: \(.id)
        Status: \(.status.state)
        Created by: \(.createdBy)
        Comment: \(.comment)
        Starts: \(.startsAt)
        Ends: \(.endsAt)
        Matchers: \(.matchers | map("\(.name) \(.isRegex // false | if . then "=~" else "=" end) \(.value)") | join(", "))
        ----------------------------------------"'
}

# Create a silence
create_silence() {
    local duration="${DURATION:-1h}"
    local comment="${COMMENT:-Maintenance window}"
    local created_by="${CREATED_BY:-silence-manager}"
    local matchers="$1"

    if [[ -z "$matchers" ]]; then
        error "Matchers are required for creating silence"
        echo "Usage: $0 create 'alertname=TestAlert,severity=warning'"
        return 1
    fi

    log "Creating silence..."
    info "Duration: $duration"
    info "Comment: $comment"
    info "Matchers: $matchers"

    # Parse matchers
    local matcher_json="["
    IFS=',' read -ra MATCHER_ARRAY <<< "$matchers"
    for i in "${!MATCHER_ARRAY[@]}"; do
        local matcher="${MATCHER_ARRAY[$i]}"
        if [[ $matcher =~ ^([^=~]+)(=~?)(.+)$ ]]; then
            local name="${BASH_REMATCH[1]}"
            local op="${BASH_REMATCH[2]}"
            local value="${BASH_REMATCH[3]}"
            local is_regex="false"

            if [[ "$op" == "=~" ]]; then
                is_regex="true"
            fi

            if [[ $i -gt 0 ]]; then
                matcher_json+=","
            fi
            matcher_json+="{\"name\":\"$name\",\"value\":\"$value\",\"isRegex\":$is_regex,\"isEqual\":true}"
        fi
    done
    matcher_json+="]"

    # Calculate times
    local starts_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local ends_at=$(date -u -d "+$duration" +"%Y-%m-%dT%H:%M:%SZ")

    # Create silence JSON
    local silence_json=$(cat <<EOF
{
    "matchers": $matcher_json,
    "startsAt": "$starts_at",
    "endsAt": "$ends_at",
    "createdBy": "$created_by",
    "comment": "$comment"
}
EOF
    )

    # Send to AlertManager
    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    local response=$(kubectl exec -n "$NAMESPACE" "$pod" -- sh -c "
        wget -O- --post-data='$silence_json' \
        --header='Content-Type: application/json' \
        http://localhost:9093/api/v2/silences 2>/dev/null
    ")

    local silence_id=$(echo "$response" | jq -r '.silenceID // .id')

    if [[ -n "$silence_id" ]] && [[ "$silence_id" != "null" ]]; then
        log "✅ Silence created successfully"
        log "Silence ID: $silence_id"
        log "Expires at: $ends_at"
    else
        error "Failed to create silence"
        echo "$response"
        return 1
    fi
}

# Delete a silence
delete_silence() {
    local silence_id="$1"

    if [[ -z "$silence_id" ]]; then
        error "Silence ID is required"
        echo "Usage: $0 delete <silence-id>"
        return 1
    fi

    log "Deleting silence $silence_id..."

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    local response=$(kubectl exec -n "$NAMESPACE" "$pod" -- sh -c "
        wget -O- --method=DELETE \
        http://localhost:9093/api/v2/silence/$silence_id 2>&1
    ")

    if [[ $? -eq 0 ]]; then
        log "✅ Silence $silence_id deleted successfully"
    else
        error "Failed to delete silence $silence_id"
        echo "$response"
        return 1
    fi
}

# Expire all silences
expire_all_silences() {
    log "Expiring all active silences..."

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    # Get all active silences
    local silences=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/api/v2/silences 2>/dev/null | \
        jq -r '.[] | select(.status.state == "active") | .id')

    if [[ -z "$silences" ]]; then
        info "No active silences to expire"
        return 0
    fi

    local count=0
    while IFS= read -r silence_id; do
        if [[ -n "$silence_id" ]]; then
            info "Expiring silence: $silence_id"
            delete_silence "$silence_id"
            ((count++))
        fi
    done <<< "$silences"

    log "✅ Expired $count silence(s)"
}

# Create maintenance window
create_maintenance_window() {
    local namespace="${MW_NAMESPACE:-all}"
    local duration="${MW_DURATION:-2h}"
    local services="${MW_SERVICES:-}"

    log "Creating maintenance window..."
    info "Namespace: $namespace"
    info "Duration: $duration"
    info "Services: ${services:-all}"

    # Create broad silence for maintenance
    local matchers=""

    if [[ "$namespace" != "all" ]]; then
        matchers="namespace=$namespace"
    fi

    if [[ -n "$services" ]]; then
        if [[ -n "$matchers" ]]; then
            matchers+=","
        fi
        matchers+="service=~($services)"
    fi

    # Add maintenance label
    if [[ -n "$matchers" ]]; then
        matchers+=","
    fi
    matchers+="severity!=CRITICAL"  # Don't silence critical alerts during maintenance

    DURATION="$duration" \
    COMMENT="Scheduled maintenance window for $namespace" \
    CREATED_BY="maintenance-automation" \
    create_silence "$matchers"
}

# Quick silence templates
quick_silence() {
    local template="$1"

    case "$template" in
        node)
            local node="${2:-}"
            if [[ -z "$node" ]]; then
                error "Node name required"
                echo "Usage: $0 quick node <node-name>"
                return 1
            fi
            COMMENT="Node maintenance: $node" \
            DURATION="${DURATION:-4h}" \
            create_silence "node=$node"
            ;;

        namespace)
            local ns="${2:-}"
            if [[ -z "$ns" ]]; then
                error "Namespace required"
                echo "Usage: $0 quick namespace <namespace>"
                return 1
            fi
            COMMENT="Namespace maintenance: $ns" \
            DURATION="${DURATION:-2h}" \
            create_silence "namespace=$ns"
            ;;

        deployment)
            local ns="${2:-}"
            local name="${3:-}"
            if [[ -z "$ns" ]] || [[ -z "$name" ]]; then
                error "Namespace and deployment name required"
                echo "Usage: $0 quick deployment <namespace> <name>"
                return 1
            fi
            COMMENT="Deployment update: $name" \
            DURATION="${DURATION:-30m}" \
            create_silence "namespace=$ns,deployment=$name"
            ;;

        gpu)
            COMMENT="GPU node maintenance" \
            DURATION="${DURATION:-6h}" \
            create_silence "alertname=~GPU.*|CUDA.*"
            ;;

        scaling)
            COMMENT="Temporary scaling event suppression" \
            DURATION="${DURATION:-1h}" \
            create_silence "alertname=~KEDA.*|.*Scaling.*"
            ;;

        testing)
            COMMENT="Test alert suppression" \
            DURATION="${DURATION:-15m}" \
            create_silence "test=true"
            ;;

        *)
            error "Unknown template: $template"
            echo "Available templates:"
            echo "  node <node-name>        - Silence alerts for a specific node"
            echo "  namespace <namespace>   - Silence alerts for a namespace"
            echo "  deployment <ns> <name>  - Silence alerts for a deployment"
            echo "  gpu                     - Silence GPU-related alerts"
            echo "  scaling                 - Silence scaling alerts"
            echo "  testing                 - Silence test alerts"
            return 1
            ;;
    esac
}

# Show active alerts that would be silenced
preview_silence() {
    local matchers="$1"

    if [[ -z "$matchers" ]]; then
        error "Matchers are required for preview"
        return 1
    fi

    log "Previewing alerts that would be silenced by: $matchers"

    local pod=$(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}')

    # Get all active alerts
    local alerts=$(kubectl exec -n "$NAMESPACE" "$pod" -- \
        wget -qO- http://localhost:9093/api/v2/alerts 2>/dev/null)

    # Parse matchers
    IFS=',' read -ra MATCHER_ARRAY <<< "$matchers"

    # Filter and display matching alerts
    echo "$alerts" | jq -r --arg matchers "$matchers" '
        .[] | select(.labels | to_entries | map(
            .key + "=" + .value
        ) | join(",") | contains($matchers)) |
        "Alert: \(.labels.alertname)
        Severity: \(.labels.severity // "unknown")
        Namespace: \(.labels.namespace // "unknown")
        Service: \(.labels.service // "unknown")
        Description: \(.annotations.description // "No description")
        ----------------------------------------"'

    local count=$(echo "$alerts" | jq -r --arg matchers "$matchers" '
        [.[] | select(.labels | to_entries | map(
            .key + "=" + .value
        ) | join(",") | contains($matchers))] | length')

    info "Would silence $count alert(s)"
}

# Main execution
main() {
    case "$ACTION" in
        list)
            list_silences
            ;;
        create)
            create_silence "$@"
            ;;
        delete)
            delete_silence "$@"
            ;;
        expire)
            expire_all_silences
            ;;
        maintenance)
            create_maintenance_window
            ;;
        quick)
            quick_silence "$@"
            ;;
        preview)
            preview_silence "$@"
            ;;
        *)
            echo "AlertManager Silence Manager"
            echo ""
            echo "Usage: $0 [ACTION] [OPTIONS]"
            echo ""
            echo "Actions:"
            echo "  list                    List all silences"
            echo "  create <matchers>       Create a new silence"
            echo "  delete <silence-id>     Delete a specific silence"
            echo "  expire                  Expire all active silences"
            echo "  maintenance             Create maintenance window"
            echo "  quick <template> [args] Use quick silence template"
            echo "  preview <matchers>      Preview alerts that would be silenced"
            echo ""
            echo "Environment Variables:"
            echo "  NAMESPACE               Kubernetes namespace (default: monitoring)"
            echo "  DURATION                Silence duration (default: 1h)"
            echo "  COMMENT                 Silence comment"
            echo "  CREATED_BY              Creator name (default: silence-manager)"
            echo ""
            echo "Examples:"
            echo "  # List all silences"
            echo "  $0 list"
            echo ""
            echo "  # Create a 2-hour silence for namespace"
            echo "  DURATION=2h $0 create 'namespace=testing'"
            echo ""
            echo "  # Quick silence for node maintenance"
            echo "  $0 quick node worker-1"
            echo ""
            echo "  # Create maintenance window"
            echo "  MW_NAMESPACE=production MW_DURATION=4h $0 maintenance"
            echo ""
            echo "  # Preview what would be silenced"
            echo "  $0 preview 'severity=warning,namespace=default'"
            exit 0
            ;;
    esac
}

# Parse arguments
ACTION="${1:-list}"
shift || true

# Run main function
main "$@"
