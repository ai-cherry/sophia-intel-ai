# SOPHIA Intel Infrastructure Runbook - CPU-Optimized Lambda Labs

This runbook guides you through deploying SOPHIA Intel's CPU-optimized infrastructure on Lambda Labs, from clean slate to production-ready cluster with automated CI/CD.

> **Architecture Philosophy:** CPU-first, cost-optimized, API-driven infrastructure that delivers 80% cost savings while maintaining high performance through intelligent model routing.

---

## 🏗️ Infrastructure Overview

**Target Architecture:**
- **3x CPU Instances**: `cpu.c2-2` (2 vCPU, 4GB RAM each)
- **K3s Cluster**: Lightweight Kubernetes orchestration
- **Kong Ingress**: API gateway with SSL termination
- **Auto-scaling**: Horizontal pod autoscaling based on CPU/memory
- **Cost**: ~$150/month vs $750/month for GPU equivalent

---

## 0️⃣ Environment Verification

```bash
# Verify all required environment variables
bash scripts/check_env.sh
```

**Required Environment Variables:**
```bash
# Lambda Labs API (CPU cluster provisioning)
LAMBDA_CLOUD_API_KEY=ll-your-lambda-labs-api-key

# AI Model Routing APIs
LAMBDA_API_KEY=secret_sophiacloudapi_your-lambda-inference-key
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key

# DNS and SSL Management
DNSIMPLE_API_KEY=dnsimple_u_your-dns-management-key
DOMAIN_NAME=sophia-intel.ai

# GitHub Integration
GITHUB_PAT=github_pat_your-personal-access-token
GITHUB_ORG=ai-cherry
```

---

## 1️⃣ Infrastructure Audit (Read-Only)

```bash
# Audit current Lambda Labs infrastructure
python scripts/audit_current_infra.py
```

**What it checks:**
- All running CPU instances and their specifications
- SSH key registrations and access
- Network configuration and security groups
- Cost analysis and optimization opportunities

---

## 2️⃣ Clean Slate Preparation

**Dry-run teardown (safe):**
```bash
python scripts/teardown_lambda_infra.py --dry-run
```

**Complete infrastructure reset (destructive):**
```bash
python scripts/teardown_lambda_infra.py --confirm-burn-it-down
```

**Post-teardown verification:**
- ✅ Zero running instances
- ✅ SSH keys cleaned up
- ✅ Network resources released

---

## 3️⃣ SSH Key Generation

```bash
# Generate production SSH key pair
bash scripts/gen_ssh_key.sh
```

**Key Management:**
- **Private Key**: `~/.ssh/id_ed25519_sophia_prod` (stays on your workstation)
- **Public Key**: `~/.ssh/id_ed25519_sophia_prod.pub` (registered with Lambda Labs)
- **Security**: Ed25519 encryption, 4096-bit equivalent strength

---

## 4️⃣ CPU Cluster Provisioning

```bash
# Deploy CPU-optimized infrastructure with Pulumi
cd infra
pulumi up --stack scoobyjava-org/sophia-prod-on-lambda
```

**Provisioned Resources:**
```yaml
# Primary API Server
sophia-api-01:
  instance_type: cpu.c2-2
  region: us-west-1
  role: api-server
  
# Worker Nodes
sophia-worker-01:
  instance_type: cpu.c2-2
  region: us-west-1
  role: worker
  
sophia-worker-02:
  instance_type: cpu.c2-2
  region: us-west-1
  role: worker
```

**Expected Output:**
```
✅ 3 CPU instances provisioned
✅ K3s cluster initialized
✅ Kong ingress controller deployed
✅ SSL certificates configured
✅ Health checks passing
```

---

## 5️⃣ Application Deployment

```bash
# Deploy SOPHIA Intel application stack
kubectl apply -f k8s/manifests/

# Verify deployment status
kubectl get pods -n sophia-intel
```

**Application Components:**
- **SOPHIA API**: Main application server (Port 5000)
- **Dashboard**: React frontend (Port 3000)
- **MCP Servers**: Model Context Protocol servers (Port 8001)
- **AI Router**: Intelligent model routing service
- **Agent Swarm**: Specialized AI agents for development tasks

---

## 6️⃣ DNS and SSL Configuration

```bash
# Configure domain and SSL certificates
bash scripts/deploy_to_production_domain.sh
```

