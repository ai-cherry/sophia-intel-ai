#!/bin/bash

# AlertManager Notification Channels Configuration Script
# Sets up and validates notification channels

set -e

# Configuration
NAMESPACE="${NAMESPACE:-monitoring}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://alertmanager.monitoring:9093}"
TEST_NOTIFICATIONS="${TEST_NOTIFICATIONS:-false}"

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

# Configure Slack
configure_slack() {
    log "Configuring Slack integration..."

    # Check if Slack webhook URL is set
    if kubectl get secret alertmanager-secrets -n "$NAMESPACE" &> /dev/null; then
        if kubectl get secret alertmanager-secrets -n "$NAMESPACE" -o jsonpath='{.data.slack-api-url}' &> /dev/null; then
            log "Slack webhook URL is configured ✓"

            # Test Slack notification if requested
            if [[ "$TEST_NOTIFICATIONS" == "true" ]]; then
                test_slack_notification
            fi
        else
            warning "Slack webhook URL not found in secrets"
            read -p "Enter Slack webhook URL (or press Enter to skip): " slack_url
            if [[ -n "$slack_url" ]]; then
                kubectl patch secret alertmanager-secrets -n "$NAMESPACE" \
                    --type='json' -p="[{\"op\": \"add\", \"path\": \"/data/slack-api-url\", \"value\":\"$(echo -n "$slack_url" | base64)\"}]"
                log "Slack webhook URL configured"
            fi
        fi
    else
        warning "AlertManager secrets not found"
    fi
}

# Configure PagerDuty
configure_pagerduty() {
    log "Configuring PagerDuty integration..."

    # Check PagerDuty service keys
    local pagerduty_keys=("pagerduty-sophia-key" "pagerduty-sophia-key" "pagerduty-platform-key" "pagerduty-infra-key" "pagerduty-security-key")

    for key in "${pagerduty_keys[@]}"; do
        if kubectl get secret alertmanager-secrets -n "$NAMESPACE" -o jsonpath="{.data.$key}" &> /dev/null; then
            log "PagerDuty key $key is configured ✓"
        else
            warning "PagerDuty key $key not found"
            read -p "Enter PagerDuty service key for ${key/pagerduty-/} (or press Enter to skip): " pd_key
            if [[ -n "$pd_key" ]]; then
                kubectl patch secret alertmanager-secrets -n "$NAMESPACE" \
                    --type='json' -p="[{\"op\": \"add\", \"path\": \"/data/$key\", \"value\":\"$(echo -n "$pd_key" | base64)\"}]"
                log "PagerDuty key $key configured"
            fi
        fi
    done

    if [[ "$TEST_NOTIFICATIONS" == "true" ]]; then
        test_pagerduty_notification
    fi
}

# Configure Email
configure_email() {
    log "Configuring Email (SMTP) integration..."

    # Check SMTP password
    if kubectl get secret alertmanager-secrets -n "$NAMESPACE" -o jsonpath='{.data.smtp-password}' &> /dev/null; then
        log "SMTP password is configured ✓"
    else
        warning "SMTP password not found"
        read -s -p "Enter SMTP password (or press Enter to skip): " smtp_pass
        echo
        if [[ -n "$smtp_pass" ]]; then
            kubectl patch secret alertmanager-secrets -n "$NAMESPACE" \
                --type='json' -p="[{\"op\": \"add\", \"path\": \"/data/smtp-password\", \"value\":\"$(echo -n "$smtp_pass" | base64)\"}]"
            log "SMTP password configured"
        fi
    fi

    # Verify SMTP configuration in ConfigMap
    local smtp_host=$(kubectl get configmap alertmanager-config -n "$NAMESPACE" \
        -o jsonpath='{.data.alertmanager\.yml}' | grep smtp_smarthost | cut -d: -f2- | tr -d ' ')

    if [[ -n "$smtp_host" ]]; then
        log "SMTP host configured: $smtp_host ✓"
    else
        warning "SMTP host not configured in alertmanager.yml"
    fi

    if [[ "$TEST_NOTIFICATIONS" == "true" ]]; then
        test_email_notification
    fi
}

