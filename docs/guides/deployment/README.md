---
title: Unified Deployment Guide
type: guide
status: active
version: 2.0.0
last_updated: 2024-09-01
ai_context: high
dependencies: []
tags: [deployment, fly.io, pulumi, infrastructure]
---

# 🚀 Unified Deployment Guide

## 🎯 Purpose
Single source of truth for deploying Sophia Intel AI across all environments.

## 📋 Prerequisites
- Python 3.11+
- Node.js 18+
- Docker
- Fly.io CLI (for cloud deployment)
- Pulumi CLI (for infrastructure as code)

## 🔧 Implementation

### Local Development
```bash
# Quick start
./scripts/start-local.sh

# With monitoring
./scripts/start-mcp-system.sh
```

### Cloud Deployment (Fly.io)
```bash
# Deploy all services
fly deploy --config fly.api.toml
fly deploy --config fly.ui.toml
```

### Infrastructure as Code (Pulumi)
```bash
# Deploy infrastructure
cd infra/pulumi
pulumi up
```

## ✅ Validation
- Health check: http://localhost:8000/health
- Metrics: http://localhost:9090
- UI: http://localhost:3000

## 🚨 Common Issues
See TROUBLESHOOTING.md

## 📚 Related
- [Architecture Overview](../../architecture/system-design.md)
- [API Documentation](../../api/rest-api.md)
- [Monitoring Guide](../operations/monitoring.md)
