# Deployment Guide

## Overview

Comprehensive deployment guide for Sophia Intel AI across different environments and configurations.

## Quick Start

### Local Development
```bash
# Clone repository
git clone https://github.com/ai-cherry/sophia-intel-ai.git
cd sophia-intel-ai

# Setup environment
cp .env.example .env
# Edit .env with your API keys

# Deploy locally
./deploy_local.sh

# Verify deployment
curl http://localhost:8000/healthz
```

### Docker Compose (Recommended)
```bash
# Production deployment
docker-compose -f docker-compose.production.yml up -d

# Development deployment
docker-compose up -d

# Check status
docker-compose ps
```

## Environment Configuration

### Required API Keys
```bash
# .env file
OPENROUTER_API_KEY=your_openrouter_key
PORTKEY_API_KEY=your_portkey_key
TOGETHER_API_KEY=your_together_key
ANTHROPIC_API_KEY=your_anthropic_key
AGNO_API_KEY=your_agno_key
```

### Service URLs
```bash
# Storage services
WEAVIATE_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://sophia:password@localhost:5432/sophia_intel

# API configuration
AGENT_API_PORT=8000
AGNO_BRIDGE_PORT=7777
```

## Deployment Options

### 1. Local Development

**Requirements:**
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- 8GB RAM minimum

**Setup:**
```bash
# Install Python dependencies
pip install -e ".[dev]"

# Install UI dependencies
cd ui && npm install
cd ../agent-ui && npm install

# Start services
python -m app.api.unified_server &
python -m app.agno_bridge &
cd ui && npm run dev &
cd ../agent-ui && npm run dev &
```

### 2. Docker Deployment

**docker-compose.yml:**
```yaml
version: '3.9'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - ./data:/app/data
    depends_on:
      - weaviate
      - redis
      - postgres

  weaviate:
    image: semitechnologies/weaviate:latest
    ports:
      - "8080:8080"
    
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sophia_intel
      POSTGRES_USER: sophia
      POSTGRES_PASSWORD: secure_password
```

### 3. Kubernetes Deployment

**Helm Installation:**
```bash
# Add Helm repository
helm repo add sophia-intel https://charts.sophia-intel.ai
helm repo update

# Install with custom values
helm install sophia sophia-intel/sophia-intel \
  --namespace sophia-system \
  --create-namespace \
  --values custom-values.yaml
```

**values.yaml:**
```yaml
api:
  replicas: 3
  resources:
    requests:
      memory: "2Gi"
      cpu: "1000m"
    limits:
      memory: "4Gi"
      cpu: "2000m"
  
weaviate:
  enabled: true
  persistence:
    size: 100Gi
  
redis:
  enabled: true
  master:
    persistence:
      size: 10Gi

postgresql:
  enabled: true
  persistence:
    size: 50Gi

ingress:
  enabled: true
  hostname: sophia.example.com
  tls: true
```

### 4. Cloud Deployments

#### AWS
```bash
# Deploy with CloudFormation
aws cloudformation create-stack \
  --stack-name sophia-intel \
  --template-body file://aws/cloudformation.yaml \
  --parameters file://aws/parameters.json

# Or use CDK
cdk deploy SophiaIntelStack
```

#### Google Cloud Platform
```bash
# Deploy with Terraform
cd terraform/gcp
terraform init
terraform plan
terraform apply

# Or use Cloud Run
gcloud run deploy sophia-api \
  --image gcr.io/project/sophia-intel:latest \
  --platform managed \
  --region us-central1
```

#### Azure
```bash
# Deploy with ARM template
az deployment group create \
  --resource-group sophia-rg \
  --template-file azure/template.json \
  --parameters @azure/parameters.json

# Or use Container Instances
az container create \
  --resource-group sophia-rg \
  --name sophia-api \
  --image sophia-intel:latest
```

## Production Configuration

### SSL/TLS Setup

**nginx.conf:**
```nginx
server {
    listen 443 ssl http2;
    server_name sophia.example.com;
    
    ssl_certificate /etc/ssl/certs/sophia.crt;
    ssl_certificate_key /etc/ssl/private/sophia.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    
    location / {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Load Balancing

**HAProxy Configuration:**
```
global
    maxconn 4096
    log stdout local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

backend api_servers
    balance roundrobin
    server api1 api1:8000 check
    server api2 api2:8000 check
    server api3 api3:8000 check
```

### Database Setup

**PostgreSQL Initialization:**
```sql
-- Create database
CREATE DATABASE sophia_intel;

-- Create user
CREATE USER sophia WITH PASSWORD 'secure_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE sophia_intel TO sophia;

-- Create schema
\c sophia_intel;
CREATE SCHEMA IF NOT EXISTS agent_data;
CREATE SCHEMA IF NOT EXISTS graphrag;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

### Redis Configuration

**redis.conf:**
```
# Persistence
appendonly yes
appendfsync everysec

# Memory management
maxmemory 2gb
maxmemory-policy allkeys-lru

# Security
requirepass your_redis_password

# Performance
tcp-keepalive 60
timeout 300
```

## Monitoring Setup

### Prometheus Configuration

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'sophia-api'
    static_configs:
      - targets: ['api:8000']
    
  - job_name: 'celery-workers'
    static_configs:
      - targets: ['celery-worker:9540']
    
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

### Grafana Dashboards

