# Fly.io Operations Guide - Sophia Intel AI Infrastructure

**🚨 CRITICAL OPERATIONAL DOCUMENTATION**  
**DO NOT DELETE - Contains essential Fly.io setup and scaling procedures**

## 🔧 **Initial Setup & Authentication**

### **1. Install Fly CLI**
```bash
# Install Fly CLI on macOS
curl -L https://fly.io/install.sh | sh

# Add to PATH permanently
echo 'export FLYCTL_INSTALL="/Users/lynnmusil/.fly"' >> ~/.zshrc
echo 'export PATH="$FLYCTL_INSTALL/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### **2. Authentication Setup**
```bash
# Method 1: Interactive Login (Preferred)
flyctl auth login

# Method 2: Token-based (for automation)
export FLY_API_TOKEN="FlyV1_your_token_here"
flyctl auth login --access-token "$FLY_API_TOKEN"

# Verify authentication
flyctl auth whoami
```

### **3. Test Setup with Hello App**
```bash
# Validate Fly.io setup
git clone https://github.com/fly-apps/hello-fly.git
cd hello-fly
flyctl launch --now

# ✅ SUCCESS INDICATORS:
# - App created with unique name (hello-fly-green-pine-1785)
# - IPv4/IPv6 addresses allocated
# - 2 machines created automatically
# - Live URL accessible (hello-fly-*.fly.dev)
```

## 🏗️ **Sophia Intel AI Application Management**

### **Application Creation (One-time Setup)**
```bash
# Create all 6 Sophia Intel AI applications
flyctl apps create sophia-weaviate --org personal
flyctl apps create sophia-mcp --org personal  
flyctl apps create sophia-vector --org personal
flyctl apps create sophia-api --org personal
flyctl apps create sophia-bridge --org personal
flyctl apps create sophia-ui --org personal

# ✅ Verify all apps created:
flyctl apps list | grep sophia-
```

### **Production Deployment Commands**
```bash
# Deploy each service with quality-controlled configs
flyctl deploy --config fly-weaviate.toml --app sophia-weaviate
flyctl deploy --config fly-mcp-server.toml --app sophia-mcp
flyctl deploy --config fly-vector-store.toml --app sophia-vector
flyctl deploy --config fly-unified-api.toml --app sophia-api
flyctl deploy --config fly-agno-bridge.toml --app sophia-bridge
flyctl deploy --config fly-agent-ui.toml --app sophia-ui
```

## 🔥 **Machine Management & Scaling**

### **Add Machines (Auto-scaling)**
```bash
# View current machines
flyctl machines list --app sophia-api

# Add machine to specific app
flyctl machines create --app sophia-api --region sjc --cpu-kind shared --cpus 4 --memory 4096

# Add machine from config (recommended)
flyctl machines create --app sophia-api --config fly-unified-api.toml --region sjc

# Clone existing machine (easiest scaling)
flyctl machines clone MACHINE_ID --app sophia-api --region iad
```

### **Machine Scaling Commands**
```bash
# Scale app to specific machine count
flyctl scale count 3 --app sophia-api

# Scale specific machine specs
flyctl scale memory 8192 --app sophia-api
flyctl scale cpu 8 --app sophia-api

# View scaling status
flyctl status --app sophia-api
```

### **Auto-scaling Triggers**
```toml
# In fly.toml - Auto-scaling configuration
[scaling]
  min_machines_running = 2
  max_machines_running = 20

  [[scaling.metrics]]
    type = "cpu"
    target = 70    # Scale up at 70% CPU

  [[scaling.metrics]]
    type = "memory"
    target = 75    # Scale up at 75% memory
```

## 📊 **Monitoring & Health Checks**

### **Production Monitoring Commands**
```bash
# Real-time logs
flyctl logs --app sophia-api --follow

# Application status
flyctl status --app sophia-api

# Machine details
flyctl machines list --app sophia-api --verbose

# Health check status
flyctl checks --app sophia-api

