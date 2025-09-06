#!/bin/bash
set -euo pipefail

# KEDA Metrics Baseline Capture Script
# Records pre-deployment metrics for comparison
# Used to validate 85% improvement target (60s to 9s)

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE_ARTEMIS="artemis-system"
NAMESPACE_SOPHIA="sophia-system"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://prometheus.monitoring.svc.cluster.local:9090}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp/keda-metrics-baseline}"
BASELINE_DURATION="${BASELINE_DURATION:-300}"  # 5 minutes of baseline capture

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Create output directory
mkdir -p "$OUTPUT_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BASELINE_FILE="$OUTPUT_DIR/baseline-$TIMESTAMP.json"

# Initialize baseline data structure
initialize_baseline() {
    cat > "$BASELINE_FILE" <<EOF
{
  "metadata": {
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "duration_seconds": $BASELINE_DURATION,
    "environment": {
      "artemis_namespace": "$NAMESPACE_ARTEMIS",
      "sophia_namespace": "$NAMESPACE_SOPHIA",
      "prometheus_url": "$PROMETHEUS_URL"
    }
  },
  "baseline_metrics": {},
  "current_state": {},
  "performance_targets": {
    "scaling_time_seconds": 60,
    "target_scaling_time_seconds": 9,
    "improvement_percentage": 85
  }
}
EOF
}

# Capture current HPA metrics
capture_hpa_metrics() {
    log_info "Capturing HPA metrics..."

    local hpa_data='{"hpa_configurations": []}'

    # Artemis HPA
    if kubectl get hpa -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        local artemis_hpas=$(kubectl get hpa -n "$NAMESPACE_ARTEMIS" -o json | \
            jq -c '.items[] | {
                name: .metadata.name,
                min_replicas: .spec.minReplicas,
                max_replicas: .spec.maxReplicas,
                current_replicas: .status.currentReplicas,
                desired_replicas: .status.desiredReplicas,
                current_cpu: .status.currentMetrics[]? | select(.type=="Resource" and .resource.name=="cpu") | .resource.current.averageUtilization,
                target_cpu: .spec.metrics[]? | select(.type=="Resource" and .resource.name=="cpu") | .resource.target.averageUtilization
            }')

        if [ -n "$artemis_hpas" ]; then
            hpa_data=$(echo "$hpa_data" | jq --argjson data "$artemis_hpas" \
                '.hpa_configurations += [$data]')
        fi
    fi

    # Sophia HPA
    if kubectl get hpa -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        local sophia_hpas=$(kubectl get hpa -n "$NAMESPACE_SOPHIA" -o json | \
            jq -c '.items[] | {
                name: .metadata.name,
                min_replicas: .spec.minReplicas,
                max_replicas: .spec.maxReplicas,
                current_replicas: .status.currentReplicas,
                desired_replicas: .status.desiredReplicas,
                current_cpu: .status.currentMetrics[]? | select(.type=="Resource" and .resource.name=="cpu") | .resource.current.averageUtilization,
                target_cpu: .spec.metrics[]? | select(.type=="Resource" and .resource.name=="cpu") | .resource.target.averageUtilization
            }')

        if [ -n "$sophia_hpas" ]; then
            hpa_data=$(echo "$hpa_data" | jq --argjson data "$sophia_hpas" \
                '.hpa_configurations += [$data]')
        fi
    fi

    # Update baseline file
    jq --argjson hpa "$hpa_data" '.current_state.hpa = $hpa' "$BASELINE_FILE" > "$BASELINE_FILE.tmp" && \
        mv "$BASELINE_FILE.tmp" "$BASELINE_FILE"

    log_success "HPA metrics captured"
}

# Capture deployment metrics
capture_deployment_metrics() {
    log_info "Capturing deployment metrics..."

    local deployments='{"deployments": []}'

    # Artemis deployments
    local artemis_deps=$(kubectl get deployments -n "$NAMESPACE_ARTEMIS" -o json | \
        jq -c '.items[] | {
            name: .metadata.name,
            replicas: .spec.replicas,
            ready_replicas: .status.readyReplicas,
            available_replicas: .status.availableReplicas,
            updated_replicas: .status.updatedReplicas
        }')

    if [ -n "$artemis_deps" ]; then
        while IFS= read -r dep; do
            deployments=$(echo "$deployments" | jq --argjson data "$dep" \
                '.deployments += [$data]')
        done <<< "$artemis_deps"
    fi

    # Sophia deployments
    local sophia_deps=$(kubectl get deployments -n "$NAMESPACE_SOPHIA" -o json | \
        jq -c '.items[] | {
            name: .metadata.name,
            replicas: .spec.replicas,
            ready_replicas: .status.readyReplicas,
            available_replicas: .status.availableReplicas,
            updated_replicas: .status.updatedReplicas
        }')

    if [ -n "$sophia_deps" ]; then
        while IFS= read -r dep; do
            deployments=$(echo "$deployments" | jq --argjson data "$dep" \
                '.deployments += [$data]')
        done <<< "$sophia_deps"
    fi

    # Update baseline file
    jq --argjson deps "$deployments" '.current_state.deployments = $deps' "$BASELINE_FILE" > "$BASELINE_FILE.tmp" && \
        mv "$BASELINE_FILE.tmp" "$BASELINE_FILE"

    log_success "Deployment metrics captured"
}

