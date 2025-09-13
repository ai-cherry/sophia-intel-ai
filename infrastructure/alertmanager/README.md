# AlertManager Infrastructure for Sophia-Intel-AI

## Overview

Production-ready AlertManager implementation with intelligent alerting, 70% false positive reduction, and multi-channel notification support. This infrastructure provides high-availability alerting for the Sophia-Intel-AI platform with domain-specific routing for Sophia (real-time), Sophia (AI workloads), and Infrastructure components.

## Key Features

- **High Availability**: 3-node StatefulSet cluster with gossip protocol
- **Intelligent Routing**: Domain-based alert routing with smart grouping
- **False Positive Reduction**: Advanced inhibition rules and ML integration hooks
- **Multi-Channel Notifications**: Slack, PagerDuty, Email, Microsoft Teams
- **Security**: OAuth2 authentication, RBAC, NetworkPolicy isolation
- **GitOps Ready**: Full Kustomize overlays for dev/staging/prod
- **Observability**: Meta-monitoring with Prometheus and Grafana dashboards

## Architecture

```
┌─────────────────────────────────────────────┐
│           Prometheus Instances              │
└────────────────┬────────────────────────────┘
                 │ Alerts
                 ▼
    ┌────────────────────────────┐
    │   AlertManager HA Cluster   │
    │  ┌──────┐ ┌──────┐ ┌──────┐│
    │  │Node-0│ │Node-1│ │Node-2││
    │  └──────┘ └──────┘ └──────┘│
    │       Gossip Protocol       │
    └────────────┬────────────────┘
                 │ Routes
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌──────────┐
│Sophia │  │ Sophia │  │  Infra   │
│ Domain │  │ Domain │  │  Domain  │
└────────┘  └────────┘  └──────────┘
    │            │            │
    └────────────┼────────────┘
                 │ Notifications
    ┌────────────┼─────────────────┐
    ▼            ▼            ▼    ▼
┌──────┐    ┌──────┐    ┌──────┐ ┌──────┐
│Slack │    │Email │    │Pager │ │Teams │
└──────┘    └──────┘    │ Duty │ └──────┘
                        └──────┘
```

## Quick Start

### Prerequisites

- Kubernetes 1.24+
- kubectl configured
- ArgoCD installed (for GitOps deployment)
- Prometheus configured
- External Secrets Operator (for secret management)

### Deployment Methods

#### 1. GitOps with ArgoCD (Recommended)

```bash
# Apply ArgoCD application for production
kubectl apply -f infrastructure/alertmanager/gitops/argocd-application.yaml

# Monitor deployment
kubectl get app -n argocd alertmanager -w
```

#### 2. Helm Deployment

```bash
# Add helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Deploy using environment-specific values
helm upgrade --install alertmanager prometheus-community/alertmanager \
  -f infrastructure/alertmanager/helm/values.yaml \
  -f infrastructure/alertmanager/helm/values-prod.yaml \
  -n monitoring --create-namespace
```

#### 3. Script-based Deployment

```bash
# Deploy AlertManager
./infrastructure/alertmanager/scripts/deploy-alertmanager.sh production

# Configure notification channels
./infrastructure/alertmanager/scripts/configure-channels.sh

# Validate deployment
./infrastructure/alertmanager/scripts/validate-deployment.sh
```

## Configuration

### Alert Routing

The AlertManager uses domain-based routing with the following structure:

```yaml
routes:
  - match:
      domain: sophia
    receiver: sophia-critical
    group_by: ['alertname', 'cluster', 'service']
    
  - match:
      domain: sophia
    receiver: sophia-ai-team
    group_by: ['alertname', 'model', 'gpu_node']
    
  - match:
      domain: infrastructure
    receiver: infrastructure-team
    group_by: ['alertname', 'namespace']
```

### Notification Channels

Configure notification channels in `scripts/configure-channels.sh`:

```bash
# Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export SLACK_CHANNEL="#alerts"

# PagerDuty
export PAGERDUTY_SERVICE_KEY="your-service-key"
export PAGERDUTY_URL="https://events.pagerduty.com/v2/enqueue"

# Email
export EMAIL_SMTP_HOST="smtp.example.com"
export EMAIL_FROM="alerts@sophia-intel-ai.com"

# Teams
export TEAMS_WEBHOOK_URL="https://outlook.office.com/webhook/YOUR-WEBHOOK"
```

### Inhibition Rules

False positive reduction through intelligent inhibition:

```yaml
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']
```

## Testing

### Load Testing

Test AlertManager capacity (500 alerts/sec):

