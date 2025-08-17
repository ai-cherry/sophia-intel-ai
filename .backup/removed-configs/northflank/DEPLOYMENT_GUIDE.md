# SOPHIA Intel Northflank Deployment Guide

## Manual Deployment Instructions

Since the API token appears to be a template token with limited permissions, follow these steps to deploy SOPHIA Intel to Northflank manually:

### 1. Access Northflank Dashboard
- Go to https://app.northflank.com
- Login to the **payready** team
- Navigate to the **sophia3** project (or create it if it doesn't exist)

### 2. Create Secret Groups
Create a secret group named `sophia-secrets-prod` with these secrets:
```
LAMBDA_API_KEY: secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f.EsLXt0lkGlhZ1Nd369Ld5DMSuhJg9O9y
DNSIMPLE_API_KEY: dnsimple_u_XBHeyhH3O8uKJF6HnqU76h7ANWdNvUzN
NOTION_API_KEY: [Your Notion API key]
QDRANT_URL: [Your Qdrant vector database URL]
```

### 3. Create Database Addons
1. **PostgreSQL Addon**:
   - Name: `sophia-postgres`
   - Version: PostgreSQL 15
   - Plan: nf-compute-20
   - Database: `sophia_intel`
   - Username: `sophia`

2. **Redis Addon**:
   - Name: `sophia-redis`
   - Version: Redis 7
   - Plan: nf-compute-10

### 4. Deploy Services

#### A. SOPHIA API Service
- **Name**: `sophia-api`
- **Source**: GitHub repository `ai-cherry/sophia-intel`
- **Branch**: `main`
- **Dockerfile**: `/northflank/docker/sophia-api.Dockerfile`
- **Port**: 8000 (public)
- **Domain**: `api.sophia-intel.ai`
- **Plan**: nf-compute-40
- **Instances**: 2
- **Environment Variables**:
  ```
  LAMBDA_API_KEY: @{secrets.sophia-secrets-prod.LAMBDA_API_KEY}
  POSTGRES_URL: @{addons.sophia-postgres.connectionString}
  REDIS_URL: @{addons.sophia-redis.connectionString}
  ENVIRONMENT: production
  LOG_LEVEL: info
  ```

#### B. SOPHIA Dashboard Service
- **Name**: `sophia-dashboard`
- **Source**: GitHub repository `ai-cherry/sophia-intel`
- **Branch**: `main`
- **Dockerfile**: `/northflank/docker/sophia-dashboard.Dockerfile`
- **Port**: 80 (public)
- **Domains**: `www.sophia-intel.ai`, `app.sophia-intel.ai`
- **Plan**: nf-compute-20
- **Instances**: 2
- **Build Arguments**:
  ```
  VITE_API_URL: https://api.sophia-intel.ai
  ```
- **Environment Variables**:
  ```
  VITE_API_URL: https://api.sophia-intel.ai
  NODE_ENV: production
  ```

#### C. SOPHIA MCP Services
Create these as separate services:

1. **Memory Service**:
   - **Name**: `sophia-mcp-memory`
   - **Dockerfile**: `/northflank/docker/sophia-mcp.Dockerfile`
   - **Port**: 8001 (internal)
   - **Environment**: `MCP_SERVICE_TYPE: memory`

2. **Notion Service**:
   - **Name**: `sophia-mcp-notion`
   - **Dockerfile**: `/northflank/docker/sophia-mcp.Dockerfile`
   - **Port**: 8002 (internal)
   - **Environment**: `MCP_SERVICE_TYPE: notion`

### 5. Configure DNS
Update your DNS records to point to Northflank:
- `www.sophia-intel.ai` → Northflank dashboard service
- `api.sophia-intel.ai` → Northflank API service
- `app.sophia-intel.ai` → Northflank dashboard service

### 6. Verify Deployment
1. Check all services are running and healthy
2. Test API endpoints: `https://api.sophia-intel.ai/health`
3. Test dashboard: `https://www.sophia-intel.ai`
4. Test chat functionality with Lambda AI integration

### 7. Monitor and Scale
- Set up monitoring and alerting
- Configure auto-scaling based on traffic
- Monitor costs and optimize resource allocation

## Files Created for Deployment
- `/northflank/templates/sophia-template.json` - IaC template
- `/northflank/docker/sophia-api.Dockerfile` - API service Docker config
- `/northflank/docker/sophia-dashboard.Dockerfile` - Dashboard Docker config
- `/northflank/docker/sophia-mcp.Dockerfile` - MCP services Docker config
- `/northflank/docker/nginx.conf` - Nginx configuration
- `/STACK_INVENTORY.md` - Complete architecture overview

## Troubleshooting
- If builds fail, check Dockerfile paths and dependencies
- If services don't start, verify environment variables
- If domains don't resolve, check DNS propagation
- If API calls fail, verify CORS and authentication settings

## Next Steps After Deployment
1. Set up CI/CD pipelines for automated deployments
2. Configure monitoring and logging
3. Set up backup strategies for databases
4. Implement security scanning and updates
5. Optimize performance and costs