# Capture resource utilization
capture_resource_metrics() {
    log_info "Capturing resource utilization metrics..."

    local resources='{"resource_utilization": {}}'

    # CPU utilization
    local cpu_usage=$(kubectl top pods -A --no-headers 2>/dev/null | \
        awk '{cpu+=$2; mem+=$3} END {print "{\"total_cpu_millicores\": "cpu", \"total_memory_mi\": "mem"}"}' || echo '{}')

    resources=$(echo "$resources" | jq --argjson cpu "$cpu_usage" '.resource_utilization.cluster = $cpu')

    # Node metrics
    local node_metrics=$(kubectl top nodes --no-headers 2>/dev/null | \
        awk '{print "{\"node\": \""$1"\", \"cpu_percent\": "$2", \"memory_percent\": "$4"}"}' | \
        jq -s '.' || echo '[]')

    resources=$(echo "$resources" | jq --argjson nodes "$node_metrics" '.resource_utilization.nodes = $nodes')

    # Update baseline file
    jq --argjson res "$resources" '.current_state.resources = $res' "$BASELINE_FILE" > "$BASELINE_FILE.tmp" && \
        mv "$BASELINE_FILE.tmp" "$BASELINE_FILE"

    log_success "Resource metrics captured"
}

# Query Prometheus for baseline metrics
query_prometheus_metrics() {
    log_info "Querying Prometheus for baseline metrics..."

    if ! command -v curl &> /dev/null; then
        log_warning "curl not available, skipping Prometheus metrics"
        return 0
    fi

    local prometheus_metrics='{}'

    # Define queries
    declare -A queries=(
        ["scaling_time_p95"]='histogram_quantile(0.95, sum(rate(container_runtime_crio_operations_latency_microseconds_bucket[5m])) by (le))'
        ["artemis_queue_length"]='redis_list_length{list="artemis:task:queue"}'
        ["sophia_processing_rate"]='sum(rate(sophia_analytics_events_processed_total[5m]))'
        ["pod_startup_time"]='avg(time() - kube_pod_start_time)'
        ["scale_events_rate"]='rate(kube_deployment_status_replicas[5m])'
        ["cpu_utilization"]='avg(rate(container_cpu_usage_seconds_total[5m]))'
        ["memory_utilization"]='avg(container_memory_working_set_bytes / container_spec_memory_limit_bytes)'
    )

    for metric_name in "${!queries[@]}"; do
        local query="${queries[$metric_name]}"
        local result=$(curl -s "$PROMETHEUS_URL/api/v1/query" \
            --data-urlencode "query=$query" 2>/dev/null | \
            jq -r '.data.result[0].value[1]' 2>/dev/null || echo "null")

        prometheus_metrics=$(echo "$prometheus_metrics" | \
            jq --arg name "$metric_name" --arg value "$result" \
            '.[$name] = ($value | tonumber? // null)')
    done

    # Update baseline file
    jq --argjson prom "$prometheus_metrics" '.baseline_metrics.prometheus = $prom' "$BASELINE_FILE" > "$BASELINE_FILE.tmp" && \
        mv "$BASELINE_FILE.tmp" "$BASELINE_FILE"

    log_success "Prometheus metrics captured"
}

