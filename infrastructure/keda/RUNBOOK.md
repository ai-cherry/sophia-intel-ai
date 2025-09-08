# KEDA Operations Runbook

## Table of Contents
1. [Critical Information](#critical-information)
2. [Deployment Procedures](#deployment-procedures)
3. [Monitoring & Alerts](#monitoring--alerts)
4. [Incident Response](#incident-response)
5. [Maintenance Procedures](#maintenance-procedures)
6. [Emergency Procedures](#emergency-procedures)
7. [Performance Tuning](#performance-tuning)
8. [Disaster Recovery](#disaster-recovery)

## Critical Information

### Key Metrics
- **Target Scaling Time**: 9 seconds (85% improvement from 60s)
- **Circuit Breaker Threshold**: 3 scale events/minute
- **SLA**: 99.9% availability
- **RPO**: 15 minutes
- **RTO**: 30 minutes

### Component Locations
| Component | Namespace | Service |
|-----------|-----------|---------|
| KEDA Operator | keda-system | keda-operator |
| Metrics Server | keda-system | keda-operator-metrics-apiserver |
| Artemis Scaler | artemis-system | artemis-scaler |
| Sophia Scaler | sophia-system | sophia-scaler |
| Prometheus | monitoring | prometheus |
| Redis | artemis-system | redis |

### Access Requirements
- Kubernetes cluster admin access
- Prometheus query access
- PagerDuty for alerts
- Slack #platform-keda channel

## Deployment Procedures

### Standard Deployment

#### Pre-deployment Checklist
- [ ] Review change request ticket
- [ ] Verify testing completed in staging
- [ ] Check maintenance window
- [ ] Notify stakeholders
- [ ] Capture baseline metrics

#### Deployment Steps

1. **Capture baseline metrics**
```bash
./scripts/metrics-baseline.sh -o /tmp/baseline-$(date +%Y%m%d-%H%M%S)
```

2. **Deploy to environment**
```bash
# Development
./scripts/deploy-keda.sh --environment dev

# Staging (with canary)
./scripts/deploy-keda.sh --environment staging --rollout-strategy canary

# Production (manual approval required)
./scripts/deploy-keda.sh --environment prod --skip-tests
```

3. **Validate deployment**
```bash
./scripts/validate-deployment.sh

# Expected output:
# ✅ VALIDATION PASSED (>90% success rate)
```

4. **Run smoke tests**
```bash
# Quick performance check
python3 tests/performance-benchmark.py --iterations 3 --profiles burst

# Integration test
./tests/integration-test.sh
```

5. **Monitor for 30 minutes**
```bash
# Watch key metrics
watch -n 10 'kubectl get hpa,scaledobjects -A | grep -E "artemis|sophia"'

# Check Prometheus alerts
curl -s "$PROMETHEUS_URL/api/v1/alerts" | jq '.data.alerts[] | select(.labels.component=="keda")'
```

### Rollback Procedure

#### When to Rollback
- Scaling time exceeds 15 seconds consistently
- Circuit breaker triggers more than 5 times in 10 minutes
- Critical alerts firing for >5 minutes
- Application performance degraded by >20%

#### Rollback Steps

1. **Initiate rollback**
```bash
# Standard rollback with backup
./scripts/rollback-keda.sh

# Emergency rollback (skip all checks)
./scripts/rollback-keda.sh --force --no-backup
```

2. **Verify HPA takeover**
```bash
kubectl get hpa -n artemis-system
kubectl get hpa -n sophia-system
```

3. **Notify stakeholders**
```bash
# Send notification
echo "KEDA rollback completed at $(date). HPAs active." | \
  slack-cli send --channel platform-keda
```

## Monitoring & Alerts

### Key Dashboards
- **Grafana**: https://grafana.sophia-intel-ai.com/d/keda-performance
- **Prometheus**: https://prometheus.sophia-intel-ai.com
- **Artemis Dashboard**: https://artemis.sophia-intel-ai.com (KEDA tab)

### Alert Response Matrix

| Alert | Severity | Response Time | Action |
|-------|----------|---------------|--------|
| KEDAOperatorDown | Critical | 5 min | [Restart operator](#keda-operator-down) |
| KEDACircuitBreakerTriggered | Critical | 10 min | [Reset circuit breaker](#circuit-breaker-triggered) |
| KEDAScalingTimeExceeded | High | 15 min | [Optimize scaling](#scaling-too-slow) |
| KEDAScalerErrors | Medium | 30 min | [Check scaler config](#scaler-errors) |
| KEDAOverScaling | Low | 1 hour | [Review thresholds](#over-scaling) |

## Incident Response

### KEDA Operator Down

**Impact**: No autoscaling, fallback to HPA if configured

**Detection**:
- Alert: `KEDAOperatorDown`
- Symptoms: Pods not scaling, ScaledObjects showing errors

**Response**:
```bash
# 1. Check pod status
kubectl get pods -n keda-system -l app=keda-operator

# 2. Check logs for errors
kubectl logs -n keda-system deployment/keda-operator --tail=100

# 3. Restart operator
kubectl rollout restart deployment/keda-operator -n keda-system

# 4. If persistent, check resources
kubectl describe pod -n keda-system -l app=keda-operator

# 5. Scale manually if needed
kubectl scale deployment artemis-worker --replicas=10 -n artemis-system
```

### Circuit Breaker Triggered

**Impact**: KEDA disabled, HPA active

**Detection**:
- Alert: `KEDACircuitBreakerTriggered`
- Dashboard shows circuit breaker status: "Triggered"

**Response**:
```bash
# 1. Check scale event rate
kubectl get events -n artemis-system | grep -i scale | tail -20

# 2. Identify cause
curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(keda_scaled_object_events_total[1m])"

# 3. Stabilize workload
kubectl patch scaledobject artemis-scaler -n artemis-system --type='json' \
  -p='[{"op": "replace", "path": "/spec/pollingInterval", "value": 20}]'

# 4. Reset circuit breaker
kubectl annotate scaledobject artemis-scaler -n artemis-system \
  keda.sh/circuit-breaker-triggered- --overwrite

# 5. Monitor recovery
watch -n 5 'kubectl get scaledobject artemis-scaler -n artemis-system -o jsonpath="{.status.conditions}"'
```

### Scaling Too Slow

**Impact**: SLA violation, performance degradation

**Detection**:
- Alert: `KEDATargetScalingTimeExceeded`
- Scaling time >9 seconds

**Response**:
```bash
# 1. Check current performance
./scripts/performance-benchmark.py --iterations 1 --profiles burst

# 2. Reduce polling interval
kubectl patch scaledobject artemis-scaler -n artemis-system \
  --type merge -p '{"spec":{"pollingInterval":5}}'

# 3. Check metrics latency
kubectl exec -n artemis-system deployment/artemis-worker -- \
  redis-cli -h redis.artemis-system.svc.cluster.local --latency

# 4. Optimize Prometheus queries
kubectl apply -f monitoring/prometheus-rules.yaml

# 5. Enable metrics caching
kubectl patch configmap keda-config -n keda-system \
  --type merge -p '{"data":{"metricsCacheDuration":"15s"}}'
```

### Scaler Errors

**Impact**: Specific scaler not functioning

**Detection**:
- Alert: `KEDAScalerErrors`
- ScaledObject shows errors

**Response**:
```bash
# 1. Identify failing scaler
kubectl get scaledobjects -A -o json | \
  jq '.items[] | select(.status.conditions[].status=="False") | .metadata'

# 2. Check authentication
kubectl get triggerauthentication -A
kubectl get secrets -n artemis-system | grep credentials

# 3. Test connectivity
# For Redis
kubectl run redis-test --rm -it --image=redis:alpine -n artemis-system -- \
  redis-cli -h redis.artemis-system.svc.cluster.local ping

# For Prometheus
kubectl run curl-test --rm -it --image=curlimages/curl -n sophia-system -- \
  curl http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up

# 4. Recreate ScaledObject if needed
kubectl delete scaledobject artemis-scaler -n artemis-system
kubectl apply -f scalers/artemis-scaledobject.yaml
```

### Over-Scaling

**Impact**: Increased costs, resource waste

**Detection**:
- Alert: `KEDAOverScaling`
- Replicas consistently at max

**Response**:
```bash
# 1. Review current thresholds
kubectl get scaledobject artemis-scaler -n artemis-system -o yaml | grep -A5 threshold

# 2. Analyze workload patterns
curl -s "$PROMETHEUS_URL/api/v1/query_range?query=redis_list_length" \
  --data-urlencode 'start=-1h' \
  --data-urlencode 'end=now' \
  --data-urlencode 'step=1m'

# 3. Adjust thresholds
kubectl patch scaledobject artemis-scaler -n artemis-system --type='json' \
  -p='[{"op": "replace", "path": "/spec/triggers/0/metadata/listLength", "value": "20"}]'

# 4. Update max replicas
kubectl patch scaledobject artemis-scaler -n artemis-system \
  --type merge -p '{"spec":{"maxReplicaCount":30}}'
```

## Maintenance Procedures

### Weekly Tasks

1. **Review scaling metrics**
```bash
# Generate weekly report
python3 tests/performance-benchmark.py --iterations 5 > weekly-report-$(date +%Y%W).txt
```

2. **Check for updates**
```bash
# Check KEDA releases
helm search repo kedacore/keda --versions | head -5

# Check for security advisories
kubectl get events -A | grep -i security
```

3. **Validate backups**
```bash
# Test HPA fallback
kubectl annotate scaledobject artemis-scaler -n artemis-system \
  test-fallback="$(date +%s)" --overwrite
```

### Monthly Tasks

1. **Update documentation**
- Review and update runbook procedures
- Update troubleshooting guide with new issues
- Document any configuration changes

2. **Capacity planning**
```bash
# Analyze scaling trends
./scripts/metrics-baseline.sh -d 2592000  # 30 days
```

3. **Security audit**
```bash
# Check RBAC
kubectl auth can-i --list --as=system:serviceaccount:keda-system:keda-operator

# Review network policies
kubectl get networkpolicies -n keda-system -o yaml
```

## Emergency Procedures

### Complete System Failure

1. **Immediate response**
```bash
# Scale critical workloads manually
kubectl scale deployment artemis-worker --replicas=20 -n artemis-system
kubectl scale deployment sophia-analytics --replicas=30 -n sophia-system
```

2. **Enable HPA fallback**
```bash
# Apply emergency HPA configuration
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: emergency-artemis-hpa
  namespace: artemis-system
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: artemis-worker
  minReplicas: 10
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
EOF
```

3. **Page on-call engineer**
```bash
# Trigger PagerDuty
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key": "YOUR_ROUTING_KEY",
    "event_action": "trigger",
    "payload": {
      "summary": "KEDA Complete Failure - Manual Intervention Required",
      "severity": "critical",
      "source": "keda-runbook",
      "component": "keda-system"
    }
  }'
```

### Data Loss Recovery

1. **Restore from backup**
```bash
# Restore ScaledObject configurations
kubectl apply -f /backup/keda/scaledobjects/

# Restore secrets
kubectl apply -f /backup/keda/secrets/
```

2. **Recalibrate metrics**
```bash
# Reset Prometheus recording rules
kubectl delete prometheusrule keda-autoscaling-rules -n monitoring
kubectl apply -f monitoring/prometheus-rules.yaml

# Clear metrics cache
kubectl delete pod -n keda-system -l app=keda-operator-metrics-apiserver
```

## Performance Tuning

### Optimization Checklist

- [ ] Polling interval: 5-10s for critical, 15-30s for others
- [ ] Cooldown period: 15-30s to prevent flapping
- [ ] Metrics cache: 10-15s to reduce API calls
- [ ] Recording rules for complex Prometheus queries
- [ ] Network latency <50ms to data sources
- [ ] CPU requests: 100m minimum for operator
- [ ] Memory limits: 1Gi for operator, 512Mi for metrics server

### Performance Testing

```bash
# Run comprehensive benchmark
python3 tests/performance-benchmark.py \
  --iterations 10 \
  --profiles burst gradual sustained wave realistic \
  --target-time 9

# Load test with monitoring
python3 tests/load-test.py --redis-host redis.artemis-system.svc.cluster.local \
  --pattern comprehensive \
  --test-duration 600
```

## Disaster Recovery

### Backup Procedures

1. **Daily backups**
```bash
# Backup KEDA configurations
kubectl get scaledobjects,triggerauthentications -A -o yaml > \
  /backup/keda/daily-$(date +%Y%m%d).yaml

# Backup Helm values
helm get values sophia-intel-keda -n keda-system > \
  /backup/keda/helm-values-$(date +%Y%m%d).yaml
```

2. **Test restore procedures quarterly**
```bash
# Restore in test cluster
kubectl apply -f /backup/keda/daily-20250106.yaml
```

### Recovery Time Objectives

| Scenario | RTO | RPO | Procedure |
|----------|-----|-----|-----------|
| Operator failure | 5 min | 0 | Automatic restart |
| Configuration loss | 15 min | 1 hour | Restore from backup |
| Complete failure | 30 min | 15 min | Rollback to HPA |
| Cluster disaster | 4 hours | 1 hour | Restore in new cluster |

## Escalation Matrix

| Level | Time | Contact | Criteria |
|-------|------|---------|----------|
| L1 | 0-15 min | On-call engineer | Any critical alert |
| L2 | 15-30 min | Platform team lead | Multiple components affected |
| L3 | 30-60 min | Engineering manager | Customer impact detected |
| L4 | 60+ min | VP Engineering | Service degradation >30 min |

### Contact Information

- **On-Call**: PagerDuty rotation `platform-keda`
- **Slack**: #platform-keda (urgent: #platform-emergency)
- **Email**: platform-team@sophia-intel-ai.com
- **War Room**: https://meet.sophia-intel-ai.com/emergency

---

**Last Updated**: 2025-01-06  
**Version**: 1.0.0  
**Review Schedule**: Monthly  
**Owner**: Platform Team