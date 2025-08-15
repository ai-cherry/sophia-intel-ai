# SOPHIA Intel Operations Manual

## Overview

This manual provides comprehensive operational procedures for managing the SOPHIA Intel platform in production. The platform runs on a CPU-optimized Lambda Labs infrastructure with Kubernetes orchestration.

## System Architecture

### Infrastructure Stack
```
┌─────────────────────────────────────────┐
│           Lambda Labs CPU Cluster       │
│  ┌─────────────────────────────────────┐ │
│  │            K3s Cluster              │ │
│  │  ┌─────────────────────────────────┐ │ │
│  │  │        Kong Ingress             │ │ │
│  │  │  ┌─────────────────────────────┐ │ │ │
│  │  │  │     SOPHIA Intel Apps       │ │ │ │
│  │  │  │  • AI Router (Claude S4)    │ │ │ │
│  │  │  │  • Agent Swarm              │ │ │ │
│  │  │  │  • Dashboard                │ │ │ │
│  │  │  │  • MCP Servers              │ │ │ │
│  │  │  └─────────────────────────────┘ │ │ │
│  │  └─────────────────────────────────┘ │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Key Components
- **Lambda Labs CPU Instances**: 3x cpu.c2-2 instances (2 vCPU, 4GB RAM each)
- **K3s Cluster**: Lightweight Kubernetes distribution
- **Kong Ingress**: API gateway with SSL termination
- **Let's Encrypt**: Automated SSL certificate management
- **Claude Sonnet 4**: Primary AI model via OpenRouter

## Deployment Procedures

### Initial Deployment

#### Prerequisites
```bash
# Required environment variables
export LAMBDA_CLOUD_API_KEY="your_lambda_api_key"
export DNSIMPLE_API_KEY="your_dnsimple_api_key"
export OPENROUTER_API_KEY="your_openrouter_api_key"
export GITHUB_PAT="your_github_token"
```

#### Deployment Command
```bash
# Clone repository
git clone https://github.com/ai-cherry/sophia-intel.git
cd sophia-intel
git checkout refactor/the-great-alignment

# Execute deployment
./scripts/deploy_cpu_cluster.sh
```

#### Deployment Process
1. **Prerequisites Check**: Validates environment variables and tools
2. **Instance Provisioning**: Creates 3 CPU instances on Lambda Labs
3. **K3s Installation**: Sets up Kubernetes cluster
4. **Component Installation**: Deploys cert-manager, Kong, metrics server
5. **Application Deployment**: Deploys SOPHIA Intel applications
6. **DNS Configuration**: Sets up domain records
7. **Health Validation**: Verifies all services are operational

### Update Deployment

#### Code Updates
```bash
# Pull latest changes
git pull origin refactor/the-great-alignment

# Apply Kubernetes updates
kubectl apply -f k8s/manifests/deployments/
kubectl rollout restart deployment/sophia-api -n sophia-intel
kubectl rollout restart deployment/sophia-dashboard -n sophia-intel
kubectl rollout restart deployment/sophia-mcp-servers -n sophia-intel
```

#### Configuration Updates
```bash
# Update ConfigMaps
kubectl apply -f k8s/manifests/configmaps/

# Update Secrets (use Pulumi ESC)
pulumi config set --secret openrouter-api-key "new_key_value"
pulumi up
```

## Monitoring & Health Checks

### Service Health Endpoints
```bash
# AI Router Health
curl https://api.sophia-intel.ai/api/health

# Agent Swarm Health
curl https://api.sophia-intel.ai/api/swarm/health

# Dashboard Health
curl https://dashboard.sophia-intel.ai/health

# Main API Health
curl https://api.sophia-intel.ai/api/health
```

### Kubernetes Monitoring
```bash
# Check pod status
kubectl get pods -n sophia-intel

# Check service status
kubectl get services -n sophia-intel

# Check ingress status
kubectl get ingress -n sophia-intel

# Check certificate status
kubectl get certificate -n sophia-intel
```

### Log Monitoring
```bash
# View AI Router logs
kubectl logs -f deployment/sophia-api -n sophia-intel

# View Agent Swarm logs
kubectl logs -f deployment/sophia-mcp-servers -n sophia-intel

# View Dashboard logs
kubectl logs -f deployment/sophia-dashboard -n sophia-intel

# View Kong logs
kubectl logs -f deployment/ingress-kong -n kong
```

### Performance Monitoring
```bash
# Check resource usage
kubectl top pods -n sophia-intel
kubectl top nodes

