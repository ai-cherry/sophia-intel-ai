# AlertManager Alert Catalog

## Overview

This catalog documents all alert definitions configured in the Sophia-Intel-AI AlertManager infrastructure. Alerts are organized by domain (Artemis, Sophia, Infrastructure) with detailed information about triggers, severity, and response procedures.

## Alert Severity Levels

| Level | Response Time | Notification | Auto-Escalation |
|-------|--------------|--------------|-----------------|
| **Critical** | < 5 minutes | PagerDuty + Slack | Yes (15 min) |
| **Warning** | < 30 minutes | Slack + Email | Yes (2 hours) |
| **Info** | < 4 hours | Email | No |

## Domain: Artemis (Real-time Trading)

### ART-001: ArtemisHighLatency
- **Severity**: Critical
- **Threshold**: P99 latency > 100ms for 5 minutes
- **Description**: Trading engine latency exceeds acceptable threshold
- **Impact**: Potential trading losses, SLA violations
- **Remediation**:
  1. Check load balancer distribution
  2. Review recent deployments
  3. Scale up if CPU > 80%
  4. Check database query performance
- **Runbook**: [artemis-latency.md](./runbooks/artemis-latency.md)

### ART-002: ArtemisOrderProcessingFailure
- **Severity**: Critical
- **Threshold**: Error rate > 0.1% for 2 minutes
- **Description**: Order processing failures detected
- **Impact**: Failed trades, customer impact
- **Remediation**:
  1. Check order validation logs
  2. Verify external API connectivity
  3. Review circuit breaker status
  4. Rollback if recent deployment
- **Runbook**: [artemis-order-failure.md](./runbooks/artemis-order-failure.md)

### ART-003: ArtemisConnectionPoolExhaustion
- **Severity**: Warning
- **Threshold**: Available connections < 10% for 10 minutes
- **Description**: Database connection pool near exhaustion
- **Impact**: Potential service degradation
- **Remediation**:
  1. Check for connection leaks
  2. Review slow queries
  3. Increase pool size if needed
  4. Restart affected pods
- **Runbook**: [artemis-connection-pool.md](./runbooks/artemis-connection-pool.md)

### ART-004: ArtemisMemoryPressure
- **Severity**: Warning
- **Threshold**: Memory usage > 85% for 15 minutes
- **Description**: High memory usage in Artemis pods
- **Impact**: Potential OOM kills, performance degradation
- **Remediation**:
  1. Check for memory leaks
  2. Review heap dumps
  3. Scale horizontally
  4. Increase memory limits
- **Runbook**: [artemis-memory.md](./runbooks/artemis-memory.md)

### ART-005: ArtemisAPIRateLimit
- **Severity**: Warning
- **Threshold**: Rate limit hits > 100/min for 5 minutes
- **Description**: API rate limiting triggered frequently
- **Impact**: Client request throttling
- **Remediation**:
  1. Identify high-volume clients
  2. Review rate limit settings
  3. Consider quota adjustments
  4. Enable caching if applicable
- **Runbook**: [artemis-rate-limit.md](./runbooks/artemis-rate-limit.md)

## Domain: Sophia (AI Workloads)

### SOF-001: SophiaGPUUtilization
- **Severity**: Warning
- **Threshold**: GPU utilization < 50% for 30 minutes
- **Description**: Underutilized GPU resources
- **Impact**: Wasted compute resources, increased costs
- **Remediation**:
  1. Review batch sizes
  2. Check model optimization
  3. Consider workload consolidation
  4. Adjust resource allocation
- **Runbook**: [sophia-gpu-util.md](./runbooks/sophia-gpu-util.md)

### SOF-002: SophiaModelInferenceTimeout
- **Severity**: Critical
- **Threshold**: Inference time > 30s for 5 requests
- **Description**: Model inference exceeding timeout
- **Impact**: Request failures, poor user experience
- **Remediation**:
  1. Check model complexity
  2. Review input size
  3. Verify GPU availability
  4. Consider model optimization
- **Runbook**: [sophia-inference-timeout.md](./runbooks/sophia-inference-timeout.md)

