# SOPHIA Intel - Comprehensive Deployment Guide

## 🎯 Overview

This guide provides complete instructions for deploying SOPHIA Intel with Lambda Labs GH200 inference servers, Railway hosting, and full production monitoring.

## 📋 Prerequisites

### Required Accounts & Services
- **Lambda Labs**: GH200 server instances
- **Railway**: Application hosting platform
- **GitHub**: Source code repository
- **OpenRouter**: AI model API access
- **Airbyte**: Data pipeline integration (optional)

### Required Credentials
- Lambda Labs API key
- Railway deployment token
- GitHub Personal Access Token
- OpenRouter API key
- SSH key pair for Lambda Labs servers

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Lambda Labs   │    │     Railway     │    │   Monitoring    │
│   GH200 Servers │    │    Services     │    │   Dashboard     │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Primary Server  │◄───┤ MCP Server      │◄───┤ Health Checks   │
│ Secondary Server│    │ Orchestrator    │    │ Alerts          │
│ Inference APIs  │    │ API Gateway     │    │ Metrics         │
└─────────────────┘    │ Dashboard       │    └─────────────────┘
                       └─────────────────┘
```

## 🚀 Phase 1: Lambda Labs GH200 Setup

### 1.1 Server Provisioning
```bash
# Servers should already be provisioned with:
# - Primary: sophia-gh200-primary-us-east-3 (192.222.51.223)
# - Secondary: sophia-gh200-secondary-us-east-3 (192.222.50.242)
# - Instance Type: gpu_1x_gh200 (96GB GPU memory)
# - Region: us-east-3 (Washington DC)
```

### 1.2 SSH Key Configuration
```bash
# Add your SSH private key to ~/.ssh/
chmod 600 ~/.ssh/lambda_labs_key

# Test connectivity
ssh -i ~/.ssh/lambda_labs_key ubuntu@192.222.51.223
ssh -i ~/.ssh/lambda_labs_key ubuntu@192.222.50.242
```

### 1.3 Server Setup Script
```bash
# Run the production setup script on both servers
./scripts/setup_lambda_production.sh

# This script installs:
# - Docker & NVIDIA Container Toolkit
# - CUDA drivers and GPU support
# - Inference server containers
# - Health monitoring endpoints
# - Security configurations (UFW firewall)
```

### 1.4 Verify Server Setup
```bash
# Check GPU availability
ssh -i ~/.ssh/lambda_labs_key ubuntu@192.222.51.223 "nvidia-smi"

# Test inference endpoint
curl http://192.222.51.223:8000/health
curl http://192.222.50.242:8000/health
```

## 🛠️ Phase 2: MCP Server Deployment

### 2.1 Environment Configuration
```bash
# Copy comprehensive environment template
cp .env.comprehensive.example .env

# Configure Lambda Labs settings
LAMBDA_API_KEY=your_lambda_labs_api_key_here
LAMBDA_PRIMARY_URL=http://192.222.51.223:8000
LAMBDA_SECONDARY_URL=http://192.222.50.242:8000
```

### 2.2 MCP Server Features
- **Authentication**: Token-based API security
- **Lifecycle Management**: Start/stop/restart Lambda servers
- **Health Monitoring**: Real-time server status
- **Statistics**: GPU utilization and performance metrics
- **Error Handling**: Comprehensive logging and recovery

### 2.3 Local Testing
```bash
# Install dependencies
cd mcp-server
pip install -r requirements.txt

# Run tests
python -m pytest test_mcp_server.py -v

# Start MCP server
python mcp_server.py
```

### 2.4 API Endpoints
```
GET  /health                    - Server health check
GET  /servers                   - List all Lambda servers
POST /servers/{key}/start       - Start server
POST /servers/{key}/stop        - Stop server
POST /servers/{key}/restart     - Restart server
GET  /servers/{key}/stats       - Get server statistics
POST /servers/rename            - Rename servers
```

## 🚢 Phase 3: Railway Deployment

### 3.1 Service Architecture
```
Railway Services:
├── mcp-server              (Lambda Labs management)
├── orchestrator            (Core AI orchestration)
├── api-gateway            (API routing & rate limiting)
├── dashboard              (Monitoring dashboard)
├── postgres               (Primary database)
├── redis                  (Caching & sessions)
└── qdrant                 (Vector database)
```

### 3.2 Deployment Configuration
```bash
# Set Railway token
export RAILWAY_TOKEN=your_railway_token_here

# Deploy services using Railway CLI or GitHub Actions
railway deploy
```

### 3.3 Environment Variables (Railway)
```bash
# Core settings
ENVIRONMENT=production
LAMBDA_API_KEY=your_lambda_labs_api_key
MCP_AUTH_TOKEN=your_secure_mcp_token

# Database connections
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
QDRANT_URL=https://...

# AI providers
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=your_openai_key
```

## 📊 Phase 4: Monitoring Dashboard

### 4.1 Dashboard Features
- **Real-time Health Checks**: All services monitored concurrently
- **Interactive Charts**: Response time trends and health distribution
- **Alert System**: Slack and email notifications
- **Service Management**: Individual service details and recommendations

### 4.2 Dashboard Configuration
```bash
# Environment variables for monitoring
DASHBOARD_PORT=8090
HEALTH_CHECK_INTERVAL=30
ALERT_UNHEALTHY_THRESHOLD=2
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### 4.3 Access Dashboard
```
Local: http://localhost:8090
Production: https://dashboard-production.up.railway.app
```