# Check HPA status
kubectl get hpa -n sophia-intel

# Check metrics server
kubectl get --raw /apis/metrics.k8s.io/v1beta1/nodes
```

## Troubleshooting

### Common Issues

#### 1. Service Not Responding
```bash
# Check pod status
kubectl describe pod <pod-name> -n sophia-intel

# Check logs
kubectl logs <pod-name> -n sophia-intel

# Restart deployment
kubectl rollout restart deployment/<deployment-name> -n sophia-intel
```

#### 2. SSL Certificate Issues
```bash
# Check certificate status
kubectl describe certificate sophia-intel-tls -n sophia-intel

# Check cert-manager logs
kubectl logs -f deployment/cert-manager -n cert-manager

# Force certificate renewal
kubectl delete certificate sophia-intel-tls -n sophia-intel
kubectl apply -f k8s/manifests/certificates/
```

#### 3. DNS Resolution Issues
```bash
# Check DNS records
dig www.sophia-intel.ai
dig api.sophia-intel.ai
dig dashboard.sophia-intel.ai

# Update DNS records via DNSimple API
curl -H "Authorization: Bearer $DNSIMPLE_API_KEY" \
     -H "Content-Type: application/json" \
     -X PUT \
     -d '{"content":"NEW_IP_ADDRESS"}' \
     https://api.dnsimple.com/v2/ACCOUNT_ID/zones/sophia-intel.ai/records/RECORD_ID
```

#### 4. High Resource Usage
```bash
# Check resource limits
kubectl describe deployment sophia-api -n sophia-intel

# Scale deployment
kubectl scale deployment sophia-api --replicas=3 -n sophia-intel

# Check HPA configuration
kubectl describe hpa sophia-intel-hpa -n sophia-intel
```

#### 5. AI Router Issues
```bash
# Test AI router directly
curl -X POST https://api.sophia-intel.ai/api/ai/route \
     -H "Content-Type: application/json" \
     -d '{
       "task_type": "general_chat",
       "prompt": "Hello, test message",
       "preferences": {"cost_preference": "balanced"}
     }'

# Check OpenRouter API key
kubectl get secret openrouter-secret -n sophia-intel -o yaml
```

### Emergency Procedures

#### Complete System Restart
```bash
# Restart all deployments
kubectl rollout restart deployment/sophia-api -n sophia-intel
kubectl rollout restart deployment/sophia-dashboard -n sophia-intel
kubectl rollout restart deployment/sophia-mcp-servers -n sophia-intel

# Wait for rollout completion
kubectl rollout status deployment/sophia-api -n sophia-intel
kubectl rollout status deployment/sophia-dashboard -n sophia-intel
kubectl rollout status deployment/sophia-mcp-servers -n sophia-intel
```

#### Cluster Recovery
```bash
# If K3s cluster is unresponsive, restart on master node
ssh -i ~/.ssh/id_ed25519_sophia ubuntu@MASTER_IP
sudo systemctl restart k3s

# On worker nodes
ssh -i ~/.ssh/id_ed25519_sophia ubuntu@WORKER_IP
sudo systemctl restart k3s-agent
```

#### Database Recovery
```bash
# If using persistent storage, check PVC status
kubectl get pvc -n sophia-intel

# Restore from backup (if configured)
kubectl apply -f k8s/manifests/backups/restore-job.yaml
```

## Maintenance Procedures

### Regular Maintenance (Weekly)

#### 1. System Health Check
```bash
# Run validation suite
python3 tests/validation/launch_validation.py

# Check certificate expiration
kubectl get certificate -n sophia-intel -o wide

# Review resource usage
kubectl top pods -n sophia-intel
kubectl top nodes
```

#### 2. Log Rotation
```bash
# Clean up old logs (if not using log aggregation)
kubectl delete pod -l app=sophia-api -n sophia-intel --field-selector=status.phase=Succeeded

# Check disk usage on nodes
kubectl get nodes -o wide
```

#### 3. Security Updates
```bash
# Update base images (rebuild and redeploy)
docker pull python:3.11-slim
docker pull node:18-alpine

# Update Kubernetes components
kubectl get nodes -o wide  # Check K3s version
```

### Monthly Maintenance

#### 1. Performance Review
```bash
# Generate performance report
kubectl top pods -n sophia-intel --sort-by=cpu
kubectl top pods -n sophia-intel --sort-by=memory