# Capture scaling behavior over time
capture_scaling_behavior() {
    log_info "Capturing scaling behavior (this will take ${BASELINE_DURATION}s)..."

    local scaling_samples='{"samples": []}'
    local interval=10  # Sample every 10 seconds
    local iterations=$((BASELINE_DURATION / interval))

    for ((i=1; i<=iterations; i++)); do
        local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)

        # Get current replica counts
        local artemis_replicas=$(kubectl get deployment artemis-worker -n "$NAMESPACE_ARTEMIS" \
            -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")
        local sophia_replicas=$(kubectl get deployment sophia-analytics -n "$NAMESPACE_SOPHIA" \
            -o jsonpath='{.status.replicas}' 2>/dev/null || echo "0")

        # Create sample
        local sample=$(jq -n \
            --arg ts "$timestamp" \
            --arg ar "$artemis_replicas" \
            --arg sr "$sophia_replicas" \
            '{
                timestamp: $ts,
                artemis_replicas: ($ar | tonumber),
                sophia_replicas: ($sr | tonumber)
            }')

        scaling_samples=$(echo "$scaling_samples" | jq --argjson s "$sample" '.samples += [$s]')

        # Show progress
        echo -ne "\r  Progress: $i/$iterations samples collected"

        sleep $interval
    done
    echo ""  # New line after progress

    # Calculate statistics
    local stats=$(echo "$scaling_samples" | jq '
        .samples |
        {
            total_samples: length,
            artemis: {
                min: [.[] | .artemis_replicas] | min,
                max: [.[] | .artemis_replicas] | max,
                avg: ([.[] | .artemis_replicas] | add / length),
                changes: ([range(1; length) as $i | if .[$i].artemis_replicas != .[$i-1].artemis_replicas then 1 else 0 end] | add)
            },
            sophia: {
                min: [.[] | .sophia_replicas] | min,
                max: [.[] | .sophia_replicas] | max,
                avg: ([.[] | .sophia_replicas] | add / length),
                changes: ([range(1; length) as $i | if .[$i].sophia_replicas != .[$i-1].sophia_replicas then 1 else 0 end] | add)
            }
        }')

    # Update baseline file
    jq --argjson samples "$scaling_samples" --argjson stats "$stats" '
        .baseline_metrics.scaling_behavior = $samples |
        .baseline_metrics.scaling_statistics = $stats
    ' "$BASELINE_FILE" > "$BASELINE_FILE.tmp" && mv "$BASELINE_FILE.tmp" "$BASELINE_FILE"

    log_success "Scaling behavior captured"
}

# Generate baseline summary
generate_summary() {
    log_info "Generating baseline summary..."

    # Extract key metrics for summary
    local summary=$(jq '{
        metadata: .metadata,
        summary: {
            total_deployments: (.current_state.deployments.deployments | length),
            total_hpas: (.current_state.hpa.hpa_configurations | length),
            average_replicas: {
                artemis: .baseline_metrics.scaling_statistics.artemis.avg,
                sophia: .baseline_metrics.scaling_statistics.sophia.avg
            },
            scaling_events: {
                artemis: .baseline_metrics.scaling_statistics.artemis.changes,
                sophia: .baseline_metrics.scaling_statistics.sophia.changes
            },
            resource_utilization: .current_state.resources.resource_utilization.cluster,
            prometheus_metrics: .baseline_metrics.prometheus
        },
        performance_targets: .performance_targets
    }' "$BASELINE_FILE")

    # Save summary
    echo "$summary" | jq '.' > "$OUTPUT_DIR/baseline-summary-$TIMESTAMP.json"

    # Display summary
    echo ""
    echo "======================================"
    echo "METRICS BASELINE CAPTURE COMPLETE"
    echo "======================================"
    echo "Timestamp: $(date)"
    echo "Duration: ${BASELINE_DURATION}s"
    echo "--------------------------------------"
    echo "Deployments monitored: $(echo "$summary" | jq -r '.summary.total_deployments')"
    echo "HPAs monitored: $(echo "$summary" | jq -r '.summary.total_hpas')"
    echo "Average Artemis replicas: $(echo "$summary" | jq -r '.summary.average_replicas.artemis // 0' | xargs printf "%.1f")"
    echo "Average Sophia replicas: $(echo "$summary" | jq -r '.summary.average_replicas.sophia // 0' | xargs printf "%.1f")"
    echo "Artemis scaling events: $(echo "$summary" | jq -r '.summary.scaling_events.artemis // 0')"
    echo "Sophia scaling events: $(echo "$summary" | jq -r '.summary.scaling_events.sophia // 0')"
    echo "--------------------------------------"
    echo "Baseline saved to: $BASELINE_FILE"
    echo "Summary saved to: $OUTPUT_DIR/baseline-summary-$TIMESTAMP.json"
    echo "======================================"

    log_success "Baseline capture complete"
}

# Main execution
main() {
    log_info "Starting metrics baseline capture..."
    log_info "Output directory: $OUTPUT_DIR"

    # Initialize baseline file
    initialize_baseline

    # Capture current state
    capture_hpa_metrics
    capture_deployment_metrics
    capture_resource_metrics

    # Query Prometheus if available
    query_prometheus_metrics

    # Capture scaling behavior over time
    capture_scaling_behavior

    # Generate summary
    generate_summary

    # Return baseline file path for use by other scripts
    echo "$BASELINE_FILE"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output-dir|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --duration|-d)
            BASELINE_DURATION="$2"
            shift 2
            ;;
        --prometheus-url|-p)
            PROMETHEUS_URL="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -o, --output-dir DIR     Output directory for baseline files [default: /tmp/keda-metrics-baseline]"
            echo "  -d, --duration SECONDS   Duration to capture baseline [default: 300]"
            echo "  -p, --prometheus-url URL Prometheus URL [default: http://prometheus.monitoring.svc.cluster.local:9090]"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            log_warning "Unknown option: $1"
            shift
            ;;
    esac
done

# Run main function
main