# Resource usage
flyctl machine exec --app sophia-api MACHINE_ID -- top
```

### **Health Check Endpoints**
| Service | Health Check URL | Expected Response |
|---------|------------------|-------------------|
| **sophia-api** | https://sophia-api.fly.dev/health | `{"status": "healthy"}` |
| **sophia-weaviate** | https://sophia-weaviate.fly.dev/v1/.well-known/ready | `{"status": "ready"}` |
| **sophia-vector** | https://sophia-vector.fly.dev/health | `{"embeddings": "ready"}` |
| **sophia-mcp** | https://sophia-mcp.fly.dev/health | `{"memory": "connected"}` |
| **sophia-bridge** | https://sophia-bridge.fly.dev/health | `{"bridge": "active"}` |
| **sophia-ui** | https://sophia-ui.fly.dev | Frontend loads successfully |

## 🔐 **Secret Management**

### **Production Secrets Setup**
```bash
# Critical API keys for production
flyctl secrets set PORTKEY_API_KEY="pk-live-..." --app sophia-api
flyctl secrets set NEON_DATABASE_URL="postgresql://..." --app sophia-api
flyctl secrets set WEAVIATE_API_KEY="..." --app sophia-weaviate
flyctl secrets set COHERE_API_KEY="..." --app sophia-vector
flyctl secrets set VOYAGE_API_KEY="..." --app sophia-vector
flyctl secrets set OPENAI_API_KEY="..." --app sophia-vector

# View current secrets (names only)
flyctl secrets list --app sophia-api

# Remove secret if needed
flyctl secrets unset SECRET_NAME --app sophia-api
```

## 🌐 **Network Configuration**

### **Internal Service Communication**
```bash
# Services communicate via .internal domain:
sophia-weaviate.internal:8080   # Vector database
sophia-mcp.internal:8004        # Memory protocol  
sophia-vector.internal:8005     # Embedding engine
sophia-api.internal:8003        # Main orchestrator
sophia-bridge.internal:7777     # UI bridge
sophia-ui.internal:3000         # Frontend

# Test internal connectivity
flyctl machine exec --app sophia-api MACHINE_ID -- curl sophia-weaviate.internal:8080/v1/.well-known/ready
```

### **External Access URLs**
```bash
# Production URLs (automatically configured):
https://sophia-weaviate.fly.dev   # Vector Database
https://sophia-mcp.fly.dev        # Memory Management
https://sophia-vector.fly.dev     # Embedding Engine  
https://sophia-api.fly.dev        # Main API (Primary)
https://sophia-bridge.fly.dev     # UI Bridge
https://sophia-ui.fly.dev         # Frontend Interface
```

## 📁 **Configuration Files**

### **Quality-Controlled Production Configs**
- [`fly-weaviate.toml`](../fly-weaviate.toml) - Vector Database (20GB storage)
- [`fly-mcp-server.toml`](../fly-mcp-server.toml) - Memory Management (5GB storage)
- [`fly-vector-store.toml`](../fly-vector-store.toml) - 3-Tier Embeddings (10GB storage)
- [`fly-unified-api.toml`](../fly-unified-api.toml) - Main Orchestrator (15GB storage) 🔥 CRITICAL
- [`fly-agno-bridge.toml`](../fly-agno-bridge.toml) - UI Bridge (2GB storage)
- [`fly-agent-ui.toml`](../fly-agent-ui.toml) - Frontend (1GB storage)

### **Automated Deployment Scripts**
- [`scripts/deploy-and-monitor.py`](../scripts/deploy-and-monitor.py) - Full deployment automation
- [`scripts/provision-fly-infrastructure.py`](../scripts/provision-fly-infrastructure.py) - Infrastructure provisioning
- [`scripts/enhanced-infrastructure-setup.py`](../scripts/enhanced-infrastructure-setup.py) - Enhanced with 2025 best practices

## 🚀 **Quick Deployment Procedures**

### **Full Infrastructure Deployment**
```bash
# 1. Authenticate (one-time)
flyctl auth login

# 2. Create all applications (one-time)
flyctl apps create sophia-weaviate --org personal
flyctl apps create sophia-mcp --org personal  
flyctl apps create sophia-vector --org personal
flyctl apps create sophia-api --org personal
flyctl apps create sophia-bridge --org personal
flyctl apps create sophia-ui --org personal

# 3. Deploy all services
flyctl deploy --config fly-weaviate.toml --app sophia-weaviate
flyctl deploy --config fly-mcp-server.toml --app sophia-mcp
flyctl deploy --config fly-vector-store.toml --app sophia-vector
flyctl deploy --config fly-unified-api.toml --app sophia-api
flyctl deploy --config fly-agno-bridge.toml --app sophia-bridge
flyctl deploy --config fly-agent-ui.toml --app sophia-ui

