# Infrastructure Deployment Template - Pulumi

Use this prompt template for deploying the Sophia Intel platform infrastructure using Pulumi.

## Deployment Prompt Template

```
You are deploying the Sophia Intel AI agent platform infrastructure using Pulumi. Follow the cloud-first deployment standards and ensure all components are properly configured for production.

**Deployment Context:**
- Platform: Sophia Intel (Python 3.11 + uv)
- Target Cloud: [AWS/GCP/Azure]
- Environment: [staging/production]
- Region: [specify target region]

**Infrastructure Components Required:**

### 1. Container Orchestration
- **Kubernetes Cluster** or **Container Service**
  - Auto-scaling enabled
  - Multi-AZ deployment
  - Node groups for different workload types

### 2. Databases & Storage
- **PostgreSQL** (managed service)
  - Multi-AZ for high availability
  - Automated backups
  - Connection pooling
- **Redis** (managed service)
  - Cluster mode for scaling
  - Persistence enabled
- **Qdrant Vector Database**
  - Cloud instance or self-hosted
  - Persistent storage
  - API key authentication

### 3. Application Services
- **Load Balancer** (Application Load Balancer)
- **API Gateway** (for MCP servers)
- **Container Registry** (for Docker images)
- **Secrets Manager** (for API keys and credentials)

### 4. Monitoring & Observability
- **Prometheus/Grafana** or cloud monitoring
- **Log aggregation** (CloudWatch/Stackdriver)
- **Application Performance Monitoring**

### 5. Networking & Security
- **VPC** with private/public subnets
- **Security Groups** with least privilege
- **WAF** for web application firewall
- **SSL/TLS certificates**

**Pulumi Stack Configuration:**

```yaml
# Pulumi.{environment}.yaml
config:
  # Basic Configuration
  sophia:environment: {environment}
  sophia:region: {region}
  
  # Database Configuration
  sophia:postgres-instance-class: db.r5.large
  sophia:redis-node-type: cache.r5.large
  
  # Kubernetes Configuration
  sophia:k8s-node-instance-type: m5.xlarge
  sophia:k8s-min-nodes: 2
  sophia:k8s-max-nodes: 10
  
  # Qdrant Configuration
  sophia:qdrant-cluster-size: 3
  sophia:qdrant-memory: 8Gi
  
  # Domain Configuration
  sophia:domain-name: sophia.yourdomain.com
  sophia:certificate-arn: arn:aws:acm:...
```

**Deployment Steps:**

### Step 1: Initialize Pulumi Project
```bash
# Initialize new Pulumi project
pulumi new kubernetes-python --name sophia-infra

# Install dependencies
pip install pulumi pulumi-kubernetes pulumi-aws pulumi-docker

# Configure stack
pulumi stack init {environment}
pulumi config set aws:region {region}
```

### Step 2: Define Infrastructure Components

**VPC and Networking:**
```python
import pulumi
import pulumi_aws as aws
from pulumi_aws import ec2

# VPC
vpc = ec2.Vpc("sophia-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": "sophia-vpc", "Environment": environment})