```bash
python infrastructure/alertmanager/tests/load-test.py \
  --alertmanager-url http://alertmanager:9093 \
  --rate 500 \
  --duration 60
```

### HA Failover Testing

Test cluster resilience:

```bash
./infrastructure/alertmanager/tests/ha-failover-test.sh
```

### Alert Routing Verification

Verify alert routing logic:

```bash
python infrastructure/alertmanager/tests/alert-routing-test.py
```

## Monitoring

### Grafana Dashboards

1. **AlertManager Dashboard**: Overall health and performance metrics
   - Import: `infrastructure/alertmanager/monitoring/grafana-dashboard.json`
   - Dashboard ID: `alertmanager-dashboard`

2. **SLA Dashboard**: Service level tracking and compliance
   - Import: `infrastructure/alertmanager/monitoring/sla-dashboard.json`
   - Dashboard ID: `alertmanager-sla`

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| `alertmanager_alerts_received_total` | Total alerts received | - |
| `alertmanager_notifications_total` | Total notifications sent | - |
| `alertmanager_notifications_failed_total` | Failed notifications | < 1% |
| `alertmanager_notification_latency_seconds` | Notification latency | P99 < 5s |
| `alertmanager_cluster_members` | Cluster member count | 3 |
| `up{job="alertmanager"}` | Instance availability | > 99.9% |

## Maintenance

### Silence Management

Create maintenance windows:

```bash
# Create 2-hour silence for specific alert
./infrastructure/alertmanager/scripts/silence-manager.sh create \
  --alert "HighMemoryUsage" \
  --duration 2h \
  --comment "Scheduled maintenance"

# List active silences
./infrastructure/alertmanager/scripts/silence-manager.sh list

# Expire silence
./infrastructure/alertmanager/scripts/silence-manager.sh expire <silence-id>
```

### Backup and Recovery

```bash
# Backup AlertManager data
kubectl exec -n monitoring alertmanager-0 -- \
  tar czf - /alertmanager | kubectl cp - ./backup-$(date +%Y%m%d).tar.gz

# Restore from backup
kubectl cp ./backup-20240101.tar.gz monitoring/alertmanager-0:/tmp/
kubectl exec -n monitoring alertmanager-0 -- \
  tar xzf /tmp/backup-20240101.tar.gz -C /
```

## Troubleshooting

### Common Issues

1. **Alerts not being received**
   ```bash
   # Check Prometheus targets
   kubectl port-forward -n monitoring svc/prometheus 9090:9090
   # Visit http://localhost:9090/targets
   
   # Check AlertManager config
   kubectl logs -n monitoring alertmanager-0 | grep -i error
   ```

2. **Notification failures**
   ```bash
   # Check notification logs
   kubectl logs -n monitoring alertmanager-0 | grep -i "notify"
   
   # Validate webhook URLs
   curl -X POST $SLACK_WEBHOOK_URL -d '{"text":"Test"}'
   ```

3. **Cluster communication issues**
   ```bash
   # Check cluster status
   kubectl exec -n monitoring alertmanager-0 -- \
     wget -qO- http://localhost:9093/api/v1/status | jq .data.cluster
   ```

## Performance Tuning

### Resource Optimization

```yaml
# Production settings (values-prod.yaml)
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2"
```

### Alert Grouping

Optimize notification batching:

```yaml
group_wait: 30s      # Initial wait before sending
group_interval: 5m   # Wait between batches
repeat_interval: 12h # Repeat if not resolved
```

## Security

### OAuth2 Authentication

Configured via OAuth2 Proxy:

```yaml
oauth2-proxy:
  provider: github
  github-org: sophia-intel-ai
  cookie-secure: true
  skip-auth-regex: "^/metrics"
```

### Network Policies

Strict ingress/egress controls:

```yaml
ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: prometheus
```

## Integration

### Prometheus Configuration

```yaml
# prometheus.yml
alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager-0.alertmanager-headless:9093
      - alertmanager-1.alertmanager-headless:9093
      - alertmanager-2.alertmanager-headless:9093
```

### KEDA Integration

AlertManager triggers KEDA scaling:

```yaml
triggers:
- type: prometheus
  metadata:
    query: |
      rate(alertmanager_alerts_received_total{
        severity="critical",
        domain="sophia"
      }[1m]) > 0.1
```

## License

Copyright 2024 Sophia-Intel-AI. All rights reserved.

## Support

- Documentation: [RUNBOOK.md](./RUNBOOK.md)
- Alert Catalog: [ALERT-CATALOG.md](./ALERT-CATALOG.md)
- Issues: https://github.com/sophia-intel-ai/infrastructure/issues
- Slack: #alertmanager-support