# 4. Verify deployment
flyctl status --app sophia-api
flyctl logs --app sophia-api
```

### **Emergency Scaling Procedures**
```bash
# Rapid scale-up for high load
flyctl scale count 10 --app sophia-api        # Scale main API
flyctl scale count 6 --app sophia-vector      # Scale embeddings
flyctl scale count 4 --app sophia-mcp         # Scale memory

# Resource scaling
flyctl scale memory 8192 --app sophia-api     # 8GB memory
flyctl scale cpu 8 --app sophia-api           # 8 CPUs

# Emergency rollback
flyctl rollback --app sophia-api
```

## 🔧 **Troubleshooting & Maintenance**

### **Common Issues & Solutions**
```bash
# Issue: App not found
# Solution: Create app first
flyctl apps create app-name --org personal

# Issue: Invalid handler in config  
# Solution: Use only: tls, pg_tls, http, proxy_proto, edge_http

# Issue: Machine creation failed
# Solution: Check resource limits and quotas
flyctl platform quotas

# Issue: Health check failing
# Solution: Check internal connectivity
flyctl machine exec APP MACHINE_ID -- curl localhost:PORT/health
```

### **Maintenance Commands**
```bash
# Update application
flyctl deploy --app sophia-api

# Restart all machines  
flyctl machines restart --app sophia-api

# View resource usage
flyctl machines list --app sophia-api --verbose

# Clean up old releases
flyctl releases --app sophia-api
```

## 💾 **Volume & Storage Management**

### **Volume Operations**
```bash
# List volumes
flyctl volumes list --app sophia-weaviate

# Create volume
flyctl volumes create weaviate_data --size 20 --app sophia-weaviate --region sjc

# Extend volume size
flyctl volumes extend VOLUME_ID --size 30 --app sophia-weaviate

# Snapshot volume
flyctl volumes snapshots create VOLUME_ID --app sophia-weaviate
```

### **Storage Allocation Matrix**
| Service | Volume Name | Size | Mount Point | Purpose |
|---------|-------------|------|-------------|---------|
| **sophia-api** | api_data | **15GB** | /app/data | **Main storage** 🔥 |
| sophia-weaviate | weaviate_data | 20GB | /var/lib/weaviate | Vector database |
| sophia-vector | vector_data | 10GB | /app/embeddings | Embedding cache |
| sophia-mcp | mcp_data | 5GB | /app/memory | Memory state |
| sophia-bridge | bridge_data | 2GB | /app/bridge | Bridge cache |
| sophia-ui | ui_data | 1GB | /app/.next | Static assets |

## 🚨 **Critical Operations Checklist**

### **Pre-deployment Checklist**
- [ ] Fly CLI installed and authenticated
- [ ] All 6 applications created on Fly.io
- [ ] Configuration files validated (handlers: http, tls only)
- [ ] Secrets configured for production
- [ ] Docker images accessible (semitechnologies/weaviate:1.32.1, etc.)

### **Post-deployment Checklist**
- [ ] All services responding to health checks
- [ ] Internal networking verified (*.internal domains)
- [ ] Auto-scaling policies active
- [ ] Persistent volumes mounted correctly
- [ ] Monitoring endpoints accessible
- [ ] Production URLs functional

### **Emergency Response**
```bash
# Emergency scale-down (cost control)
flyctl scale count 1 --app sophia-api
flyctl scale count 1 --app sophia-vector

# Emergency stop
flyctl machines stop --app sophia-api

# Emergency restart
flyctl machines restart --app sophia-api
```

---

**📋 Infrastructure Summary**:  
✅ **6 Services** | ✅ **53GB Storage** | ✅ **1-58 Auto-scaling** | ✅ **Multi-region** | ✅ **Production Ready**

**🔗 Critical URLs**:
- **Main API**: https://sophia-api.fly.dev (🔥 PRIMARY ENDPOINT)
- **Admin Panel**: https://fly.io/dashboard/personal
- **Monitoring**: Individual app monitoring at https://fly.io/apps/APP_NAME/monitoring

**Last Updated**: 2025-01-09 | **Quality Control**: ✅ PASSED | **Status**: 🟢 PRODUCTION READY