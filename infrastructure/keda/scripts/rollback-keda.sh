#!/bin/bash
set -euo pipefail

# KEDA Emergency Rollback Script
# Quickly reverts to HPA-based autoscaling when KEDA issues are detected
# Preserves system stability by falling back to proven HPA configuration

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KEDA_DIR="$(dirname "$SCRIPT_DIR")"
NAMESPACE_KEDA="keda-system"
NAMESPACE_ARTEMIS="artemis-system"
NAMESPACE_SOPHIA="sophia-system"
HELM_RELEASE="sophia-intel-keda"

# Rollback options
PRESERVE_MONITORING="${PRESERVE_MONITORING:-true}"
BACKUP_BEFORE_ROLLBACK="${BACKUP_BEFORE_ROLLBACK:-true}"
FORCE_ROLLBACK="${FORCE_ROLLBACK:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging
LOG_FILE="/tmp/keda-rollback-$(date +%Y%m%d-%H%M%S).log"
exec 1> >(tee -a "$LOG_FILE")
exec 2>&1

log_info() { echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

# Backup current state before rollback
backup_current_state() {
    if [ "$BACKUP_BEFORE_ROLLBACK" != "true" ]; then
        log_info "Skipping backup (BACKUP_BEFORE_ROLLBACK=false)"
        return 0
    fi

    log_info "Backing up current KEDA configuration..."

    local backup_dir="/tmp/keda-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup ScaledObjects
    kubectl get scaledobjects -A -o yaml > "$backup_dir/scaledobjects.yaml" 2>/dev/null || true

    # Backup TriggerAuthentications
    kubectl get triggerauthentications -A -o yaml > "$backup_dir/triggerauths.yaml" 2>/dev/null || true

    # Backup KEDA operator configuration
    helm get values "$HELM_RELEASE" -n "$NAMESPACE_KEDA" > "$backup_dir/helm-values.yaml" 2>/dev/null || true

    # Backup current metrics
    kubectl top pods -A > "$backup_dir/pod-metrics.txt" 2>/dev/null || true
    kubectl get hpa -A > "$backup_dir/hpa-status.txt" 2>/dev/null || true

    log_success "Backup saved to $backup_dir"
    echo "$backup_dir" > /tmp/last-keda-backup-dir.txt
}

# Check if rollback is necessary
check_rollback_necessity() {
    if [ "$FORCE_ROLLBACK" = "true" ]; then
        log_warning "Force rollback requested (FORCE_ROLLBACK=true)"
        return 0
    fi

    log_info "Checking if rollback is necessary..."

    local issues_found=0

    # Check KEDA operator health
    local keda_ready=$(kubectl get pods -n "$NAMESPACE_KEDA" \
        -l app=keda-operator \
        -o jsonpath='{.items[0].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)

    if [ "$keda_ready" != "True" ]; then
        log_warning "KEDA operator is not healthy"
        ((issues_found++))
    fi

    # Check ScaledObject errors
    local scaledobject_errors=$(kubectl get scaledobjects -A \
        -o jsonpath='{.items[?(@.status.conditions[?(@.type=="Ready")].status!="True")].metadata.name}' 2>/dev/null | wc -w)

    if [ "$scaledobject_errors" -gt 0 ]; then
        log_warning "Found $scaledobject_errors ScaledObjects with errors"
        ((issues_found++))
    fi

    # Check circuit breaker status
    local circuit_breaker_triggered=$(kubectl get scaledobjects -A \
        -o jsonpath='{.items[*].metadata.annotations.keda\.sh/circuit-breaker-triggered}' 2>/dev/null | grep -c "true" || echo "0")

    if [ "$circuit_breaker_triggered" -gt 0 ]; then
        log_warning "Circuit breaker triggered on $circuit_breaker_triggered ScaledObjects"
        ((issues_found++))
    fi

    if [ "$issues_found" -eq 0 ]; then
        log_info "No critical issues found. Rollback may not be necessary."
        read -p "Continue with rollback anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Rollback cancelled by user"
            exit 0
        fi
    else
        log_warning "Found $issues_found critical issues. Proceeding with rollback."
    fi
}

# Step 1: Pause KEDA scaling
pause_keda_scaling() {
    log_info "Step 1: Pausing KEDA scaling activities..."

    # Annotate ScaledObjects to pause autoscaling
    kubectl get scaledobjects -A -o json | \
        jq '.items[] | "\(.metadata.namespace)/\(.metadata.name)"' -r | \
        while read -r scaledobject; do
            namespace=$(echo "$scaledobject" | cut -d'/' -f1)
            name=$(echo "$scaledobject" | cut -d'/' -f2)

            kubectl annotate scaledobject "$name" -n "$namespace" \
                autoscaling.keda.sh/paused="true" \
                --overwrite || true
        done

    log_success "KEDA scaling paused"
}

# Step 2: Enable HPA fallback
enable_hpa_fallback() {
    log_info "Step 2: Enabling HPA fallback..."

    # Artemis HPA
    if kubectl get hpa artemis-worker-hpa-backup -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        log_info "Enabling Artemis HPA fallback..."
        kubectl patch hpa artemis-worker-hpa-backup -n "$NAMESPACE_ARTEMIS" \
            --type='json' \
            -p='[{"op": "remove", "path": "/metadata/labels/type"}]' 2>/dev/null || true

        # Rename to primary HPA
        kubectl get hpa artemis-worker-hpa-backup -n "$NAMESPACE_ARTEMIS" -o yaml | \
            sed 's/artemis-worker-hpa-backup/artemis-worker-hpa/g' | \
            kubectl apply -f -
    else
        log_info "Creating new Artemis HPA..."
        cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: artemis-worker-hpa
  namespace: $NAMESPACE_ARTEMIS
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: artemis-worker
  minReplicas: 2
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
    fi

    # Sophia HPA
    if kubectl get hpa sophia-analytics-hpa-backup -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        log_info "Enabling Sophia HPA fallback..."
        kubectl patch hpa sophia-analytics-hpa-backup -n "$NAMESPACE_SOPHIA" \
            --type='json' \
            -p='[{"op": "remove", "path": "/metadata/labels/type"}]' 2>/dev/null || true

        # Rename to primary HPA
        kubectl get hpa sophia-analytics-hpa-backup -n "$NAMESPACE_SOPHIA" -o yaml | \
            sed 's/sophia-analytics-hpa-backup/sophia-analytics-hpa/g' | \
            kubectl apply -f -
    else
        log_info "Creating new Sophia HPA..."
        cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sophia-analytics-hpa
  namespace: $NAMESPACE_SOPHIA
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sophia-analytics
  minReplicas: 3
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
EOF
    fi

    log_success "HPA fallback enabled"
}

# Step 3: Remove ScaledObjects
remove_scaledobjects() {
    log_info "Step 3: Removing KEDA ScaledObjects..."

    # Delete ScaledObjects but preserve the deployments
    kubectl delete scaledobject artemis-scaler -n "$NAMESPACE_ARTEMIS" --ignore-not-found
    kubectl delete scaledobject sophia-scaler -n "$NAMESPACE_SOPHIA" --ignore-not-found
    kubectl delete scaledobject ai-workload-cron-scaler -n "$NAMESPACE_SOPHIA" --ignore-not-found

    # Remove any KEDA-created HPAs
    kubectl delete hpa -n "$NAMESPACE_ARTEMIS" -l app.kubernetes.io/managed-by=keda-operator --ignore-not-found
    kubectl delete hpa -n "$NAMESPACE_SOPHIA" -l app.kubernetes.io/managed-by=keda-operator --ignore-not-found

    log_success "ScaledObjects removed"
}

# Step 4: Uninstall KEDA operator (optional)
uninstall_keda_operator() {
    log_info "Step 4: Uninstalling KEDA operator..."

    read -p "Do you want to completely uninstall KEDA operator? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Keeping KEDA operator installed (can be re-enabled later)"
        return 0
    fi

    # Uninstall via Helm
    helm uninstall "$HELM_RELEASE" -n "$NAMESPACE_KEDA" || true

    # Clean up CRDs (careful - this removes all KEDA resources cluster-wide)
    read -p "Remove KEDA CRDs? This will delete ALL KEDA resources cluster-wide! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl delete crd scaledobjects.keda.sh --ignore-not-found
        kubectl delete crd scaledjobs.keda.sh --ignore-not-found
        kubectl delete crd triggerauthentications.keda.sh --ignore-not-found
        kubectl delete crd clustertriggerauthentications.keda.sh --ignore-not-found
    fi

    log_success "KEDA operator uninstalled"
}

# Step 5: Preserve monitoring (optional)
preserve_monitoring() {
    if [ "$PRESERVE_MONITORING" != "true" ]; then
        log_info "Removing monitoring components (PRESERVE_MONITORING=false)"
        kubectl delete prometheusrule keda-autoscaling-rules -n monitoring --ignore-not-found
        kubectl delete configmap keda-custom-metrics -n monitoring --ignore-not-found
        return 0
    fi

    log_info "Step 5: Preserving monitoring components..."

    # Update Prometheus rules to work without KEDA
    kubectl get prometheusrule keda-autoscaling-rules -n monitoring -o yaml 2>/dev/null | \
        sed 's/keda_/hpa_/g' | \
        kubectl apply -f - || true

    log_success "Monitoring components preserved"
}

# Verify rollback success
verify_rollback() {
    log_info "Verifying rollback success..."

    local success=true

    # Check HPA is working
    if ! kubectl get hpa artemis-worker-hpa -n "$NAMESPACE_ARTEMIS" &> /dev/null; then
        log_error "Artemis HPA not found"
        success=false
    fi

    if ! kubectl get hpa sophia-analytics-hpa -n "$NAMESPACE_SOPHIA" &> /dev/null; then
        log_error "Sophia HPA not found"
        success=false
    fi

    # Check deployments are still running
    local artemis_ready=$(kubectl get deployment artemis-worker -n "$NAMESPACE_ARTEMIS" \
        -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null)

    if [ "$artemis_ready" != "True" ]; then
        log_error "Artemis deployment is not available"
        success=false
    fi

    local sophia_ready=$(kubectl get deployment sophia-analytics -n "$NAMESPACE_SOPHIA" \
        -o jsonpath='{.status.conditions[?(@.type=="Available")].status}' 2>/dev/null)

    if [ "$sophia_ready" != "True" ]; then
        log_error "Sophia deployment is not available"
        success=false
    fi

    # Check no KEDA ScaledObjects remain
    local remaining_so=$(kubectl get scaledobjects -A 2>/dev/null | wc -l)
    if [ "$remaining_so" -gt 1 ]; then  # Header line counts as 1
        log_warning "Some ScaledObjects still remain"
    fi

    if [ "$success" = true ]; then
        log_success "Rollback verification passed"
        return 0
    else
        log_error "Rollback verification failed - manual intervention may be required"
        return 1
    fi
}

# Generate rollback report
generate_rollback_report() {
    log_info "Generating rollback report..."

    local report_file="/tmp/keda-rollback-report-$(date +%Y%m%d-%H%M%S).txt"

    cat > "$report_file" <<EOF
KEDA Rollback Report
====================
Date: $(date)
Initiated by: $(whoami)
Log file: $LOG_FILE

Current State:
--------------
EOF

    echo "HPAs:" >> "$report_file"
    kubectl get hpa -A | grep -E "artemis|sophia" >> "$report_file" 2>/dev/null || echo "None found" >> "$report_file"

    echo "" >> "$report_file"
    echo "Deployments:" >> "$report_file"
    kubectl get deployments -n "$NAMESPACE_ARTEMIS" >> "$report_file" 2>/dev/null
    kubectl get deployments -n "$NAMESPACE_SOPHIA" >> "$report_file" 2>/dev/null

    echo "" >> "$report_file"
    echo "KEDA Components:" >> "$report_file"
    kubectl get pods -n "$NAMESPACE_KEDA" 2>/dev/null >> "$report_file" || echo "KEDA namespace not found" >> "$report_file"

    echo "" >> "$report_file"
    echo "Backup Location:" >> "$report_file"
    cat /tmp/last-keda-backup-dir.txt 2>/dev/null >> "$report_file" || echo "No backup created" >> "$report_file"

    log_success "Rollback report saved to $report_file"
    cat "$report_file"
}

# Main rollback flow
main() {
    log_info "=== Starting KEDA Emergency Rollback ==="
    log_warning "This will revert autoscaling from KEDA to HPA"

    # Check if rollback is necessary
    check_rollback_necessity

    # Backup current state
    backup_current_state

    # Execute rollback steps
    pause_keda_scaling
    enable_hpa_fallback
    remove_scaledobjects

    # Optional: Uninstall KEDA
    uninstall_keda_operator

    # Preserve monitoring if requested
    preserve_monitoring

    # Verify rollback
    log_info "Waiting for system to stabilize..."
    sleep 30

    if verify_rollback; then
        log_success "=== KEDA Rollback Completed Successfully ==="
    else
        log_error "=== KEDA Rollback Completed with Warnings ==="
        log_warning "Please review the logs and manually verify system state"
    fi

    # Generate report
    generate_rollback_report

    log_info "Rollback log saved to: $LOG_FILE"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE_ROLLBACK="true"
            shift
            ;;
        --remove-monitoring)
            PRESERVE_MONITORING="false"
            shift
            ;;
        --no-backup)
            BACKUP_BEFORE_ROLLBACK="false"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --force              Force rollback without checking necessity"
            echo "  --remove-monitoring  Remove KEDA monitoring components"
            echo "  --no-backup         Skip backup before rollback"
            echo "  -h, --help          Show this help message"
            echo ""
            echo "This script performs an emergency rollback from KEDA to HPA-based autoscaling."
            echo "It preserves application stability by reverting to the proven HPA configuration."
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Confirm before proceeding
if [ "$FORCE_ROLLBACK" != "true" ]; then
    echo ""
    log_warning "This will rollback KEDA autoscaling to HPA. This action can be reversed by re-running the deployment script."
    read -p "Are you sure you want to proceed? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi
fi

# Run main rollback
main
