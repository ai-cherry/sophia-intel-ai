# AI Orchestra Deployment and Rollout Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Deployment Strategy](#deployment-strategy)
4. [Feature Flags Configuration](#feature-flags-configuration)
5. [Rollout Phases](#rollout-phases)
6. [Monitoring and Alerts](#monitoring-and-alerts)
7. [Rollback Procedures](#rollback-procedures)
8. [Post-Deployment Validation](#post-deployment-validation)

## Pre-Deployment Checklist

### Code Quality
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code coverage > 80%
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks met
- [ ] Code review completed

### Infrastructure
- [ ] Database migrations prepared
- [ ] Cache layer configured
- [ ] Load balancer settings verified
- [ ] SSL certificates valid
- [ ] Backup systems operational

### Documentation
- [ ] API documentation updated
- [ ] Runbook prepared
- [ ] Change log updated
- [ ] Team notified of deployment

## Environment Setup

### Development Environment
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Environment variables
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export DATABASE_URL=postgresql://localhost/ai_orchestra_dev
export REDIS_URL=redis://localhost:6379/0
export WEBSOCKET_MAX_CONNECTIONS=100

# Run migrations
alembic upgrade head

# Start services
docker-compose -f docker-compose.dev.yml up -d
python app/main.py
```

### Staging Environment
```bash
# Build Docker image
docker build -t ai-orchestra:staging -f Dockerfile.staging .

# Deploy to Kubernetes
kubectl apply -f k8s/staging/

# Verify deployment
kubectl rollout status deployment/ai-orchestra -n staging
kubectl get pods -n staging
```

### Production Environment
```bash
# Build and tag production image
docker build -t ai-orchestra:v2.0.0 -f Dockerfile.prod .
docker tag ai-orchestra:v2.0.0 registry.ai-orchestra.com/ai-orchestra:v2.0.0
docker push registry.ai-orchestra.com/ai-orchestra:v2.0.0

# Update production manifest
kubectl set image deployment/ai-orchestra \
  ai-orchestra=registry.ai-orchestra.com/ai-orchestra:v2.0.0 \
  -n production

# Monitor rollout
kubectl rollout status deployment/ai-orchestra -n production
```

## Deployment Strategy

### Blue-Green Deployment
```yaml
# k8s/production/blue-green.yaml
apiVersion: v1
kind: Service
metadata:
  name: ai-orchestra
spec:
  selector:
    app: ai-orchestra
    version: green  # Switch between blue/green
  ports:
    - port: 80
      targetPort: 8000
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-orchestra-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-orchestra
      version: green
  template:
    metadata:
      labels:
        app: ai-orchestra
        version: green
    spec:
      containers:
      - name: ai-orchestra
        image: registry.ai-orchestra.com/ai-orchestra:v2.0.0
        env:
        - name: ENVIRONMENT
          value: production
```

### Canary Deployment
```yaml
# k8s/production/canary.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-orchestra-canary
  annotations:
    nginx.ingress.kubernetes.io/canary: "true"
    nginx.ingress.kubernetes.io/canary-weight: "10"  # 10% traffic
spec:
  rules:
  - host: api.ai-orchestra.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ai-orchestra-canary
            port:
              number: 80
```

## Feature Flags Configuration

### Feature Flag Service
```python
# app/infrastructure/feature_flags.py
class FeatureFlags:
    def __init__(self):
        self.flags = {
            "v2_api": {
                "enabled": True,
                "rollout_percentage": 100,
                "allowlist": []
            },
            "swarm_intelligence": {
                "enabled": True,
                "rollout_percentage": 50,
                "allowlist": ["beta-users"]
            },
            "websocket_streaming": {
                "enabled": True,
                "rollout_percentage": 75,
                "allowlist": []
            },
            "advanced_memory": {
                "enabled": False,
                "rollout_percentage": 0,
                "allowlist": ["internal-testing"]
            }
        }
    
    def is_enabled(self, flag: str, user_id: str = None) -> bool:
        if flag not in self.flags:
            return False
        
        config = self.flags[flag]
        
        # Check if globally enabled
        if not config["enabled"]:
            return False
        
        # Check allowlist
        if user_id and user_id in config["allowlist"]:
            return True
        
        # Check rollout percentage
        import hashlib
        if user_id:
            hash_val = int(hashlib.md5(f"{flag}{user_id}".encode()).hexdigest(), 16)
            return (hash_val % 100) < config["rollout_percentage"]
        
        return config["rollout_percentage"] == 100
```

### LaunchDarkly Integration
```python
import ldclient
from ldclient.config import Config

ldclient.set_config(Config("YOUR_SDK_KEY"))

def check_feature(flag_key: str, user_context: dict) -> bool:
    user = {
        "key": user_context.get("user_id", "anonymous"),
        "custom": {
            "plan": user_context.get("plan", "free"),
            "region": user_context.get("region", "us-east-1")
        }
    }
    return ldclient.get().variation(flag_key, user, False)
```

## Rollout Phases

### Phase 1: Internal Testing (Day 1-3)
- Deploy to staging environment
- Internal team testing
- Performance profiling
- Security scanning

### Phase 2: Beta Users (Day 4-7)
- Enable for 5% of beta users
- Monitor metrics closely
- Collect feedback
- Fix critical issues

### Phase 3: Gradual Rollout (Day 8-14)
- Day 8: 10% of traffic
- Day 10: 25% of traffic
- Day 12: 50% of traffic
- Day 14: 75% of traffic

### Phase 4: Full Rollout (Day 15)
- 100% of traffic
- Monitor for 24 hours
- Ready for rollback if needed

## Monitoring and Alerts

### Key Metrics to Monitor
```yaml
# prometheus/alerts.yml
groups:
- name: ai-orchestra
  interval: 30s
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      description: "Error rate is {{ $value }} (threshold: 0.05)"
  
  - alert: HighLatency
    expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High P95 latency"
      description: "P95 latency is {{ $value }}s (threshold: 2s)"
  
  - alert: WebSocketConnectionLimit
    expr: websocket_connections > 900
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Approaching WebSocket connection limit"
      description: "Current connections: {{ $value }} (limit: 1000)"
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "AI Orchestra Deployment",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~'5..'}[5m])"
          }
        ]
      },
      {
        "title": "P95 Latency",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, http_request_duration_seconds)"
          }
        ]
      },
      {
        "title": "WebSocket Connections",
        "targets": [
          {
            "expr": "websocket_connections"
          }
        ]
      }
    ]
  }
}
```

## Rollback Procedures

### Immediate Rollback
```bash
#!/bin/bash
# rollback.sh

