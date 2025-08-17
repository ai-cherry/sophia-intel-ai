# SOPHIA Intel Railway Deployment Guide

## Overview

This document outlines the complete deployment architecture for SOPHIA Intel on Railway, integrated with Lambda Labs GH200 GPU servers for high-performance inference.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   MCP Server    │    │ Lambda Labs     │
│   (Railway)     │◄──►│   (Railway)     │◄──►│ GH200 Servers   │
│   Port: 8000    │    │   Port: 8001    │    │ 192.222.51.223  │
└─────────────────┘    └─────────────────┘    │ 192.222.50.242  │
         │                       │             └─────────────────┘
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │ Monitoring      │
│   (Railway)     │    │ Stack (Railway) │
│   Port: 3000    │    │ Port: 8002      │
└─────────────────┘    └─────────────────┘
```

## Services

### 1. API Gateway (`api-gateway/`)
- **Purpose**: Main FastAPI application with LangChain integration
- **Port**: 8000
- **Health Check**: `/health`
- **Dependencies**: FastAPI, LangChain, OpenAI, Prometheus

### 2. MCP Server (`mcp-server/`)
- **Purpose**: Model Control Plane for Lambda Labs GPU management
- **Port**: 8001
- **Health Check**: `/health`
- **Dependencies**: FastAPI, MCP, WebSockets, HTTPX

### 3. Dashboard (`apps/dashboard/`)
- **Purpose**: React frontend for SOPHIA Intel
- **Port**: 3000
- **Build**: Vite + React
- **Dependencies**: React, Vite, TailwindCSS

### 4. Monitoring Stack (`monitoring-stack/`)
- **Purpose**: Health checks, metrics, and observability
- **Port**: 8002
- **Health Check**: `/health`
- **Dependencies**: Prometheus, Grafana, Sentry

## Environment Variables

### Global Variables (All Services)
```bash
ENVIRONMENT=production
RAILWAY_PROJECT_ID=381dde06-1aff-40b2-a1c9-470a2acabe3f
```

### API Gateway
```bash
PORT=8000
OPENROUTER_API_KEY=<openrouter-api-key>
LANGCHAIN_API_KEY=<langchain-api-key>
MCP_SERVER_URL=http://mcp-server.railway.internal:8001
SENTRY_DSN=<sentry-dsn>
PROMETHEUS_PORT=9090
```

### MCP Server
```bash
PORT=8001
LAMBDA_API_KEY=secret_sophiacloudapi_17cf7f3cedca48f18b4b8ea46cbb258f
LAMBDA_PRIMARY_URL=http://192.222.51.223:8000
LAMBDA_SECONDARY_URL=http://192.222.50.242:8000
API_GATEWAY_URL=http://api-gateway.railway.internal:8000
```

### Dashboard
```bash
PORT=3000
VITE_API_URL=https://api-gateway-production.up.railway.app
VITE_ENVIRONMENT=production
```

### Monitoring Stack
```bash
PORT=8002
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
SENTRY_DSN=<sentry-dsn>
```

## Lambda Labs Integration

### GH200 Server Configuration
- **Server A**: 192.222.51.223 (sophia-inference-gh200-1)
- **Server B**: 192.222.50.242 (sophia-inference-gh200-2)
- **SSH Key**: Sophia Production Key (Ed25519)
- **Firewall**: Ports 22 (SSH), 8000 (API), 443 (HTTPS)

### Required Software on GH200 Servers
```bash
# NVIDIA Drivers & CUDA
sudo apt update
sudo apt install -y nvidia-driver-535 cuda-toolkit-12-1

# Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Python & Dependencies
sudo apt install -y python3.11 python3.11-pip
pip3 install vllm fastapi uvicorn torch transformers
```

### Inference API Setup
Each GH200 server runs a containerized inference API:
```dockerfile
FROM nvidia/cuda:12.1-runtime-ubuntu22.04
RUN pip install vllm fastapi uvicorn
COPY inference_server.py /app/
WORKDIR /app
EXPOSE 8000
CMD ["uvicorn", "inference_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Deployment Commands

### Railway CLI Setup
```bash
export RAILWAY_TOKEN=32f097ac-7c3a-4a81-8385-b4ce98a2ca1f
railway login --token $RAILWAY_TOKEN
railway link --project 381dde06-1aff-40b2-a1c9-470a2acabe3f
```

### Deploy All Services
```bash
# API Gateway
cd api-gateway && railway up --service=api-gateway

# MCP Server
cd ../mcp-server && railway up --service=mcp-server

# Dashboard
cd ../apps/dashboard && railway up --service=dashboard

# Monitoring Stack
cd ../../monitoring-stack && railway up --service=monitoring
```

## Health Checks

All services expose health endpoints:
- **API Gateway**: `GET /health`
- **MCP Server**: `GET /health`
- **Monitoring**: `GET /health`
- **Lambda Labs**: `GET /health` (on each GH200 server)

## Security

### Secrets Management
- All API keys stored in Railway environment variables
- No hardcoded credentials in code
- SSH keys managed via Railway secrets
- TLS/HTTPS enforced for all external communication

### Network Security
- Railway internal networking for service-to-service communication
- Lambda Labs firewall configured for minimal attack surface
- VPN/WireGuard for secure Lambda Labs access (optional)

## Monitoring & Observability

### Metrics
- Prometheus metrics exposed on `/metrics` endpoints
- Custom metrics for inference latency, model usage, error rates
- Railway built-in monitoring for resource usage

### Logging
- Structured JSON logging with correlation IDs
- Centralized log aggregation via Railway
- Error tracking with Sentry integration

### Alerting
- Health check failures
- High error rates (>5%)
- Resource exhaustion (CPU >80%, Memory >90%)
- Lambda Labs server unavailability

## Scaling

### Horizontal Scaling
- Railway auto-scaling based on CPU/memory usage
- Load balancing between multiple Lambda Labs servers
- Database connection pooling

### Vertical Scaling
- Railway plan upgrades for increased resources
- Lambda Labs instance type upgrades (GH200 → H100)

## Troubleshooting

### Common Issues
1. **Service startup failures**: Check environment variables and dependencies
2. **Lambda Labs connectivity**: Verify firewall rules and SSH access
3. **High latency**: Check Lambda Labs server health and load balancing
4. **Memory issues**: Monitor Railway resource usage and upgrade plans

### Debug Commands
```bash
# Check service logs
railway logs --service=api-gateway

# Connect to Lambda Labs servers
ssh -i sophia_production_key ubuntu@192.222.51.223

# Test health endpoints
curl https://api-gateway-production.up.railway.app/health
curl http://192.222.51.223:8000/health
```

## Maintenance

### Regular Tasks
- Monitor Lambda Labs server health and resource usage
- Update dependencies and security patches
- Rotate API keys and SSH keys quarterly
- Review and optimize Railway resource allocation

### Backup & Recovery
- Database backups via Railway managed services
- Configuration backups in Git repository
- Lambda Labs server snapshots (if supported)
- Disaster recovery procedures documented

## Support

For deployment issues or questions:
- Check Railway dashboard for service status
- Review logs via `railway logs`
- Monitor health endpoints
- Contact Lambda Labs support for GPU server issues