# Review HPA metrics
kubectl describe hpa -n sophia-intel
```

#### 2. Cost Analysis
```bash
# Check Lambda Labs usage
curl -H "Authorization: Bearer $LAMBDA_CLOUD_API_KEY" \
     https://cloud.lambdalabs.com/api/v1/instances

# Review OpenRouter usage
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
     https://openrouter.ai/api/v1/usage
```

#### 3. Backup Verification
```bash
# Test backup restoration (if configured)
kubectl apply -f k8s/manifests/backups/test-restore.yaml

# Verify data integrity
kubectl exec -it deployment/sophia-api -n sophia-intel -- python -c "import health_check; health_check.verify_data()"
```

## Scaling Procedures

### Horizontal Scaling
```bash
# Scale specific deployment
kubectl scale deployment sophia-api --replicas=5 -n sophia-intel

# Update HPA configuration
kubectl patch hpa sophia-intel-hpa -n sophia-intel -p '{"spec":{"maxReplicas":10}}'
```

### Vertical Scaling
```bash
# Update resource limits
kubectl patch deployment sophia-api -n sophia-intel -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "sophia-api",
          "resources": {
            "limits": {"cpu": "2", "memory": "4Gi"},
            "requests": {"cpu": "1", "memory": "2Gi"}
          }
        }]
      }
    }
  }
}'
```

### Cluster Scaling
```bash
# Add new Lambda Labs instance
curl -X POST \
     -H "Authorization: Bearer $LAMBDA_CLOUD_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "region_name": "us-west-1",
       "instance_type_name": "cpu.c2-2",
       "ssh_key_names": ["sophia-cpu-cluster"],
       "name": "sophia-cpu-04"
     }' \
     https://cloud.lambdalabs.com/api/v1/instance-operations/launch

# Join to K3s cluster
ssh -i ~/.ssh/id_ed25519_sophia ubuntu@NEW_NODE_IP
curl -sfL https://get.k3s.io | K3S_URL=https://MASTER_IP:6443 K3S_TOKEN=NODE_TOKEN sh -
```

## Security Procedures

### SSL Certificate Management
```bash
# Check certificate status
kubectl get certificate -n sophia-intel

# Force certificate renewal
kubectl delete certificate sophia-intel-tls -n sophia-intel
kubectl apply -f k8s/manifests/certificates/letsencrypt-issuer.yaml
```

### Secret Rotation
```bash
# Rotate OpenRouter API key
kubectl create secret generic openrouter-secret \
        --from-literal=api-key=NEW_API_KEY \
        --dry-run=client -o yaml | kubectl apply -f -

# Restart deployments to pick up new secret
kubectl rollout restart deployment/sophia-api -n sophia-intel
```

### Access Control
```bash
# Review RBAC permissions
kubectl get rolebinding -n sophia-intel
kubectl get clusterrolebinding | grep sophia

# Update service account permissions
kubectl apply -f k8s/manifests/rbac/
```

## Backup & Recovery

### Configuration Backup
```bash
# Backup Kubernetes configurations
kubectl get all -n sophia-intel -o yaml > backup/sophia-intel-$(date +%Y%m%d).yaml

# Backup secrets (encrypted)
kubectl get secrets -n sophia-intel -o yaml > backup/secrets-$(date +%Y%m%d).yaml
```

### Data Backup
```bash
# If using persistent volumes
kubectl get pv,pvc -n sophia-intel

# Create backup job
kubectl apply -f k8s/manifests/backups/backup-job.yaml
```

### Disaster Recovery
```bash
# Complete cluster rebuild
./scripts/deploy_cpu_cluster.sh

# Restore configurations
kubectl apply -f backup/sophia-intel-YYYYMMDD.yaml

# Restore secrets
kubectl apply -f backup/secrets-YYYYMMDD.yaml
```

## Contact Information

### Support Escalation
- **Level 1**: Automated monitoring and alerts
- **Level 2**: Operations team intervention
- **Level 3**: Development team escalation

### Key Contacts
- **Operations**: ops@sophia-intel.ai
- **Development**: dev@sophia-intel.ai
- **Security**: security@sophia-intel.ai

### External Dependencies
- **Lambda Labs**: support@lambdalabs.com
- **DNSimple**: support@dnsimple.com
- **OpenRouter**: support@openrouter.ai

---

*This operations manual should be reviewed and updated monthly to reflect any changes in procedures or infrastructure.*