# 1. Switch traffic to previous version
kubectl set image deployment/ai-orchestra \
  ai-orchestra=registry.ai-orchestra.com/ai-orchestra:v1.9.0 \
  -n production

# 2. Wait for rollout
kubectl rollout status deployment/ai-orchestra -n production

# 3. Verify health
./scripts/health_check.sh

# 4. Disable feature flags
curl -X POST https://api.launchdarkly.com/api/v2/flags/ai-orchestra/v2-features \
  -H "Authorization: YOUR_API_KEY" \
  -d '{"patch": [{"op": "replace", "path": "/environments/production/on", "value": false}]}'

# 5. Notify team
./scripts/notify_rollback.sh "v2.0.0" "v1.9.0" "High error rate"
```

### Database Rollback
```sql
-- Rollback migrations
BEGIN;
-- Revert schema changes
ALTER TABLE chat_sessions DROP COLUMN optimization_mode;
ALTER TABLE websocket_connections DROP COLUMN pool_id;
-- Restore indexes
CREATE INDEX idx_sessions_user_id ON chat_sessions(user_id);
COMMIT;
```

### Cache Invalidation
```python
import redis

def clear_deployment_cache():
    r = redis.Redis(host='redis.ai-orchestra.com', port=6379)
    
    # Clear all v2 cache keys
    for key in r.scan_iter("v2:*"):
        r.delete(key)
    
    # Reset feature flags cache
    r.delete("feature_flags:*")
    
    # Clear session data
    r.delete("sessions:*")
```

## Post-Deployment Validation

### Smoke Tests
```python
# tests/smoke/test_deployment.py
import requests
import websocket
import time

def test_health_endpoint():
    """Verify health endpoint is responding"""
    response = requests.get("https://api.ai-orchestra.com/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_endpoint():
    """Test basic API functionality"""
    response = requests.post(
        "https://api.ai-orchestra.com/chat/v2/chat",
        headers={"Authorization": "Bearer SMOKE_TEST_TOKEN"},
        json={
            "message": "test",
            "session_id": "smoke-test"
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] == True

def test_websocket_connection():
    """Test WebSocket connectivity"""
    ws = websocket.create_connection(
        "wss://api.ai-orchestra.com/chat/ws/smoke-test/session-1"
    )
    ws.send('{"type": "ping"}')
    result = ws.recv()
    assert result is not None
    ws.close()

def test_metrics_endpoint():
    """Verify metrics are being collected"""
    response = requests.get("https://api.ai-orchestra.com/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
```

### Load Testing
```bash
# Run load test with k6
k6 run --vus 100 --duration 5m scripts/load_test.js

# Expected results:
# - P95 response time < 2s
# - Error rate < 0.1%
# - Throughput > 1000 req/s
```

### Security Validation
```bash
# Run security scan
docker run --rm \
  -v $(pwd):/app \
  owasp/zap2docker-stable zap-baseline.py \
  -t https://api.ai-orchestra.com \
  -r security_report.html

# Check for vulnerabilities
trivy image registry.ai-orchestra.com/ai-orchestra:v2.0.0
```

## Runbook

### Common Issues and Solutions

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n production

# Scale horizontally
kubectl scale deployment ai-orchestra --replicas=5 -n production

# Restart pods with memory leak
kubectl delete pod ai-orchestra-xxxxx -n production
```

#### Database Connection Pool Exhaustion
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Kill idle connections
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' 
AND state_change < now() - interval '10 minutes';
```

#### WebSocket Connection Issues
```python
# Force disconnect idle connections
from app.infrastructure.connection_manager import ConnectionManager

manager = ConnectionManager()
await manager.cleanup_idle_connections(idle_threshold_seconds=300)
```

## Contact Information

- **On-Call Engineer**: Use PagerDuty rotation
- **Escalation**: 
  1. L1: Platform Team
  2. L2: Backend Team Lead
  3. L3: CTO
- **War Room**: #ai-orchestra-incidents (Slack)
- **Status Page**: https://status.ai-orchestra.com