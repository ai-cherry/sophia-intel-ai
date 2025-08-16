# Production Deployment Guide

This guide covers the complete deployment process for the SOPHIA Intel platform to production servers.

## 🚀 Quick Production Deployment

For immediate deployment to www.sophia-intel.ai, see [REAL_PRODUCTION_DEPLOY.md](../../REAL_PRODUCTION_DEPLOY.md)

## Overview

The SOPHIA Intel platform uses a production-ready architecture with:

- **React Frontend** with Vite build system
- **FastAPI Backend** with async capabilities  
- **Nginx Reverse Proxy** for production serving
- **SSL/TLS Certificates** via Let's Encrypt
- **Systemd Services** for process management

## Production Server Requirements

### Minimum Specifications
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum, 50GB recommended
- **Network**: Public IP with ports 80/443 accessible

### Required Software
```bash
# Core packages
sudo apt update
sudo apt install -y nginx python3 python3-pip python3-venv nodejs npm git curl

# SSL certificate management
sudo apt install -y certbot python3-certbot-nginx

# Optional: Docker for containerized deployment
curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh
```

## Production Deployment Methods

### Method 1: Direct Server Deployment (Recommended)

1. **Clone repository on production server**:
```bash
cd /opt
sudo git clone https://github.com/ai-cherry/sophia-intel.git
sudo chown -R $USER:$USER /opt/sophia-intel
```

