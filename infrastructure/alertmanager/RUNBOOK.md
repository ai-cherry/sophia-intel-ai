# AlertManager Operations Runbook

## Table of Contents

1. [Emergency Procedures](#emergency-procedures)
2. [Deployment Operations](#deployment-operations)
3. [Maintenance Tasks](#maintenance-tasks)
4. [Troubleshooting Guide](#troubleshooting-guide)
5. [Performance Tuning](#performance-tuning)
6. [Disaster Recovery](#disaster-recovery)
7. [Monitoring and Health Checks](#monitoring-and-health-checks)
8. [Common Scenarios](#common-scenarios)

## Emergency Procedures

### 🚨 AlertManager Complete Failure

**Symptoms**: No alerts being routed, all monitoring blind

**Immediate Actions**:
```bash
# 1. Check pod status
kubectl get pods -n monitoring -l app=alertmanager

# 2. If all pods are down, force restart
kubectl delete pods -n monitoring -l app=alertmanager

# 3. Check for persistent volume issues
kubectl get pvc -n monitoring

# 4. Emergency single-node deployment
kubectl apply -f infrastructure/alertmanager/emergency/single-node.yaml

# 5. Notify on-call team
./scripts/notify-emergency.sh "AlertManager down"
```

### 🔥 Alert Storm (> 1000 alerts/minute)

**Symptoms**: Notification channels overwhelmed, high latency

**Immediate Actions**:
```bash
# 1. Enable emergency rate limiting
kubectl exec -n monitoring alertmanager-0 -- \
  amtool silence add --duration="30m" \
  --comment="Emergency rate limit" \
  alertname=~".+"

# 2. Identify source
kubectl exec -n monitoring alertmanager-0 -- \
  amtool alert query --limit=100 | \
  jq -r '.[] | .labels.alertname' | sort | uniq -c | sort -rn

# 3. Apply targeted silence
./scripts/silence-manager.sh create \
  --alert "<problematic-alert>" \
  --duration 1h \
  --comment "Alert storm mitigation"

# 4. Scale up AlertManager
kubectl scale statefulset -n monitoring alertmanager --replicas=5
```

### 💔 Split Brain Cluster

**Symptoms**: Inconsistent alert routing, duplicate notifications

**Immediate Actions**:
```bash
# 1. Check cluster status
for i in 0 1 2; do
  kubectl exec -n monitoring alertmanager-$i -- \
    wget -qO- http://localhost:9093/api/v1/status | \
    jq .data.cluster
done

# 2. Identify partition
kubectl logs -n monitoring alertmanager-0 --tail=100 | grep cluster

# 3. Force cluster reformation
kubectl delete pod -n monitoring alertmanager-1
sleep 30
kubectl delete pod -n monitoring alertmanager-2

# 4. Verify cluster health
kubectl exec -n monitoring alertmanager-0 -- \
  amtool cluster show
```

## Deployment Operations

### Standard Deployment

```bash
# 1. Pre-deployment checks
./scripts/validate-deployment.sh --pre-check

# 2. Deploy to environment
./scripts/deploy-alertmanager.sh <environment>

# 3. Verify deployment
./scripts/validate-deployment.sh

# 4. Run smoke tests
./tests/smoke-test.sh

# 5. Monitor metrics for 10 minutes
watch -n 5 'kubectl top pods -n monitoring -l app=alertmanager'
```

### Rolling Update

```bash
# 1. Update configuration
kubectl create configmap alertmanager-config \
  --from-file=alertmanager.yml=config/alertmanager-config.yaml \
  --dry-run=client -o yaml | kubectl apply -f -

# 2. Trigger rolling update
kubectl rollout restart statefulset -n monitoring alertmanager

# 3. Monitor rollout
kubectl rollout status statefulset -n monitoring alertmanager

# 4. Verify all nodes joined cluster
kubectl exec -n monitoring alertmanager-0 -- amtool cluster show
```

### Rollback Procedure

```bash
# 1. Identify last working revision
kubectl rollout history statefulset -n monitoring alertmanager

# 2. Rollback to previous version
kubectl rollout undo statefulset -n monitoring alertmanager

# 3. Or rollback to specific revision
kubectl rollout undo statefulset -n monitoring alertmanager --to-revision=3

# 4. Verify rollback
kubectl get pods -n monitoring -l app=alertmanager -w
```

## Maintenance Tasks

### Daily Tasks

```bash
# Check cluster health
./scripts/daily-health-check.sh

# Review error logs
kubectl logs -n monitoring -l app=alertmanager --since=24h | grep ERROR

# Check disk usage
kubectl exec -n monitoring alertmanager-0 -- df -h /alertmanager

# Verify backup completion
kubectl get jobs -n monitoring | grep backup-alertmanager
```

### Weekly Tasks

```bash
# 1. Compact TSDB
for i in 0 1 2; do
  kubectl exec -n monitoring alertmanager-$i -- \
    curl -X POST http://localhost:9093/-/compact
done

# 2. Review and cleanup old silences
kubectl exec -n monitoring alertmanager-0 -- \
  amtool silence expire $(amtool silence query -q | grep -E "^[a-f0-9-]+")

# 3. Analyze notification metrics
./scripts/notification-report.sh --weekly

# 4. Update documentation
./scripts/generate-metrics-report.sh > reports/weekly-$(date +%Y%W).md
```

### Monthly Tasks

```bash
# 1. Certificate renewal check
./scripts/check-certificates.sh

# 2. Capacity planning review
./scripts/capacity-report.sh --monthly

# 3. Disaster recovery drill
./scripts/dr-drill.sh --dry-run

# 4. Update dependencies
helm dependency update infrastructure/alertmanager/helm/
```

## Troubleshooting Guide

### Issue: Alerts Not Firing

```bash
# 1. Check Prometheus configuration
kubectl get servicemonitor -n monitoring alertmanager -o yaml

# 2. Verify Prometheus can reach AlertManager
kubectl exec -n monitoring prometheus-0 -- \
  wget -qO- http://alertmanager:9093/metrics | head

# 3. Check alert rules are loaded
kubectl exec -n monitoring prometheus-0 -- \
  promtool query instant http://localhost:9090 "up"

# 4. Test alert pipeline
curl -X POST http://alertmanager:9093/api/v1/alerts \
  -d '[{"labels":{"alertname":"test","severity":"info"}}]'
```

### Issue: Notifications Not Sent

```bash
# 1. Check notification logs
kubectl logs -n monitoring alertmanager-0 | grep -i notify

# 2. Verify webhook URLs
kubectl get secret -n monitoring alertmanager-secrets -o yaml | \
  base64 -d

# 3. Test notification channel
kubectl exec -n monitoring alertmanager-0 -- \
  amtool config routes test \
  --config.file=/etc/alertmanager/alertmanager.yml

# 4. Check inhibition rules
kubectl exec -n monitoring alertmanager-0 -- \
  amtool alert query --inhibited
```

### Issue: High Memory Usage

```bash
# 1. Check memory consumption
kubectl top pods -n monitoring -l app=alertmanager

# 2. Analyze heap profile
kubectl exec -n monitoring alertmanager-0 -- \
  wget -qO- http://localhost:9093/debug/pprof/heap > heap.prof

# 3. Review alert grouping
kubectl exec -n monitoring alertmanager-0 -- \
  amtool alert groups

# 4. Adjust memory limits if needed
kubectl edit statefulset -n monitoring alertmanager
```

## Performance Tuning

### Optimize Alert Grouping

```yaml
# Adjust in alertmanager-config.yaml
global:
  group_wait: 30s      # Increase for fewer notifications
  group_interval: 5m   # Increase for batching
  repeat_interval: 12h # Increase to reduce repeats
```

### Cluster Performance

```bash
# 1. Optimize gossip settings
--cluster.gossip-interval=200ms  # Default: 200ms
--cluster.pushpull-interval=1m   # Default: 1m
--cluster.tcp-timeout=10s        # Default: 10s

# 2. Adjust peer timeouts
--cluster.peer-timeout=15s       # Default: 15s
--cluster.reconnect-timeout=5m   # Default: 5m
```

### Database Optimization

```bash
# 1. Set retention
--storage.retention=120h  # Keep 5 days of data

# 2. Enable compression
--storage.compression=snappy

# 3. Regular compaction
curl -X POST http://localhost:9093/-/compact
```

## Disaster Recovery

### Backup Procedures

```bash
# 1. Automated backup (runs daily)
kubectl apply -f infrastructure/alertmanager/backup/cronjob.yaml

# 2. Manual backup
./scripts/backup-alertmanager.sh

# 3. Verify backup
tar -tzf alertmanager-backup-$(date +%Y%m%d).tar.gz | head

# 4. Copy to offsite storage
aws s3 cp alertmanager-backup-*.tar.gz \
  s3://sophia-intel-backups/alertmanager/
```

### Restore Procedures

```bash
# 1. Stop AlertManager
kubectl scale statefulset -n monitoring alertmanager --replicas=0

# 2. Restore data
for i in 0 1 2; do
  kubectl cp backup.tar.gz monitoring/alertmanager-$i:/tmp/
  kubectl exec -n monitoring alertmanager-$i -- \
    tar -xzf /tmp/backup.tar.gz -C /alertmanager
done

# 3. Start AlertManager
kubectl scale statefulset -n monitoring alertmanager --replicas=3

# 4. Verify restoration
kubectl exec -n monitoring alertmanager-0 -- \
  amtool alert query
```

### Full Cluster Recovery

```bash
# 1. Deploy fresh cluster
kubectl apply -f infrastructure/alertmanager/base/

# 2. Restore configuration
kubectl create configmap alertmanager-config \
  --from-file=backup/alertmanager.yml

# 3. Restore secrets
kubectl apply -f backup/secrets.yaml

# 4. Restore data volumes
./scripts/restore-volumes.sh

# 5. Verify cluster formation
kubectl exec -n monitoring alertmanager-0 -- amtool cluster show
```

## Monitoring and Health Checks

### Health Check Endpoints

```bash
# Readiness check
curl http://alertmanager:9093/-/ready

# Liveness check
curl http://alertmanager:9093/-/healthy

# Metrics endpoint
curl http://alertmanager:9093/metrics

# API status
curl http://alertmanager:9093/api/v1/status
```

### Key Metrics to Monitor

| Metric | Alert Threshold | Check Command |
|--------|----------------|---------------|
| `up{job="alertmanager"}` | < 1 | `promtool query instant` |
| `alertmanager_cluster_members` | < 3 | `amtool cluster show` |
| `alertmanager_notifications_failed_total` | > 10/min | `amtool metrics` |
| `alertmanager_notification_latency_seconds` | P99 > 5s | `histogram_quantile` |
| `alertmanager_alerts` | > 1000 | `amtool alert query \| wc -l` |

### Dashboard Access

```bash
# Port forward Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000

# Access dashboards
# - AlertManager: http://localhost:3000/d/alertmanager-dashboard
# - SLA Tracking: http://localhost:3000/d/alertmanager-sla
```

## Common Scenarios

### Scenario: Planned Maintenance

```bash
# 1. Create silence for maintenance window
./scripts/silence-manager.sh create \
  --matcher "environment=production" \
  --duration 2h \
  --comment "Planned maintenance window"

# 2. Get silence ID
SILENCE_ID=$(amtool silence query -q | head -1)

# 3. Perform maintenance
# ... your maintenance tasks ...

# 4. Expire silence when done
./scripts/silence-manager.sh expire $SILENCE_ID
```

### Scenario: Adding New Alert Channel

```bash
# 1. Update configuration
vi config/alertmanager-config.yaml

# 2. Validate configuration
amtool check-config config/alertmanager-config.yaml

# 3. Apply configuration
kubectl create configmap alertmanager-config \
  --from-file=config/alertmanager-config.yaml \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Reload configuration
kubectl exec -n monitoring alertmanager-0 -- \
  kill -HUP 1

# 5. Test new channel
./scripts/test-notification.sh --channel=new-channel
```

### Scenario: Debugging Alert Routing

```bash
# 1. Test routing logic
amtool config routes test \
  --config.file=config/alertmanager-config.yaml \
  --labels="severity=critical,domain=artemis"

# 2. Show routing tree
amtool config routes show \
  --config.file=config/alertmanager-config.yaml

# 3. Trace specific alert
kubectl exec -n monitoring alertmanager-0 -- \
  amtool alert add \
  alertname=test severity=critical domain=artemis \
  --annotation=description="Test routing"
```

## Quick Reference

### Common Commands

```bash
# View all alerts
amtool alert query

# View grouped alerts
amtool alert groups

# Add silence
amtool silence add alertname=test --duration=1h

# Query silences
amtool silence query

# Expire silence
amtool silence expire <silence-id>

# Show cluster status
amtool cluster show

# Check configuration
amtool check-config <config-file>

# Reload configuration
kill -HUP 1  # Inside container
```

### Port Forwards

```bash
# AlertManager UI
kubectl port-forward -n monitoring svc/alertmanager 9093:9093

# Prometheus
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Grafana
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

### Log Locations

- AlertManager logs: `kubectl logs -n monitoring alertmanager-0`
- Configuration: `/etc/alertmanager/alertmanager.yml`
- Data directory: `/alertmanager`
- Silence data: `/alertmanager/silences`
- Notification log: `/alertmanager/notifications.log`

## Contact Information

- **On-Call Schedule**: https://pagerduty.sophia-intel-ai.com
- **Slack Channel**: #alertmanager-ops
- **Documentation**: https://docs.sophia-intel-ai.com/alertmanager
- **Issue Tracker**: https://jira.sophia-intel-ai.com/browse/ALERT

---
*Last Updated: 2024-01-15*
*Version: 1.0.0*