**DNS Configuration:**
```
A     sophia-intel.ai           → [Load Balancer IP]
A     www.sophia-intel.ai       → [Load Balancer IP]
A     api.sophia-intel.ai       → [Load Balancer IP]
A     dashboard.sophia-intel.ai → [Load Balancer IP]
```

**SSL Certificates:**
- **Provider**: Let's Encrypt (automated renewal)
- **Coverage**: Wildcard certificate for `*.sophia-intel.ai`
- **Security**: TLS 1.3, HSTS enabled

---

## 7️⃣ Health Verification

```bash
# Run comprehensive health checks
python scripts/health_check_production.py
```

**Health Check Matrix:**
```
✅ API Server         https://api.sophia-intel.ai/health
✅ Dashboard          https://dashboard.sophia-intel.ai
✅ AI Router          https://api.sophia-intel.ai/ai/health
✅ MCP Servers        https://api.sophia-intel.ai/mcp/health
✅ SSL Certificates   Valid until [date]
✅ DNS Resolution     All domains resolving correctly
✅ Load Balancer      Traffic distribution working
✅ Auto-scaling       HPA configured and responsive
```

---

## 8️⃣ CI/CD Pipeline Activation

```bash
# Activate GitHub Actions workflows
gh workflow enable infra-deploy.yaml
gh workflow enable app-deploy.yaml
gh workflow enable health-monitoring.yaml
```

**Automated Workflows:**
- **Infrastructure**: Pulumi-based infrastructure updates
- **Application**: Kubernetes deployment automation
- **Monitoring**: Continuous health checks and alerting
- **Security**: Automated security scanning and updates

---

## 🔧 Operational Commands

### Scaling Operations
```bash
# Scale worker nodes
kubectl scale deployment sophia-api --replicas=5

# Scale cluster (add more CPU instances)
pulumi config set worker-count 4
pulumi up
```

### Monitoring and Debugging
```bash
# View application logs
kubectl logs -f deployment/sophia-api -n sophia-intel

# Monitor resource usage
kubectl top pods -n sophia-intel

# Check ingress status
kubectl get ingress -n sophia-intel
```

### Backup and Recovery
```bash
# Backup application data
bash scripts/backup_production_data.sh

# Restore from backup
bash scripts/restore_production_data.sh [backup-id]
```

---

## 💰 Cost Optimization

**Monthly Cost Breakdown:**
```
Lambda Labs CPU Instances (3x cpu.c2-2): $120/month
DNS Management (DNSimple):                $5/month
SSL Certificates (Let's Encrypt):         $0/month
Load Balancer:                           $15/month
Monitoring & Logging:                    $10/month
---
Total Infrastructure Cost:               $150/month
```

**Cost vs Performance:**
- **80% cost reduction** compared to GPU infrastructure
- **99.9% uptime** with multi-instance deployment
- **Sub-second response times** with intelligent model routing
- **Auto-scaling** prevents over-provisioning

---

## 🚨 Troubleshooting

### Common Issues

**Issue**: Instances not starting
```bash
# Check Lambda Labs API status
curl -H "Authorization: Bearer $LAMBDA_CLOUD_API_KEY" \
     https://cloud.lambdalabs.com/api/v1/instances
```

**Issue**: SSL certificate problems
```bash
# Renew certificates manually
kubectl delete certificate sophia-intel-tls -n sophia-intel
kubectl apply -f k8s/manifests/certificates/
```

**Issue**: Application not responding
```bash
# Restart application pods
kubectl rollout restart deployment/sophia-api -n sophia-intel
```

### Emergency Procedures

**Complete System Recovery:**
```bash
# 1. Backup current state
bash scripts/emergency_backup.sh

# 2. Reset infrastructure
python scripts/teardown_lambda_infra.py --confirm-burn-it-down

# 3. Redeploy from scratch
pulumi up --stack scoobyjava-org/sophia-prod-on-lambda
kubectl apply -f k8s/manifests/
```

---

## 📊 Success Metrics

After successful deployment, you should see:

- ✅ **API Response Time**: < 200ms average
- ✅ **Uptime**: > 99.9%
- ✅ **Cost Efficiency**: < $200/month total
- ✅ **Auto-scaling**: Responsive to load changes
- ✅ **Security**: A+ SSL rating, all security headers
- ✅ **Performance**: Sub-second AI model routing decisions

---

**SOPHIA Intel Infrastructure** - CPU-optimized, cost-effective, production-ready AI platform.