# Configure Microsoft Teams
configure_teams() {
    log "Configuring Microsoft Teams integration..."

    # Check Teams webhook URLs
    local teams_webhooks=("teams-infrastructure-webhook" "teams-critical-webhook")

    for webhook in "${teams_webhooks[@]}"; do
        if kubectl get secret alertmanager-secrets -n "$NAMESPACE" -o jsonpath="{.data.$webhook}" &> /dev/null; then
            log "Teams webhook $webhook is configured ✓"
        else
            warning "Teams webhook $webhook not found"
            read -p "Enter Teams webhook URL for ${webhook/teams-/} (or press Enter to skip): " teams_url
            if [[ -n "$teams_url" ]]; then
                kubectl patch secret alertmanager-secrets -n "$NAMESPACE" \
                    --type='json' -p="[{\"op\": \"add\", \"path\": \"/data/$webhook\", \"value\":\"$(echo -n "$teams_url" | base64)\"}]"
                log "Teams webhook $webhook configured"
            fi
        fi
    done

    if [[ "$TEST_NOTIFICATIONS" == "true" ]]; then
        test_teams_notification
    fi
}

# Configure Webhooks
configure_webhooks() {
    log "Configuring Webhook receivers..."

    # Check MLOps webhook
    if kubectl get secret alertmanager-secrets -n "$NAMESPACE" -o jsonpath='{.data.mlops-webhook-url}' &> /dev/null; then
        log "MLOps webhook URL is configured ✓"
    else
        warning "MLOps webhook URL not found"
        read -p "Enter MLOps webhook URL (or press Enter to skip): " mlops_url
        if [[ -n "$mlops_url" ]]; then
            kubectl patch secret alertmanager-secrets -n "$NAMESPACE" \
                --type='json' -p="[{\"op\": \"add\", \"path\": \"/data/mlops-webhook-url\", \"value\":\"$(echo -n "$mlops_url" | base64)\"}]"
            log "MLOps webhook URL configured"
        fi
    fi
}

# Test Slack notification
test_slack_notification() {
    info "Testing Slack notification..."

    local test_alert='{
        "labels": {
            "alertname": "TestSlackNotification",
            "severity": "info",
            "test": "true"
        },
        "annotations": {
            "description": "This is a test notification from AlertManager configuration script"
        },
        "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "endsAt": "'$(date -u -d '+1 hour' +"%Y-%m-%dT%H:%M:%SZ")'"
    }'

    if curl -s -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "[$test_alert]" > /dev/null; then
        log "Test Slack notification sent ✓"
    else
        error "Failed to send test Slack notification"
    fi
}

# Test PagerDuty notification
test_pagerduty_notification() {
    info "Testing PagerDuty notification..."

    local test_alert='{
        "labels": {
            "alertname": "TestPagerDutyNotification",
            "severity": "critical",
            "domain": "platform",
            "test": "true"
        },
        "annotations": {
            "description": "This is a test PagerDuty notification - please acknowledge and resolve"
        },
        "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "endsAt": "'$(date -u -d '+5 minutes' +"%Y-%m-%dT%H:%M:%SZ")'"
    }'

    warning "This will create a real PagerDuty incident"
    read -p "Continue? (y/N): " confirm

    if [[ "$confirm" == "y" || "$confirm" == "Y" ]]; then
        if curl -s -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
            -H "Content-Type: application/json" \
            -d "[$test_alert]" > /dev/null; then
            log "Test PagerDuty notification sent ✓"
            info "Remember to resolve the test incident in PagerDuty"
        else
            error "Failed to send test PagerDuty notification"
        fi
    fi
}