2. **Setup backend**:
```bash
cd /opt/sophia-intel
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

3. **Build and deploy frontend**:
```bash
cd apps/dashboard
npm install
npm run build
sudo mkdir -p /var/www/sophia-intel
sudo cp -r dist/* /var/www/sophia-intel/
```

4. **Configure Nginx and SSL**:
```bash
# See REAL_PRODUCTION_DEPLOY.md for complete Nginx configuration
sudo certbot --nginx -d sophia-intel.ai -d www.sophia-intel.ai
```

### Method 2: Docker Deployment

Use the provided `docker-compose.prod.yml` for containerized deployment with automatic SSL renewal and service management.

## Environment Configuration

### Production Environment Variables
```bash
# Core API Configuration
LAMBDA_API_KEY=your-actual-lambda-key
OPENAI_API_KEY=your-openai-key
PORT=5000
HOST=127.0.0.1
ENVIRONMENT=production

# Security
SECRET_KEY=your-production-secret-key
JWT_SECRET=your-jwt-secret
API_SALT=your-api-salt

# Database (if using)
DATABASE_URL=postgresql://user:pass@localhost:5432/sophia_prod
REDIS_URL=redis://localhost:6379/0
```

### Frontend Configuration
Ensure `apps/dashboard/vite.config.js` has proper production settings:
```javascript
export default defineConfig({
  preview: {
    host: '0.0.0.0',
    port: 8080,
    allowedHosts: true  // CRITICAL for production domains
  }
})
```

### 5. Verify Installation

```bash
# Run deployment tests
python scripts/test_deployment.py

# Test Estuary integration
python scripts/test_estuary_integration.py

# Check health endpoints
curl http://localhost:8000/health
```

## Production Deployment

### 1. Infrastructure Setup

The platform uses Pulumi for Infrastructure as Code:

```bash
# Navigate to infrastructure directory
cd infra

# Install Pulumi dependencies
uv sync

# Configure Pulumi stack
pulumi stack select scoobyjava-org/sophia-prod-on-lambda

# Deploy infrastructure
pulumi up
```

### 2. Secrets Management

Secrets are managed through GitHub Organization Secrets → Pulumi ESC → Application:

```bash
# Set secrets in GitHub Organization Secrets
# These will be automatically synced to Pulumi ESC

# Required production secrets:
OPENROUTER_API_KEY
LAMBDA_CLOUD_API_KEY
EXA_API_KEY
SECRET_KEY
ENCRYPTION_KEY
JWT_SECRET
API_SALT
DATABASE_URL
REDIS_URL
QDRANT_URL
ESTUARY_JWT_TOKEN
ESTUARY_REFRESH_TOKEN
```

### 3. CI/CD Deployment

The platform uses GitHub Actions for automated deployment:

```bash
# Push to main branch triggers deployment
git push origin main

# Or manually trigger deployment
gh workflow run deploy.yml
```

### 4. Verify Production Deployment

```bash
# Check production endpoints
curl https://api.sophia-intel.ai/health
curl https://app.sophia-intel.ai

# Monitor deployment logs
gh run list --workflow=deploy.yml
gh run view <run-id> --log
```

## Deployment Environments

### Development
- **URL**: http://localhost:8000
- **Database**: Local PostgreSQL
- **Cache**: Local Redis
- **Vector DB**: Local Qdrant

### Production
- **API URL**: https://api.sophia-intel.ai
- **App URL**: https://app.sophia-intel.ai
- **Infrastructure**: Lambda Labs
- **Database**: Managed PostgreSQL
- **Cache**: Managed Redis
- **Vector DB**: Managed Qdrant

## Monitoring & Health Checks

### Health Endpoints

```bash
# Application health
GET /health

# Database health
GET /health/database

# Cache health
GET /health/cache

# Vector database health
GET /health/vector

# Estuary Flow health
GET /health/estuary
```

### Monitoring Tools

- **Application Metrics**: Built-in FastAPI metrics
- **Infrastructure Metrics**: Lambda Labs monitoring
- **Log Aggregation**: Structured JSON logging
- **Alerting**: GitHub Actions notifications

## Troubleshooting

### Common Issues

**1. Dependency Installation Fails**
```bash
# Clear cache and reinstall
uv cache clean
rm -rf .venv
uv venv
uv sync --dev
```

**2. Database Connection Issues**
```bash
# Check database status
docker-compose ps postgres

# View database logs
docker-compose logs postgres

# Reset database
docker-compose down postgres
docker-compose up -d postgres
```

**3. CI/CD Pipeline Failures**
```bash
# Check workflow status
gh run list --workflow=ci.yml

# View specific run logs
gh run view <run-id> --log

# Re-run failed jobs
gh run rerun <run-id>
```

**4. Production Deployment Issues**
```bash
# Check Pulumi stack status
pulumi stack --show-urns

# View infrastructure logs
pulumi logs

# Rollback if needed
pulumi stack select previous
pulumi up
```

### Log Analysis

```bash
# View application logs
tail -f logs/sophia.log

# Filter for errors
grep ERROR logs/sophia.log

# View structured logs
jq '.' logs/sophia.json
```

## Performance Optimization

### Application Performance

- **Connection Pooling**: Configured for PostgreSQL and Redis
- **Caching Strategy**: Multi-layer caching with Redis
- **Async Operations**: Full async/await implementation
- **Resource Limits**: Configured container limits

### Infrastructure Performance

- **Auto Scaling**: Configured based on CPU/memory usage
- **Load Balancing**: Distributed across multiple instances
- **CDN**: Static assets served via CDN
- **Database Optimization**: Indexed queries and connection pooling

## Security Considerations

### Application Security

- **Input Validation**: Pydantic models for all inputs
- **Authentication**: JWT-based authentication
- **Authorization**: Role-based access control
- **Rate Limiting**: API rate limiting implemented

### Infrastructure Security

- **Network Security**: VPC with private subnets
- **Encryption**: TLS 1.2+ for all communications
- **Secrets Management**: Encrypted secrets via Pulumi ESC
- **Access Control**: IAM roles and policies

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups
# Manual backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20250814.sql
```

### Configuration Backups

```bash
# Export Pulumi state
pulumi stack export > stack_backup.json

# Import Pulumi state
pulumi stack import < stack_backup.json
```

## Scaling

### Horizontal Scaling

- **Application Instances**: Scale via container orchestration
- **Database**: Read replicas for query scaling
- **Cache**: Redis cluster for distributed caching
- **Vector Database**: Qdrant cluster for vector operations

### Vertical Scaling

- **CPU/Memory**: Increase instance sizes
- **Storage**: Expand disk capacity
- **Network**: Upgrade bandwidth allocation

## Cost Optimization

### Resource Management

- **Instance Sizing**: Right-size based on usage
- **Auto Shutdown**: Scheduled shutdown for dev environments
- **Resource Monitoring**: Track usage and costs
- **Reserved Instances**: Use reserved instances for predictable workloads

### Development Efficiency

- **Local Development**: Minimize cloud usage during development
- **Shared Environments**: Use shared dev/staging environments
- **Efficient CI/CD**: Optimize build times and resource usage

## References

- [Infrastructure Remediation Report](INFRASTRUCTURE_REMEDIATION_REPORT.md)
- [Ship Checklist](SHIP_CHECKLIST.md)
- [CI/CD Configuration](cicd.md)
- [Dependency Management](../dependency_management.md)
- [Estuary Flow Integration](../estuary_flow_integration.md)



## Enterprise Infrastructure Updates (v2.0)

### Recent Infrastructure Improvements

The Sophia Intel platform has been upgraded with enterprise-grade infrastructure improvements:

#### Service Consolidation and Refactoring

1. **Frontend Consolidation**
   - Removed duplicate `apps/interface` directory
   - Consolidated to single React frontend: `apps/sophia-dashboard/sophia-dashboard-frontend`
   - Fixed dependency conflicts (date-fns version)
   - Added production-ready Dockerfile with Nginx

2. **MCP Services Consolidation**
   - Removed duplicate MCP server directories
   - Consolidated all MCP services under `apps/mcp-services/`
   - Standardized Docker configurations

3. **Enhanced Security**
   - Hardened authentication in dashboard backend
   - Added production token validation
   - Improved CORS configuration
   - Added missing `reset_conversation` endpoint

#### New Docker Configurations

All services now have production-ready Dockerfiles:

```bash
# API Gateway (FastAPI + Uvicorn)
apps/api-gateway/Dockerfile

# Dashboard Backend (Flask + Gunicorn)  
apps/sophia-dashboard/sophia-dashboard-backend/Dockerfile

# Dashboard Frontend (React + Nginx)
apps/sophia-dashboard/sophia-dashboard-frontend/Dockerfile

# MCP Services (Python + Gunicorn)
apps/mcp-services/embedding-mcp-server/Dockerfile
```

#### Requirements Files Added

Missing requirements.txt files have been created:

- `apps/api-gateway/requirements.txt`
- `apps/api/requirements.txt`
- Updated `apps/sophia-dashboard/sophia-dashboard-backend/requirements.txt`

#### Pulumi Infrastructure Enhancements

The Pulumi infrastructure has been enhanced with:

1. **DNS Management**
   - Automated DNS record creation for all subdomains
   - TLS certificate management
   - Load balancer configuration (IP: 192.222.58.232)

2. **Application Deployment**
   - Automated service deployment scripts
   - Health check configurations
   - Monitoring setup

3. **Secrets Management**
   - Integration with GitHub Secrets
   - Secure environment variable injection
   - Production-ready secret handling

#### Service Endpoints (Updated)

After the enterprise infrastructure deployment:

- **Main Application**: https://app.sophia-intel.ai
- **API Gateway**: https://api.sophia-intel.ai  
- **Root Domain**: https://www.sophia-intel.ai
- **Load Balancer**: http://192.222.58.232

#### GitHub Secrets Configuration

The following secrets have been configured in the GitHub repository:

- `LAMBDA_API_KEY`: Lambda Labs API access
- `DEPLOYMENT_PAT`: GitHub Personal Access Token (renamed from GITHUB_PAT due to naming restrictions)
- `DNSIMPLE_API_KEY`: DNS management
- `OPENROUTER_API_KEY`: AI model access
- `PULUMI_ACCESS_TOKEN`: Infrastructure deployment

#### Deployment Validation

To validate the enterprise deployment:

```bash
# Check Pulumi stack status
cd infra
pulumi stack ls
pulumi stack --show-name

# Verify DNS configuration
nslookup api.sophia-intel.ai
nslookup app.sophia-intel.ai

# Test service endpoints
curl -v https://api.sophia-intel.ai/health
curl -v https://app.sophia-intel.ai

# Check load balancer directly
curl -v http://192.222.58.232
```

#### Migration Notes

When upgrading from v1.0 to v2.0:

1. **Frontend Migration**
   - The minimal `apps/interface` has been removed
   - Use `apps/sophia-dashboard/sophia-dashboard-frontend` for all frontend needs
   - Update any references to the old interface

2. **MCP Services Migration**
   - Individual MCP server directories have been consolidated
   - Update any deployment scripts to use `apps/mcp-services/`

3. **Authentication Updates**
   - `DASHBOARD_API_TOKEN` is now required in production
   - Update environment configurations accordingly

4. **Docker Updates**
   - All services now use production-ready Dockerfiles
   - Update CI/CD pipelines to use new Docker configurations

#### Troubleshooting Enterprise Infrastructure

**DNS Issues**
```bash
# Check DNS propagation
dig api.sophia-intel.ai
dig app.sophia-intel.ai

# Verify DNSimple configuration
# Check Pulumi DNS outputs
pulumi stack output dns_records
```

**Certificate Issues**
```bash
# Check TLS certificate status
openssl s_client -connect api.sophia-intel.ai:443 -servername api.sophia-intel.ai

# Verify cert-manager configuration
kubectl get certificates -n sophia-intel
```

**Service Deployment Issues**
```bash
# Check Pulumi deployment status
pulumi stack output infrastructure_status

# View deployment logs
pulumi logs --follow

# Check application deployment
pulumi stack output application_deployment
```

This enterprise infrastructure provides a robust, scalable, and maintainable foundation for the Sophia Intel platform with proper containerization, infrastructure as code, and automated deployment capabilities.



## Frontend Configuration (Critical)

### Vite Host Restrictions Fix

**IMPORTANT**: The React dashboard uses Vite for development and preview servers. By default, Vite only responds to localhost requests for security reasons. For external access (including production domains), you MUST configure the host settings.

#### Required Vite Configuration

In `apps/dashboard/vite.config.js`, ensure the following configuration:

```javascript
export default defineConfig({
  // ... other config
  preview: {
    host: '0.0.0.0',        // Listen on all addresses
    port: 8080,             // Production port
    strictPort: false,
    allowedHosts: true      // CRITICAL: Allow any host
  }
})
```

#### Why This Matters

- **Without `host: '0.0.0.0'`**: Server only listens on localhost
- **Without `allowedHosts: true`**: Vite blocks external domains with "This host is not allowed" error
- **Result**: Blank screens, CORS errors, and inaccessible dashboard

#### Alternative Configuration (More Secure)

For production environments where you want to restrict hosts:

```javascript
preview: {
  host: '0.0.0.0',
  port: 8080,
  allowedHosts: ['sophia-intel.ai', 'www.sophia-intel.ai', 'localhost']
}
```

#### Troubleshooting

If you see:
- Blank screens on external domains
- "This host is not allowed" errors
- CORS-related issues

Check your Vite configuration and ensure `allowedHosts` is properly set.