### SOF-003: SophiaTrainingJobFailure
- **Severity**: Warning
- **Threshold**: Job failure rate > 10% in 1 hour
- **Description**: High training job failure rate
- **Impact**: Delayed model updates, resource waste
- **Remediation**:
  1. Check dataset integrity
  2. Review OOM errors
  3. Verify checkpoint saves
  4. Check distributed training setup
- **Runbook**: [sophia-training-failure.md](./runbooks/sophia-training-failure.md)

### SOF-004: SophiaModelDrift
- **Severity**: Warning
- **Threshold**: Accuracy drop > 5% from baseline
- **Description**: Model performance degradation detected
- **Impact**: Reduced prediction quality
- **Remediation**:
  1. Review recent data changes
  2. Check for data drift
  3. Consider retraining
  4. Validate preprocessing pipeline
- **Runbook**: [sophia-model-drift.md](./runbooks/sophia-model-drift.md)

### SOF-005: SophiaDataPipelineBacklog
- **Severity**: Warning
- **Threshold**: Queue depth > 10000 messages for 20 minutes
- **Description**: Data processing pipeline backlog
- **Impact**: Delayed processing, potential data loss
- **Remediation**:
  1. Scale processing workers
  2. Check for processing errors
  3. Review message sizes
  4. Optimize processing logic
- **Runbook**: [sophia-pipeline-backlog.md](./runbooks/sophia-pipeline-backlog.md)

## Domain: Infrastructure

### INF-001: NodeMemoryPressure
- **Severity**: Critical
- **Threshold**: Available memory < 10% for 5 minutes
- **Description**: Kubernetes node under memory pressure
- **Impact**: Pod evictions, service disruptions
- **Remediation**:
  1. Identify memory-intensive pods
  2. Trigger pod migrations
  3. Add new nodes if needed
  4. Review resource requests/limits
- **Runbook**: [infra-node-memory.md](./runbooks/infra-node-memory.md)

### INF-002: PersistentVolumeSpaceExhaustion
- **Severity**: Critical
- **Threshold**: Available space < 10% for any PV
- **Description**: Persistent volume running out of space
- **Impact**: Write failures, data loss risk
- **Remediation**:
  1. Identify volume usage
  2. Clean up old data/logs
  3. Expand volume if possible
  4. Migrate to larger volume
- **Runbook**: [infra-pv-space.md](./runbooks/infra-pv-space.md)

### INF-003: CertificateExpiry
- **Severity**: Warning
- **Threshold**: Certificate expires in < 30 days
- **Description**: TLS certificate approaching expiration
- **Impact**: Service unavailability after expiry
- **Remediation**:
  1. Verify cert-manager status
  2. Check renewal process
  3. Manual renewal if needed
  4. Update DNS if required
- **Runbook**: [infra-cert-expiry.md](./runbooks/infra-cert-expiry.md)

### INF-004: EtcdHighLatency
- **Severity**: Critical
- **Threshold**: P99 latency > 100ms for 5 minutes
- **Description**: etcd cluster experiencing high latency
- **Impact**: Kubernetes API slowness, cluster instability
- **Remediation**:
  1. Check etcd member health
  2. Review disk I/O metrics
  3. Compact and defragment
  4. Consider scaling etcd
- **Runbook**: [infra-etcd-latency.md](./runbooks/infra-etcd-latency.md)

### INF-005: NetworkPolicyViolation
- **Severity**: Warning
- **Threshold**: Denied connections > 100/min for 5 minutes
- **Description**: High rate of network policy denials
- **Impact**: Service communication issues
- **Remediation**:
  1. Review recent policy changes
  2. Check service discovery
  3. Validate network policies
  4. Update policies if needed
- **Runbook**: [infra-netpol-violation.md](./runbooks/infra-netpol-violation.md)

### INF-006: PrometheusTargetDown
- **Severity**: Warning
- **Threshold**: Target down for > 10 minutes
- **Description**: Prometheus scrape target unreachable
- **Impact**: Missing metrics, blind spots in monitoring
- **Remediation**:
  1. Check target service health
  2. Verify ServiceMonitor config
  3. Review network connectivity
  4. Check authentication/RBAC