# Subnets
private_subnet = ec2.Subnet("sophia-private",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a")

public_subnet = ec2.Subnet("sophia-public",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-east-1a")
```

**Database Services:**
```python
import pulumi_aws as aws

# RDS PostgreSQL
postgres = aws.rds.Instance("sophia-postgres",
    instance_class="db.r5.large",
    allocated_storage=100,
    storage_type="gp2",
    engine="postgres",
    engine_version="15.4",
    db_name="sophia",
    username="sophia",
    password=postgres_password,  # From secrets
    vpc_security_group_ids=[db_security_group.id],
    db_subnet_group_name=db_subnet_group.name,
    backup_retention_period=7,
    multi_az=True,
    storage_encrypted=True)

# ElastiCache Redis
redis = aws.elasticache.ReplicationGroup("sophia-redis",
    description="Sophia Redis cluster",
    node_type="cache.r5.large",
    parameter_group_name="default.redis7",
    port=6379,
    num_cache_clusters=2,
    security_group_ids=[cache_security_group.id],
    subnet_group_name=cache_subnet_group.name)
```

**Kubernetes Cluster:**
```python
import pulumi_eks as eks

# EKS Cluster
cluster = eks.Cluster("sophia-cluster",
    version="1.28",
    instance_types=["m5.xlarge"],
    desired_capacity=2,
    min_size=2,
    max_size=10,
    vpc_id=vpc.id,
    subnet_ids=[private_subnet.id, public_subnet.id])
```

### Step 3: Application Deployment

**Kubernetes Manifests:**
```yaml
# sophia-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sophia
---
# sophia-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sophia-config
  namespace: sophia
data:
  ENVIRONMENT: "{environment}"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  DATABASE_URL: "{postgres_connection_string}"
  REDIS_URL: "{redis_connection_string}"
  QDRANT_URL: "{qdrant_connection_string}"
---
# sophia-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: sophia-secrets
  namespace: sophia
type: Opaque
data:
  OPENROUTER_API_KEY: "{base64_encoded_key}"
  PORTKEY_API_KEY: "{base64_encoded_key}"
  SECRET_KEY: "{base64_encoded_key}"
```

**Deployment Manifests:**
```yaml
# sophia-backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sophia-backend
  namespace: sophia
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sophia-backend
  template:
    metadata:
      labels:
        app: sophia-backend
    spec:
      containers:
      - name: backend
        image: {container_registry}/sophia-backend:{version}
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: sophia-config
        - secretRef:
            name: sophia-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Step 4: Service Configuration

**Load Balancer Services:**
```yaml
# sophia-services.yaml
apiVersion: v1
kind: Service
metadata:
  name: sophia-backend-service
  namespace: sophia
spec:
  selector:
    app: sophia-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: v1
kind: Service
metadata:
  name: sophia-mcp-service
  namespace: sophia
spec:
  selector:
    app: sophia-mcp
  ports:
  - port: 80
    targetPort: 8001
  type: ClusterIP
```

**Ingress Configuration:**
```yaml
# sophia-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sophia-ingress
  namespace: sophia
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - sophia.yourdomain.com
    secretName: sophia-tls
  rules:
  - host: sophia.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: sophia-backend-service
            port:
              number: 80
      - path: /mcp
        pathType: Prefix
        backend:
          service:
            name: sophia-mcp-service
            port:
              number: 80
```

### Step 5: Monitoring & Observability

**Prometheus Configuration:**
```yaml
# prometheus-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    scrape_configs:
    - job_name: 'sophia-backend'
      static_configs:
      - targets: ['sophia-backend-service:80']
      metrics_path: /metrics
    - job_name: 'sophia-mcp'
      static_configs:
      - targets: ['sophia-mcp-service:80']
      metrics_path: /metrics
```

### Step 6: Deployment Execution

**Deploy Infrastructure:**
```bash
# Set configuration
pulumi config set sophia:postgres-password --secret {strong_password}
pulumi config set sophia:redis-auth-token --secret {redis_token}

# Preview changes
pulumi preview

# Deploy infrastructure
pulumi up

# Get outputs
pulumi stack output postgres-endpoint
pulumi stack output redis-endpoint
pulumi stack output cluster-kubeconfig
```

**Deploy Applications:**
```bash
# Configure kubectl
pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml
export KUBECONFIG=kubeconfig.yaml

# Deploy applications
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployments.yaml
kubectl apply -f k8s/services.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployment
kubectl get pods -n sophia
kubectl get services -n sophia
kubectl logs deployment/sophia-backend -n sophia
```

### Step 7: Post-Deployment Validation

**Health Checks:**
```bash
# Test API endpoints
curl https://sophia.yourdomain.com/api/health
curl https://sophia.yourdomain.com/mcp/health

# Test agent functionality
curl -X POST https://sophia.yourdomain.com/api/agent/coding \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "code": "def hello(): pass",
    "query": "Add docstring"
  }'

# Check monitoring
curl https://sophia.yourdomain.com/api/metrics
```

**Performance Testing:**
```bash
# Load testing with wrk
wrk -t12 -c400 -d30s https://sophia.yourdomain.com/api/health

# Agent performance testing
for i in {1..10}; do
  curl -X POST https://sophia.yourdomain.com/api/agent/coding \
    -H "Content-Type: application/json" \
    -d '{
      "session_id": "perf-test-'$i'",
      "code": "# Test code",
      "query": "Optimize this code"
    }'
done
```

### Step 8: Cleanup and Rollback

**Rollback Procedure:**
```bash
# Rollback to previous version
pulumi stack --show-urns
pulumi import {urn} {resource-id}
pulumi up --target-dependents

# Emergency rollback
kubectl rollout undo deployment/sophia-backend -n sophia
kubectl rollout undo deployment/sophia-mcp -n sophia
```

**Complete Cleanup:**
```bash
# Delete Kubernetes resources
kubectl delete namespace sophia

# Destroy Pulumi stack
pulumi destroy
pulumi stack rm {environment}
```
```

## Usage Notes

1. **Replace placeholders** with actual values:
   - `{environment}`: staging/production
   - `{region}`: target cloud region
   - `{container_registry}`: your container registry URL
   - `{version}`: application version tag
   - Strong passwords and API keys

2. **Security considerations**:
   - Use secrets management for all credentials
   - Enable encryption at rest and in transit
   - Configure proper IAM roles and policies
   - Set up VPC security groups with least privilege

3. **Monitoring**:
   - Set up alerts for critical metrics
   - Monitor agent performance and error rates
   - Track database and cache utilization
   - Monitor API response times and availability

4. **Scaling**:
   - Configure horizontal pod autoscaling
   - Set up database read replicas if needed
   - Monitor and adjust resource limits
   - Plan for traffic spikes and seasonal changes

This template provides a production-ready infrastructure deployment for the Sophia Intel platform with proper security, monitoring, and scalability considerations.