# KEDA Troubleshooting Guide

## Common Issues and Solutions

### 1. KEDA Operator Not Starting

#### Symptoms
- KEDA operator pod in `CrashLoopBackOff` or `Error` state
- No metrics available
- ScaledObjects not being processed

#### Diagnosis
```bash
# Check pod status
kubectl get pods -n keda-system

# Check pod logs
kubectl logs -n keda-system deployment/keda-operator -f

# Check events
kubectl get events -n keda-system --sort-by='.lastTimestamp'
```

#### Solutions

**Issue: OOMKilled**
```bash
# Increase memory limits in values.yaml
kubectl edit deployment keda-operator -n keda-system
# Set resources.limits.memory: 2Gi
```

**Issue: RBAC permissions**
```bash
# Reapply RBAC configuration
kubectl apply -f base/rbac.yaml

# Verify ServiceAccount
kubectl get serviceaccount keda-operator -n keda-system
```

**Issue: Webhook certificate expired**
```bash
# Delete webhook configurations
kubectl delete validatingwebhookconfiguration keda-admission

# Restart operator to regenerate
kubectl rollout restart deployment/keda-operator -n keda-system
```

### 2. ScaledObject Not Scaling

#### Symptoms
- Deployment replicas not changing
- ScaledObject shows as "Not Ready"
- No HPA created

#### Diagnosis
```bash
# Check ScaledObject status
kubectl describe scaledobject artemis-scaler -n artemis-system

# Check HPA status
kubectl get hpa -n artemis-system

# Check metrics
kubectl get --raw /apis/external.metrics.k8s.io/v1beta1 | jq
```

#### Solutions

**Issue: Authentication failure**
```bash
# Check TriggerAuthentication
kubectl get triggerauthentication -n artemis-system

# Verify secrets exist
kubectl get secrets redis-credentials -n artemis-system

# Test connection manually
kubectl run redis-test --rm -it --image=redis:alpine -- redis-cli -h redis.artemis-system.svc.cluster.local ping
```

**Issue: Metrics not available**
```bash
# Check metrics server
kubectl get pods -n keda-system -l app=keda-operator-metrics-apiserver

# Test Prometheus query
curl "http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up"

# Verify ServiceMonitor
kubectl get servicemonitor -n keda-system
```

**Issue: Circuit breaker triggered**
```bash
# Check annotations
kubectl get scaledobject artemis-scaler -n artemis-system -o jsonpath='{.metadata.annotations}'

# Reset circuit breaker
kubectl annotate scaledobject artemis-scaler -n artemis-system keda.sh/circuit-breaker-triggered- --overwrite

# Monitor scale events
kubectl get events -n artemis-system | grep -i scale
```

### 3. Scaling Too Slow (Not Meeting 9s Target)

#### Symptoms
- Scaling takes longer than 9 seconds
- SLA violations in monitoring
- Performance degradation

#### Diagnosis
```bash
# Check current scaling time
./scripts/performance-benchmark.py --iterations 1 --profiles burst

# Review metrics
kubectl port-forward -n keda-system svc/keda-operator 8080:8080
curl http://localhost:8080/metrics | grep keda_scale_loop_duration_seconds

# Check polling intervals
kubectl get scaledobject artemis-scaler -n artemis-system -o jsonpath='{.spec.pollingInterval}'
```

#### Solutions

**Optimize polling interval**
```yaml
# Edit ScaledObject
spec:
  pollingInterval: 5  # Reduce from 10 to 5 seconds
  cooldownPeriod: 15  # Reduce from 30 to 15 seconds
```

**Reduce metrics latency**
```bash
# Check Prometheus scrape interval
kubectl get servicemonitor -n monitoring -o yaml | grep interval

# Optimize query performance
# Use recording rules for complex queries
kubectl apply -f monitoring/prometheus-rules.yaml
```

**Enable metrics caching**
```yaml
# In values.yaml
performance:
  metricsCacheDuration: 10s  # Cache metrics for 10 seconds
  scalerCheckInterval: 5s    # Check scalers every 5 seconds
```

### 4. Circuit Breaker Keeps Triggering

#### Symptoms
- Frequent fallback to HPA
- Alert: "KEDACircuitBreakerTriggered"
- More than 3 scale events per minute

#### Diagnosis
```bash
# Check scale event rate
kubectl get events -n artemis-system | grep -i scale | tail -20

# Monitor in real-time
watch -n 5 'kubectl get hpa -A'

# Check Prometheus metrics
curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(keda_scaled_object_events_total[1m])"
```

#### Solutions

**Adjust circuit breaker threshold**
```yaml
# Temporarily increase threshold
kubectl annotate scaledobject artemis-scaler -n artemis-system \
  keda.sh/max-scale-events=5 --overwrite
```

**Stabilize workload**
```yaml
# Increase stabilization window
spec:
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 120  # Increase from 60
        scaleUp:
          stabilizationWindowSeconds: 30   # Add delay to scale up
```

**Review scaling policies**
```yaml
# Make scaling less aggressive
spec:
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleUp:
          policies:
          - type: Percent
            value: 50  # Reduce from 100%
            periodSeconds: 30
```

### 5. Redis Connection Issues

#### Symptoms
- "connection refused" errors in logs
- Redis scaler shows "unknown" status
- Artemis not scaling

#### Diagnosis
```bash
# Test Redis connectivity
kubectl run redis-cli --rm -it --image=redis:alpine -n artemis-system -- \
  redis-cli -h redis.artemis-system.svc.cluster.local ping

# Check Redis service
kubectl get svc -n artemis-system | grep redis

# Verify network policy
kubectl get networkpolicy -n keda-system
```