# Test Email notification
test_email_notification() {
    info "Testing Email notification..."

    read -p "Enter test email address: " test_email

    if [[ -z "$test_email" ]]; then
        warning "No email address provided, skipping test"
        return
    fi

    local test_alert='{
        "labels": {
            "alertname": "TestEmailNotification",
            "severity": "warning",
            "test": "true",
            "email_to": "'$test_email'"
        },
        "annotations": {
            "description": "This is a test email notification from AlertManager"
        },
        "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "endsAt": "'$(date -u -d '+1 hour' +"%Y-%m-%dT%H:%M:%SZ")'"
    }'

    if curl -s -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "[$test_alert]" > /dev/null; then
        log "Test email notification sent to $test_email ✓"
    else
        error "Failed to send test email notification"
    fi
}

# Test Teams notification
test_teams_notification() {
    info "Testing Microsoft Teams notification..."

    local test_alert='{
        "labels": {
            "alertname": "TestTeamsNotification",
            "severity": "info",
            "domain": "infrastructure",
            "test": "true"
        },
        "annotations": {
            "description": "This is a test Teams notification from AlertManager"
        },
        "startsAt": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",
        "endsAt": "'$(date -u -d '+1 hour' +"%Y-%m-%dT%H:%M:%SZ")'"
    }'

    if curl -s -X POST "$ALERTMANAGER_URL/api/v1/alerts" \
        -H "Content-Type: application/json" \
        -d "[$test_alert]" > /dev/null; then
        log "Test Teams notification sent ✓"
    else
        error "Failed to send test Teams notification"
    fi
}

# Validate channel configuration
validate_channels() {
    log "Validating notification channels..."

    # Check AlertManager configuration
    local config_valid=$(kubectl exec -n "$NAMESPACE" \
        $(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}') -- \
        amtool config routes --config.file=/etc/alertmanager/alertmanager.yml 2>&1)

    if [[ $? -eq 0 ]]; then
        log "AlertManager configuration is valid ✓"
    else
        error "AlertManager configuration validation failed"
        echo "$config_valid"
        return 1
    fi

    # Check receivers
    local receivers=$(kubectl exec -n "$NAMESPACE" \
        $(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}') -- \
        amtool config routes show --config.file=/etc/alertmanager/alertmanager.yml 2>/dev/null | grep -c "Receiver:")

    log "Found $receivers configured receivers"

    return 0
}

# Main execution
main() {
    log "=========================================="
    log "AlertManager Channel Configuration"
    log "=========================================="
    log "Namespace: $NAMESPACE"
    log "URL: $ALERTMANAGER_URL"
    log ""

    # Check if AlertManager is running
    if ! kubectl get pods -n "$NAMESPACE" -l app=alertmanager | grep -q Running; then
        error "AlertManager is not running in namespace $NAMESPACE"
        exit 1
    fi

    # Configure each channel
    configure_slack
    configure_pagerduty
    configure_email
    configure_teams
    configure_webhooks

    # Validate configuration
    validate_channels

    # Reload AlertManager configuration
    log "Reloading AlertManager configuration..."
    kubectl exec -n "$NAMESPACE" \
        $(kubectl get pod -n "$NAMESPACE" -l app=alertmanager -o jsonpath='{.items[0].metadata.name}') -- \
        kill -HUP 1

    log ""
    log "=========================================="
    log "✅ Channel configuration completed!"
    log "=========================================="

    if [[ "$TEST_NOTIFICATIONS" == "true" ]]; then
        log ""
        log "Test notifications have been sent."
        log "Please check your notification channels to confirm receipt."
    else
        log ""
        log "To test notifications, run:"
        log "  TEST_NOTIFICATIONS=true $0"
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --test)
            TEST_NOTIFICATIONS="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --namespace <namespace>    Kubernetes namespace (default: monitoring)"
            echo "  --test                     Send test notifications"
            echo "  --help                     Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main
