# 🚀 Sophia Intel AI - Production Deployment Plan

## Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENTS                              │
├─────────────────────────────────────────────────────────────┤
│  Browser → UI (Vercel) → API (Fly.io) → Services           │
└─────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│                         FLY.IO EDGE                          │
├──────────────────────────────┴──────────────────────────────┤
│  • Global CDN                                                │
│  • Auto-scaling                                              │
│  • Load Balancing                                            │
│  • SSL/TLS Termination                                       │
└──────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│                    SOPHIA API CLUSTER                        │
├──────────────────────────────┴──────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   API-1     │  │   API-2     │  │   API-3     │         │
│  │  (Primary)  │  │  (Replica)  │  │  (Replica)  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└──────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────┐
│                     EXTERNAL SERVICES                        │
├──────────────────────────────┴──────────────────────────────┤
│  • Neon PostgreSQL (Primary Database)                        │
│  • Redis Cloud (Caching & Sessions)                          │
│  • Weaviate Cloud (Vector Store)                             │
│  • Lambda Labs (GPU Compute - Optional)                      │
└──────────────────────────────────────────────────────────────┘
```

## Phase 1: Preparation (Local)

### 1.1 Create Production Dockerfile
```dockerfile
# Dockerfile.production
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/

# Set production environment
ENV PYTHONPATH=/app
ENV LOCAL_DEV_MODE=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the application
CMD ["uvicorn", "app.api.unified_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Create fly.toml Configuration
```toml
# fly.toml
app = "sophia-intel-ai"
primary_region = "sjc"  # San Jose (closest to you)
kill_signal = "SIGINT"
kill_timeout = 5

[build]
  dockerfile = "Dockerfile.production"

[env]
  PORT = "8000"
  PYTHONPATH = "/app"
  LOCAL_DEV_MODE = "false"

[experimental]
  auto_rollback = true

[[services]]
  http_checks = []
  internal_port = 8000
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 100
    soft_limit = 80
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 6
    timeout = "2s"

  [[services.http_checks]]
    interval = "30s"
    grace_period = "5s"
    method = "get"
    path = "/healthz"
    protocol = "http"
    timeout = "2s"
    tls_skip_verify = false

[mounts]
  source = "sophia_data"
  destination = "/data"

[[statics]]
  guest_path = "/app/static"
  url_prefix = "/static/"

[metrics]
  port = 9091
  path = "/metrics"
```

### 1.3 Create Production Environment Configuration
```bash
# .env.production
# Core API Keys
OPENAI_API_KEY=sk-svcacct-...
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENROUTER_API_KEY=sk-or-v1-...
PORTKEY_API_KEY=nYraiE8dOR9A1gDwaRNpSSXRkXBc
GROQ_API_KEY=gsk_...

# Database - Neon PostgreSQL
DATABASE_URL=postgresql://sophia:${NEON_PASSWORD}@ep-proud-surf-123456.us-west-2.aws.neon.tech/sophia
NEON_API_KEY=napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby
NEON_PROJECT_ID=rough-union-72390895

# Redis Cloud
REDIS_URL=redis://default:pdM2P5F7oO269JCCtBURsrCBrSacqZmF@redis-15014.us-east-1-1.ec2.redns.redis-cloud.com:15014

# Weaviate Cloud (to be configured)
WEAVIATE_URL=https://sophia-intel-ai.weaviate.network
WEAVIATE_API_KEY=${WEAVIATE_CLOUD_KEY}

# Lambda Labs (Optional GPU)
LAMBDA_API_KEY=secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f.EsLXt0lkGlhZ1Nd369Ld5DMSuhJg9O9y
LAMBDA_CLOUD_ENDPOINT=https://cloud.lambdalabs.com/api/v1
```

## Phase 2: Fly.io Deployment

### 2.1 Install Fly CLI and Authenticate
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login with your token
export FLY_API_TOKEN="FlyV1 fm2_lJPECAAAAAAACcioxBCHKpegBSo8azHO5tEzGMgIwrVodHRwczovL2FwaS5mbHkuaW8vdjGUAJLOABLk6x8Lk7lodHRwczovL2FwaS5mbHkuaW8vYWFhL3YxxDx..."
fly auth token
```

### 2.2 Create Fly App
```bash
# Create the app
fly apps create sophia-intel-ai --org personal

# Set secrets (sensitive environment variables)
fly secrets set \
  OPENAI_API_KEY="sk-svcacct-..." \
  ANTHROPIC_API_KEY="sk-ant-api03-..." \
  NEON_PASSWORD="Huskers1983$" \
  REDIS_PASSWORD="pdM2P5F7oO269JCCtBURsrCBrSacqZmF" \
  PORTKEY_API_KEY="nYraiE8dOR9A1gDwaRNpSSXRkXBc" \
  --app sophia-intel-ai
```

### 2.3 Deploy API to Fly.io
```bash
# Initial deployment
fly deploy --app sophia-intel-ai

# Scale to 3 instances for high availability
fly scale count 3 --app sophia-intel-ai

# Set up autoscaling
fly autoscale set min=2 max=10 --app sophia-intel-ai
```

## Phase 3: Database & Services Setup

### 3.1 Neon PostgreSQL Setup
```sql
-- Connect to Neon and run migrations
CREATE DATABASE sophia;
\c sophia;

-- Run the init script
\i scripts/init-postgres.sql

-- Create production user
CREATE USER sophia_prod WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE sophia TO sophia_prod;
```

### 3.2 Weaviate Cloud Setup
```bash
# Option 1: Deploy Weaviate to Fly.io
fly apps create sophia-weaviate --org personal
fly deploy --app sophia-weaviate -c docker-compose.weaviate.yml

# Option 2: Use Weaviate Cloud Service
# 1. Go to https://console.weaviate.cloud
# 2. Create new cluster
# 3. Get endpoint and API key
# 4. Update WEAVIATE_URL and WEAVIATE_API_KEY
```

### 3.3 Redis Cloud (Already Configured)
- Using existing Redis Cloud instance
- Connection string already in environment

## Phase 4: UI Deployment

### 4.1 Deploy UI to Vercel
```bash
cd /Users/lynnmusil/sophia-intel-ai/agent-ui

# Install Vercel CLI
npm i -g vercel

# Deploy to production
vercel --prod \
  --env NEXT_PUBLIC_API_URL=https://sophia-intel-ai.fly.dev \
  --env NEXT_PUBLIC_DEFAULT_ENDPOINT=https://sophia-intel-ai.fly.dev
```

### 4.2 Alternative: Deploy UI to Fly.io
```dockerfile
# Dockerfile.ui
FROM node:18-alpine
WORKDIR /app
COPY agent-ui/package*.json ./
RUN npm ci --only=production
COPY agent-ui/ .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
fly apps create sophia-ui --org personal
fly deploy --app sophia-ui -c Dockerfile.ui
```

## Phase 5: Lambda Labs GPU Setup (Optional)

### 5.1 Lambda Labs Instance Creation
```python
# scripts/setup_lambda_gpu.py
import requests
import os

LAMBDA_API_KEY = os.getenv("LAMBDA_API_KEY")
LAMBDA_ENDPOINT = "https://cloud.lambdalabs.com/api/v1"

headers = {
    "Authorization": f"Bearer {LAMBDA_API_KEY}"
}

# Create GPU instance for heavy ML workloads
def create_gpu_instance():
    payload = {
        "region_name": "us-west-1",
        "instance_type_name": "gpu_1x_a100",
        "ssh_key_names": ["sophia-key"],
        "file_system_names": [],
        "quantity": 1
    }
    
    response = requests.post(
        f"{LAMBDA_ENDPOINT}/instance-operations/launch",
        json=payload,
        headers=headers
    )
    return response.json()

# Setup instance with dependencies
def setup_instance(instance_id):
    setup_script = """
    #!/bin/bash
    pip install torch transformers accelerate
    git clone https://github.com/ai-cherry/sophia-intel-ai
    cd sophia-intel-ai
    pip install -r requirements.txt
    """
    
    # SSH and run setup
    # ... implementation
```

### 5.2 Connect API to Lambda GPU
```python
# app/gpu/lambda_executor.py
class LambdaGPUExecutor:
    def __init__(self):
        self.api_key = os.getenv("LAMBDA_API_KEY")
        self.endpoint = os.getenv("LAMBDA_CLOUD_ENDPOINT")
    
    async def execute_on_gpu(self, task):
        # Route heavy ML tasks to Lambda GPU
        # ... implementation
```

## Phase 6: Monitoring & Observability

### 6.1 Set Up Monitoring
```bash
# Add Grafana Cloud
fly secrets set \
  GRAFANA_API_KEY="..." \
  GRAFANA_ENDPOINT="https://prometheus-prod-us-central.grafana.net/api/prom/push"

# Enable metrics
fly metrics enable --app sophia-intel-ai
```

### 6.2 Configure Alerts
```yaml
# alerts.yml
alerts:
  - name: high_error_rate
    condition: rate(errors) > 0.05
    action: notify_slack
  
  - name: high_latency
    condition: p99(response_time) > 2000ms
    action: notify_pagerduty
```

## Phase 7: CI/CD Pipeline

### 7.1 GitHub Actions Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Fly.io
        uses: superfly/flyctl-actions@v2
        with:
          args: "deploy --app sophia-intel-ai"
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
  
  deploy-ui:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        uses: vercel/action@v1
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
```

## Phase 8: Post-Deployment

### 8.1 DNS Configuration
```bash
# Point your domain to Fly.io
fly certs add sophia-intel-ai.com --app sophia-intel-ai

# Add CNAME records:
# api.sophia-intel-ai.com → sophia-intel-ai.fly.dev
# app.sophia-intel-ai.com → sophia-ui.vercel.app
```

### 8.2 Performance Testing
```bash
# Load testing
artillery quick --count 100 --num 10 https://sophia-intel-ai.fly.dev/healthz

# Stress testing
vegeta attack -duration=30s -rate=100 \
  -targets=targets.txt | vegeta report
```

## Deployment Commands Summary

```bash
# 1. Build and test locally
docker build -f Dockerfile.production -t sophia-api .
docker run -p 8000:8000 --env-file .env.production sophia-api

# 2. Deploy API to Fly.io
fly deploy --app sophia-intel-ai

# 3. Deploy UI to Vercel
cd agent-ui && vercel --prod

# 4. Monitor deployment
fly status --app sophia-intel-ai
fly logs --app sophia-intel-ai

# 5. Scale if needed
fly scale count 5 --app sophia-intel-ai
```

## Cost Estimate

| Service | Configuration | Monthly Cost |
|---------|--------------|-------------|
| Fly.io API | 3x shared-cpu-2x (4GB RAM) | ~$30 |
| Fly.io Postgres | 1GB Dev | Free |
| Neon PostgreSQL | Starter | Free-$19 |
| Redis Cloud | 30MB | Free |
| Weaviate Cloud | Sandbox | Free-$25 |
| Lambda Labs GPU | On-demand A100 | $1.10/hour (as needed) |
| Vercel | Pro | $20 |
| **Total** | **Production Ready** | **~$50-75/month** |

## Success Metrics

- ✅ API response time < 200ms (p50)
- ✅ 99.9% uptime SLA
- ✅ Auto-scaling 2-10 instances
- ✅ Global CDN distribution
- ✅ SSL/TLS encryption
- ✅ Automated backups
- ✅ Real-time monitoring
- ✅ GPU acceleration available

## Rollback Plan

```bash
# If deployment fails
fly releases --app sophia-intel-ai
fly deploy --app sophia-intel-ai --image <previous-image>

# Database rollback
fly postgres connect --app sophia-postgres
\i scripts/rollback.sql
```

---

**Ready to deploy! This plan provides a production-ready, scalable deployment of Sophia Intel AI with high availability, monitoring, and optional GPU acceleration.**