## 🔧 Phase 5: CLI Management

### 5.1 CLI Installation
```bash
# Install CLI dependencies
pip install click requests

# Make CLI executable
chmod +x cli/sophia_cli.py
```

### 5.2 CLI Commands
```bash
# List Lambda Labs servers
python cli/sophia_cli.py lambda-servers list

# Start/stop servers
python cli/sophia_cli.py lambda-servers start primary
python cli/sophia_cli.py lambda-servers stop secondary

# Get server statistics
python cli/sophia_cli.py lambda-servers stats primary

# Rename servers with proper convention
python cli/sophia_cli.py lambda-servers rename --force
```

### 5.3 Authentication
```bash
# Set MCP authentication token
export MCP_AUTH_TOKEN=your_mcp_token_here

# Or use CLI option
python cli/sophia_cli.py lambda-servers list --token your_token_here
```

## 🔒 Security Configuration

### 6.1 API Security
- **Authentication**: MCP token-based authentication
- **Rate Limiting**: Configurable request limits
- **CORS**: Restricted origins for production
- **Firewall**: UFW configured on Lambda Labs servers

### 6.2 Network Security
```bash
# Lambda Labs servers expose only required ports:
# - 22 (SSH)
# - 8000 (Inference API)
# - 8001 (Health monitoring)
```

### 6.3 Secrets Management
- Environment variables for all sensitive data
- No hardcoded credentials in source code
- Separate development and production configurations

## 📈 Monitoring & Alerting

### 7.1 Health Check Endpoints
```
MCP Server:     /health
Orchestrator:   /health
API Gateway:    /health
Lambda Primary: /health
Lambda Secondary: /health
```

### 7.2 Alert Conditions
- **Unhealthy Services**: ≥2 services down
- **Response Time**: >5 seconds average
- **Lambda Servers**: ≥1 server down
- **GPU Utilization**: Custom thresholds

### 7.3 Alert Channels
- **Slack**: Real-time notifications
- **Email**: Critical alerts
- **Dashboard**: Visual indicators

## 🧪 Testing & Validation

### 8.1 Unit Tests
```bash
# MCP Server tests
cd mcp-server && python -m pytest test_mcp_server.py -v

# Expected: 22/22 tests passing
```

### 8.2 Integration Tests
```bash
# Test Lambda Labs connectivity
curl -H "X-MCP-Token: $MCP_AUTH_TOKEN" \
  https://mcp-server-production.up.railway.app/servers

# Test inference endpoints
curl http://192.222.51.223:8000/health
curl http://192.222.50.242:8000/health
```

### 8.3 End-to-End Testing
```bash
# Test complete workflow
python cli/sophia_cli.py lambda-servers list
python cli/sophia_cli.py lambda-servers stats primary
```

## 🚨 Troubleshooting

### 9.1 Common Issues

#### Lambda Labs Server Not Responding
```bash
# Check server status
python cli/sophia_cli.py lambda-servers list

# Restart server if needed
python cli/sophia_cli.py lambda-servers restart primary

# Check logs via SSH
ssh -i ~/.ssh/lambda_labs_key ubuntu@192.222.51.223 "docker logs inference-server"
```

#### MCP Server Authentication Errors
```bash
# Verify token is set
echo $MCP_AUTH_TOKEN

# Test authentication
curl -H "X-MCP-Token: $MCP_AUTH_TOKEN" \
  https://mcp-server-production.up.railway.app/health
```

#### Railway Deployment Issues
```bash
# Check Railway service logs
railway logs

# Verify environment variables
railway variables
```

### 9.2 Performance Optimization

#### Lambda Labs Servers
- Monitor GPU utilization via dashboard
- Scale inference requests across both servers
- Use primary for real-time, secondary for batch

#### Railway Services
- Monitor response times in dashboard
- Scale services based on load
- Use Redis caching for frequently accessed data

## 📚 Additional Resources

### Documentation
- [Lambda Labs API Documentation](https://docs.lambdalabs.com/)
- [Railway Deployment Guide](https://docs.railway.app/)
- [OpenRouter API Reference](https://openrouter.ai/docs)

### Support
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Comprehensive guides and API references
- **Monitoring**: Real-time dashboard and alerting

## 🎯 Production Checklist

- [ ] Lambda Labs GH200 servers provisioned and configured
- [ ] SSH keys configured and tested
- [ ] MCP server deployed with authentication
- [ ] All Railway services deployed and healthy
- [ ] Environment variables configured
- [ ] Monitoring dashboard accessible
- [ ] Alert channels configured (Slack/Email)
- [ ] CLI tools installed and tested
- [ ] End-to-end testing completed
- [ ] Documentation reviewed and updated

## 🔄 Maintenance

### Regular Tasks
- Monitor server health via dashboard
- Review alert notifications
- Update environment variables as needed
- Scale services based on usage patterns
- Backup configuration and data

### Updates
- Keep Lambda Labs servers updated
- Deploy new versions via Railway
- Update CLI tools and dependencies
- Review and update security configurations

---

**SOPHIA Intel Production Deployment Complete** 🎉

Your SOPHIA Intel system is now fully deployed with Lambda Labs GH200 inference servers, Railway hosting, comprehensive monitoring, and production-ready management tools.