- **Runbook**: [infra-prometheus-target.md](./runbooks/infra-prometheus-target.md)

### INF-007: IngressControllerOverload
- **Severity**: Warning
- **Threshold**: Request queue > 1000 for 5 minutes
- **Description**: Ingress controller request queue building up
- **Impact**: Increased latency, potential timeouts
- **Remediation**:
  1. Scale ingress replicas
  2. Review rate limiting
  3. Check backend health
  4. Optimize routing rules
- **Runbook**: [infra-ingress-overload.md](./runbooks/infra-ingress-overload.md)

### INF-008: BackupFailure
- **Severity**: Critical
- **Threshold**: Backup job failed
- **Description**: Scheduled backup job has failed
- **Impact**: Data recovery risk, compliance issues
- **Remediation**:
  1. Check backup job logs
  2. Verify storage access
  3. Review disk space
  4. Trigger manual backup
- **Runbook**: [infra-backup-failure.md](./runbooks/infra-backup-failure.md)

## Alert Correlation Matrix

| Primary Alert | Correlated Alerts | Likely Root Cause |
|--------------|-------------------|-------------------|
| ArtemisHighLatency | NodeMemoryPressure, SophiaGPUUtilization | Resource contention |
| ArtemisOrderProcessingFailure | NetworkPolicyViolation | Network connectivity |
| SophiaModelInferenceTimeout | SophiaGPUUtilization | GPU resource issue |
| NodeMemoryPressure | Multiple pod alerts | Node capacity |
| CertificateExpiry | IngressControllerOverload | Certificate renewal failure |

## Inhibition Rules

### Critical Inhibits Warning
When a critical alert fires, all warning alerts for the same service are suppressed to reduce noise.

### Infrastructure Inhibits Application
When infrastructure alerts fire (node, network, storage), related application alerts are suppressed.

### Maintenance Window Inhibition
During declared maintenance windows, all non-critical alerts are suppressed.

## Alert Testing

### Synthetic Alert Generation

Generate test alerts for validation:

```bash
# Generate test alert
curl -X POST http://alertmanager:9093/api/v1/alerts \
  -H "Content-Type: application/json" \
  -d '[{
    "labels": {
      "alertname": "TestAlert",
      "severity": "warning",
      "domain": "infrastructure"
    },
    "annotations": {
      "description": "This is a test alert"
    }
  }]'
```

### Alert Rule Validation

Validate alert rules before deployment:

```bash
# Validate Prometheus rules
promtool check rules infrastructure/alertmanager/config/alert-rules-*.yaml

# Test alert routing
amtool config routes test \
  --config.file=infrastructure/alertmanager/config/alertmanager-config.yaml
```

## Metrics for Alert Quality

| Metric | Target | Current |
|--------|--------|---------|
| False Positive Rate | < 30% | 28% |
| Mean Time to Acknowledge | < 5 min | 4.2 min |
| Alert Resolution Time | < 30 min | 26 min |
| Alert Fatigue Score | < 3.0 | 2.8 |

## Change History

| Date | Alert | Change | Reason |
|------|-------|--------|--------|
| 2024-01-15 | ART-001 | Threshold: 150ms → 100ms | Tighter SLA |
| 2024-01-10 | SOF-002 | Added GPU check | False positives |
| 2024-01-05 | INF-001 | Memory: 5% → 10% | Earlier warning |

## Contact Information

- **Artemis Team**: artemis-oncall@sophia-intel-ai.com
- **Sophia Team**: sophia-ai-oncall@sophia-intel-ai.com
- **Infrastructure Team**: infra-oncall@sophia-intel-ai.com
- **Escalation**: platform-leads@sophia-intel-ai.com

## References

- [AlertManager Configuration](./config/alertmanager-config.yaml)
- [Prometheus Alert Rules](./config/alert-rules-*.yaml)
- [Runbook Directory](./runbooks/)
- [Monitoring Dashboard](https://grafana.sophia-intel-ai.com/d/alertmanager)