Import dashboards:
1. API Performance: `monitoring/dashboards/api-performance.json`
2. Agent Metrics: `monitoring/dashboards/agent-metrics.json`
3. Memory System: `monitoring/dashboards/memory-system.json`
4. Infrastructure: `monitoring/dashboards/infrastructure.json`

## Scaling Guidelines

### Horizontal Scaling

| Component | Min | Recommended | Max | Notes |
|-----------|-----|-------------|-----|--------|
| API Servers | 2 | 3-5 | 10 | Behind load balancer |
| Celery Workers | 1 | 4-8 | 20 | Based on queue depth |
| Redis | 1 | 3 (cluster) | 6 | Master-slave setup |
| PostgreSQL | 1 | 2 (primary+replica) | 5 | Read replicas |
| Weaviate | 1 | 3 (cluster) | 10 | For vector scaling |

### Resource Allocation

**Small (< 100 users):**
- 4 CPU cores
- 8GB RAM
- 100GB storage

**Medium (100-1000 users):**
- 16 CPU cores
- 32GB RAM
- 500GB storage

**Large (1000+ users):**
- 32+ CPU cores
- 64GB+ RAM
- 1TB+ storage

## Backup & Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup.sh

# Backup PostgreSQL
pg_dump -h localhost -U sophia sophia_intel > backup/postgres_$(date +%Y%m%d).sql

# Backup Weaviate
curl -X POST http://localhost:8080/v1/backups \
  -H "Content-Type: application/json" \
  -d '{"id": "backup-'$(date +%Y%m%d)'"}'

# Backup Redis
redis-cli --rdb backup/redis_$(date +%Y%m%d).rdb

# Backup SQLite Supermemory
cp data/supermemory.db backup/supermemory_$(date +%Y%m%d).db

# Upload to S3
aws s3 sync backup/ s3://sophia-backups/$(date +%Y%m%d)/
```

### Recovery Procedure

```bash
#!/bin/bash
# restore.sh

# Download from S3
aws s3 sync s3://sophia-backups/$BACKUP_DATE/ restore/

# Restore PostgreSQL
psql -h localhost -U sophia sophia_intel < restore/postgres_$BACKUP_DATE.sql

# Restore Weaviate
curl -X POST http://localhost:8080/v1/backups/backup-$BACKUP_DATE/restore

# Restore Redis
redis-cli --pipe < restore/redis_$BACKUP_DATE.rdb

# Restore SQLite
cp restore/supermemory_$BACKUP_DATE.db data/supermemory.db
```

## Security Hardening

### Network Security
```yaml
# Network policies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
spec:
  podSelector:
    matchLabels:
      app: sophia-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
```

### Secret Management
```bash
# Use Kubernetes secrets
kubectl create secret generic sophia-secrets \
  --from-literal=openrouter-key=$OPENROUTER_API_KEY \
  --from-literal=postgres-password=$POSTGRES_PASSWORD

# Or use HashiCorp Vault
vault kv put secret/sophia \
  openrouter_key=$OPENROUTER_API_KEY \
  postgres_password=$POSTGRES_PASSWORD
```

## Health Checks

### Endpoints
- **API Health**: `GET /healthz`
- **Ready Check**: `GET /readyz`
- **Metrics**: `GET /metrics`

### Monitoring Script
```python
#!/usr/bin/env python3
import requests
import time

SERVICES = [
    {"name": "API", "url": "http://localhost:8000/healthz"},
    {"name": "Agno Bridge", "url": "http://localhost:7777/v1/playground/status"},
    {"name": "Weaviate", "url": "http://localhost:8080/v1/.well-known/ready"},
    {"name": "Redis", "cmd": "redis-cli ping"},
]

def check_health():
    for service in SERVICES:
        try:
            if "url" in service:
                response = requests.get(service["url"], timeout=5)
                status = "✓" if response.status_code == 200 else "✗"
            else:
                # Execute command check
                status = "✓"  # Simplified
            
            print(f"{service['name']}: {status}")
        except Exception as e:
            print(f"{service['name']}: ✗ ({e})")

if __name__ == "__main__":
    while True:
        check_health()
        time.sleep(30)
```

## Troubleshooting

### Common Issues

1. **API Not Responding**
   ```bash
   # Check logs
   docker-compose logs api
   
   # Restart service
   docker-compose restart api
   ```

2. **Database Connection Failed**
   ```bash
   # Test connection
   psql -h localhost -U sophia -d sophia_intel -c "SELECT 1;"
   
   # Check credentials
   echo $POSTGRES_URL
   ```

3. **Memory Issues**
   ```bash
   # Check memory usage
   docker stats
   
   # Increase limits
   docker update --memory="4g" sophia-api
   ```

4. **Slow Performance**
   ```bash
   # Check metrics
   curl http://localhost:8000/metrics
   
   # Scale horizontally
   docker-compose up -d --scale api=3
   ```

## Maintenance

### Regular Tasks

**Daily:**
- Monitor error logs
- Check disk usage
- Verify backups

**Weekly:**
- Update dependencies
- Review metrics
- Test recovery procedure

**Monthly:**
- Security updates
- Performance tuning
- Capacity planning

### Update Procedure

```bash
#!/bin/bash
# update.sh

# Pull latest code
git pull origin main

# Build new images
docker-compose build

# Rolling update
docker-compose up -d --no-deps --build api

# Verify
curl http://localhost:8000/healthz
```