#### Solutions

**Fix DNS resolution**
```bash
# Check CoreDNS
kubectl get pods -n kube-system | grep coredns

# Test DNS
kubectl run -it --rm debug --image=alpine --restart=Never -n keda-system -- \
  nslookup redis.artemis-system.svc.cluster.local
```

**Update network policy**
```yaml
# Allow Redis access
spec:
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: artemis-system
    ports:
    - protocol: TCP
      port: 6379
```

### 6. Prometheus Metrics Not Available

#### Symptoms
- Sophia scaler not working
- "no datapoints" in Prometheus queries
- Metrics API returns empty

#### Diagnosis
```bash
# Test Prometheus connectivity
kubectl run curl --rm -it --image=curlimages/curl -n sophia-system -- \
  curl http://prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up

# Check ServiceMonitor
kubectl get servicemonitor -n sophia-system

# Verify metrics are being scraped
curl -s "$PROMETHEUS_URL/api/v1/targets" | jq '.data.activeTargets[] | select(.labels.job=="sophia-analytics")'
```

#### Solutions

**Fix ServiceMonitor selector**
```yaml
# Ensure labels match
spec:
  selector:
    matchLabels:
      app: sophia-analytics  # Must match service labels
```

**Check bearer token**
```bash
# Verify secret exists
kubectl get secret prometheus-credentials -n sophia-system

# Recreate if needed
kubectl create secret generic prometheus-credentials \
  --from-literal=bearer-token="your-token" \
  -n sophia-system
```

### 7. Memory Leaks

#### Symptoms
- Gradual memory increase
- OOMKilled after running for hours
- Performance degradation over time

#### Diagnosis
```bash
# Monitor memory usage
kubectl top pods -n keda-system --watch

# Check for goroutine leaks
kubectl port-forward -n keda-system deployment/keda-operator 6060:6060
go tool pprof http://localhost:6060/debug/pprof/heap
```

#### Solutions

**Upgrade KEDA version**
```bash
# Check for known issues
# https://github.com/kedacore/keda/issues

# Upgrade if patch available
helm upgrade keda kedacore/keda --version 2.13.1 -n keda-system
```

**Implement resource limits**
```yaml
resources:
  limits:
    memory: 1Gi
  requests:
    memory: 128Mi
```

### 8. Cron Scaler Not Triggering

#### Symptoms
- Scheduled scaling not happening
- Wrong timezone
- Replicas not changing at scheduled times

#### Diagnosis
```bash
# Check current time in pod
kubectl exec -n keda-system deployment/keda-operator -- date

# Verify cron schedule
kubectl get scaledobject ai-workload-cron-scaler -n sophia-system -o yaml | grep -A5 cron

# Check timezone setting
kubectl get scaledobject ai-workload-cron-scaler -n sophia-system -o jsonpath='{.spec.triggers[*].metadata.timezone}'
```

#### Solutions

**Fix timezone**
```yaml
# Update ScaledObject
spec:
  triggers:
  - type: cron
    metadata:
      timezone: America/Los_Angeles  # Use IANA timezone
      start: "0 8 * * 1-5"  # 8 AM Monday-Friday
```

**Validate cron expression**
```bash
# Use crontab guru to validate
# https://crontab.guru/

# Test with simple schedule first
start: "*/5 * * * *"  # Every 5 minutes
```

## Performance Optimization Checklist

1. **Reduce Polling Interval**: Set to 5-10 seconds for critical workloads
2. **Optimize Metrics Queries**: Use recording rules for complex Prometheus queries
3. **Enable Metrics Caching**: Cache for 10-15 seconds to reduce API calls
4. **Tune HPA Behavior**: Adjust scale up/down policies
5. **Monitor Network Latency**: Ensure <50ms to Redis/Prometheus
6. **Resource Allocation**: Ensure KEDA has sufficient CPU/memory
7. **Use SSD Storage**: For etcd and Prometheus data

## Debugging Commands Reference

```bash
# Get all KEDA resources
kubectl get scaledobjects,scaledjobs,triggerauthentications -A

# Watch scaling in real-time
watch -n 2 'kubectl get hpa,deployment -A | grep -E "artemis|sophia"'

# Export KEDA metrics
kubectl port-forward -n keda-system svc/keda-operator 8080:8080 &
curl -s http://localhost:8080/metrics > keda-metrics.txt

# Check KEDA operator version
kubectl get deployment keda-operator -n keda-system -o jsonpath='{.spec.template.spec.containers[0].image}'

# Force ScaledObject reconciliation
kubectl annotate scaledobject artemis-scaler -n artemis-system \
  reconcile="$(date +%s)" --overwrite

# Get detailed ScaledObject status
kubectl get scaledobject artemis-scaler -n artemis-system -o json | \
  jq '.status'

# Test external metrics API
kubectl get --raw "/apis/external.metrics.k8s.io/v1beta1/namespaces/artemis-system/redis_list_length"

# Check KEDA webhook logs
kubectl logs -n keda-system -l app=keda-admission-webhooks -f
```

## Emergency Contacts

- **Platform Team Lead**: platform-lead@sophia-intel-ai.com
- **On-Call Engineer**: See PagerDuty
- **Slack Channel**: #platform-keda-help
- **Escalation**: Follow RUNBOOK.md procedures

---

**Last Updated**: 2025-01-06  
**Version**: 1.0.0  
**Related**: [README.md](README.md) | [RUNBOOK.md](RUNBOOK.md)