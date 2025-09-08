# Sophia Intel AI - Automated Startup System

A comprehensive, production-ready automated startup system for the Sophia Intel AI platform that works across local development and cloud deployment environments.

## 🎯 Overview

This automation system provides:
- **Cross-platform startup automation** (macOS, Linux, Windows)
- **Environment-aware configuration management** 
- **Production-ready orchestration** (Docker Compose, Kubernetes, Helm)
- **Comprehensive health monitoring** and auto-recovery
- **System service integration** (systemd, launchd)

## 🚀 Quick Start

### 1. Universal Startup (Auto-Detection)

```bash
# Auto-detect environment and start all services
./automation/scripts/sophia-start.sh

# Windows PowerShell
.\automation\scripts\sophia-start.ps1
```

### 2. Specific Environment

```bash
# Development with Docker Compose
./automation/scripts/sophia-start.sh --mode=docker --environment=development

# Production Kubernetes
./automation/scripts/sophia-start.sh --mode=kubernetes --environment=production

# Staging with Helm
./automation/scripts/sophia-start.sh --mode=helm --environment=staging
```

## 📁 Directory Structure

```
automation/
├── config/                          # Configuration management
│   ├── system.yaml                  # Central system configuration
│   ├── startup-local.yaml          # Local development settings
│   └── startup-production.yaml     # Production settings
├── docker/                         # Docker configurations
│   ├── Dockerfile.unified-api      # Unified API container
│   ├── Dockerfile.sophia           # Sophia Orchestrator
│   └── Dockerfile.health-monitor   # Health monitoring service
├── monitoring/                     # Monitoring and observability
│   ├── prometheus/                 # Prometheus configuration
│   │   ├── prometheus.yml         # Prometheus config
│   │   └── rules/                 # Alert rules
│   └── grafana/                   # Grafana dashboards
│       └── dashboards/            # Pre-built dashboards
├── scripts/                       # Automation scripts
│   ├── sophia-start.sh           # Universal startup (Unix)
│   ├── sophia-start.ps1          # Universal startup (Windows)
│   ├── startup-manager.sh        # Advanced startup manager
│   ├── health-check.py           # Health monitoring
│   ├── config-manager.py         # Configuration management
│   └── entrypoint.sh            # Docker entrypoint
├── system-services/               # System service files
│   ├── linux/                   # systemd services
│   │   └── sophia-intel-ai.service
│   └── macos/                   # launchd agents
│       └── com.sophia.intel.ai.plist
└── templates/                    # Configuration templates
    ├── docker-compose.yml.j2    # Docker Compose template
    ├── kubernetes/              # Kubernetes templates
    └── monitoring/              # Monitoring templates
```

## 🔧 Configuration System

### Central Configuration

The system uses `automation/config/system.yaml` as the central configuration source:

```yaml
# Environment profiles
profiles:
  development:
    enabled: true
    auto_recovery: true
    health_check_interval: 30
    log_level: "INFO"
    
  production:
    enabled: true
    auto_recovery: true
    health_check_interval: 60
    log_level: "ERROR"
```

### Environment-Specific Configuration

Generate configurations for different environments:

```bash
# Generate development configuration
python3 automation/scripts/config-manager.py --environment=development --action=generate

# Validate production configuration
python3 automation/scripts/config-manager.py --environment=production --action=validate

# Export configuration as JSON
python3 automation/scripts/config-manager.py --action=export --format=json
```

## 🐳 Docker Deployment

### Enhanced Docker Compose

The system provides an enhanced Docker Compose configuration with:
- **Tiered startup ordering** (Infrastructure → Applications → Monitoring)
- **Advanced health checks** with startup probes
- **Resource limits** and performance optimization
- **Auto-recovery** and restart policies

```bash
# Start with enhanced configuration
docker-compose -f docker-compose.enhanced.yml up -d

# Check service health
docker-compose -f docker-compose.enhanced.yml ps
```

### Services Included

1. **Infrastructure Tier (Tier 1)**
   - Redis (cache and messaging)
   - PostgreSQL (persistent storage)
   - Weaviate (vector database)

2. **Application Tier (Tier 2)**
   - Unified API Server
   - Sophia Orchestrator
   - Artemis Orchestrator

3. **Monitoring Tier (Tier 3)**
   - Prometheus (metrics collection)
   - Grafana (visualization)
   - Health Monitor (system health)

## ☸️ Kubernetes Deployment

### Kubernetes Manifests

Production-ready Kubernetes deployment with:

```bash
# Deploy to Kubernetes
kubectl apply -k k8s/base/

# Check deployment status
kubectl get all -n sophia-intel-ai

# View logs
kubectl logs -f deployment/unified-api -n sophia-intel-ai
```

### Features

- **Namespace isolation** with RBAC
- **StatefulSets** for stateful services
- **Persistent volumes** with SSD storage class
- **Service discovery** and load balancing
- **Auto-scaling** with HPA
- **Security policies** and network policies

## ⚓ Helm Deployment

### Helm Charts

Flexible Helm deployment for multiple environments:

```bash
# Install with Helm
helm install sophia-intel-ai ./helm/sophia-intel-ai \
  --namespace sophia-intel-ai \
  --create-namespace \
  --values ./helm/sophia-intel-ai/values-production.yaml

# Upgrade deployment
helm upgrade sophia-intel-ai ./helm/sophia-intel-ai

# View status
helm status sophia-intel-ai
```

### Values Configuration

Environment-specific values files:
- `values-development.yaml` - Local development
- `values-staging.yaml` - Staging environment  
- `values-production.yaml` - Production deployment

## 🏥 Health Monitoring

### Comprehensive Health Checks

The system includes a comprehensive health monitoring service:

```python
# Run health check
python3 automation/scripts/health-check.py --check-only

# Start health monitoring server
python3 automation/scripts/health-check.py --port=8888
```

### Health Endpoints

- `GET /health` - Overall system health
- `GET /health/ready` - Kubernetes readiness probe
- `GET /health/live` - Kubernetes liveness probe
- `GET /health/detailed` - Detailed component status
- `GET /metrics` - Prometheus metrics

### Monitored Components

- **Infrastructure**: Redis, PostgreSQL, Weaviate
- **Applications**: Unified API, Orchestrators
- **System**: CPU, Memory, Disk usage
- **Network**: Response times, error rates

## 📊 Monitoring and Observability

### Prometheus Integration

The system includes pre-configured Prometheus monitoring:

- **Service discovery** for dynamic targets
- **Alert rules** for critical conditions
- **Custom metrics** for business logic
- **Long-term storage** configuration

### Grafana Dashboards

Pre-built dashboards for:
- **System Overview** - Service health and performance
- **Infrastructure Metrics** - Database and cache status
- **Application Metrics** - Request rates and response times
- **Resource Usage** - CPU, memory, and disk utilization

### Alerting

Comprehensive alerting rules for:
- **Service availability** (down/degraded)
- **Performance issues** (high latency/error rate)
- **Resource exhaustion** (CPU/memory/disk)
- **Business metrics** (low success rate)

## 🔒 Security Features

### Production Security

- **Pod Security Standards** (restricted)
- **Network Policies** for traffic isolation
- **RBAC** with least-privilege access
- **Secret management** for sensitive data
- **TLS encryption** for all communications

### Development Security

- **CORS configuration** for local development
- **Health check authentication** bypass
- **Debug mode** controls
- **Local certificate** generation

## 🔄 Auto-Recovery

### Intelligent Recovery

The system provides multiple layers of auto-recovery:

1. **Container Level** - Docker restart policies
2. **Service Level** - Health check failures
3. **System Level** - Process monitoring
4. **Application Level** - Circuit breakers

### Recovery Strategies

- **Immediate restart** for critical services
- **Exponential backoff** for failing components
- **Circuit breaker** patterns for external dependencies
- **Graceful degradation** for non-critical features

## 🛠️ System Services

### macOS (launchd)

Install as system service on macOS:

```bash
# Install service
cp automation/system-services/macos/com.sophia.intel.ai.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.sophia.intel.ai.plist

# Check status
launchctl list | grep sophia

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.sophia.intel.ai.plist
```

### Linux (systemd)

Install as system service on Linux:

```bash
# Install service
sudo cp automation/system-services/linux/sophia-intel-ai.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sophia-intel-ai
sudo systemctl start sophia-intel-ai

# Check status
sudo systemctl status sophia-intel-ai

# View logs
sudo journalctl -u sophia-intel-ai -f
```

## 📋 Operational Commands

### Common Operations

```bash
# Start all services
./automation/scripts/sophia-start.sh start

# Stop all services
./automation/scripts/sophia-start.sh stop

# Restart services
./automation/scripts/sophia-start.sh restart

# Check status
./automation/scripts/sophia-start.sh status

# Install dependencies
./automation/scripts/sophia-start.sh install

# Setup configuration
./automation/scripts/sophia-start.sh config

# Run health check
./automation/scripts/sophia-start.sh health
```

### Development Workflow

```bash
# Start development environment
./automation/scripts/sophia-start.sh --mode=development --verbose

# Generate configurations
python3 automation/scripts/config-manager.py --environment=development --action=generate

# Validate setup
python3 automation/scripts/health-check.py --check-only --format=text

# View logs
docker-compose -f docker-compose.enhanced.yml logs -f
```

### Production Deployment

```bash
# Validate production configuration
python3 automation/scripts/config-manager.py --environment=production --action=validate

# Deploy to Kubernetes
./automation/scripts/sophia-start.sh --mode=kubernetes --environment=production

# Check deployment health
kubectl get pods -n sophia-intel-ai
python3 automation/scripts/health-check.py --check-only

# Monitor metrics
curl http://prometheus:9090/api/v1/query?query=up
```

## 🔧 Troubleshooting

### Common Issues

1. **Services won't start**
   - Check dependencies: `./automation/scripts/sophia-start.sh install`
   - Verify configuration: `python3 automation/scripts/config-manager.py --action=validate`
   - Review logs: `docker-compose logs service-name`

2. **Health checks failing**
   - Run detailed health check: `python3 automation/scripts/health-check.py --check-only --format=text`
   - Check service connectivity: `curl http://localhost:8003/health`
   - Verify environment variables: `env | grep SOPHIA`

3. **Kubernetes deployment issues**
   - Check pod status: `kubectl describe pod pod-name -n sophia-intel-ai`
   - View events: `kubectl get events -n sophia-intel-ai --sort-by='.firstTimestamp'`
   - Check resources: `kubectl top pods -n sophia-intel-ai`

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Enable debug logging
export SOPHIA_VERBOSE=true
export LOG_LEVEL=DEBUG

# Run with verbose output
./automation/scripts/sophia-start.sh --verbose

# Check detailed health status
python3 automation/scripts/health-check.py --check-only --format=json | jq .
```

## 📈 Performance Optimization

### Resource Tuning

The system includes environment-specific resource limits:

**Development:**
- CPU: 4 cores, Memory: 8GB, Storage: 50GB

**Production:**
- CPU: 16 cores, Memory: 32GB, Storage: 500GB

### Auto-scaling

Kubernetes deployments include Horizontal Pod Autoscaling:
- **Target CPU**: 70%
- **Target Memory**: 80%
- **Min Replicas**: 2
- **Max Replicas**: 10

## 🔍 Observability

### Metrics Collection

The system exposes comprehensive metrics:
- **Application metrics**: Request rates, response times, error rates
- **Business metrics**: Success rates, user interactions
- **Infrastructure metrics**: CPU, memory, disk, network
- **Custom metrics**: Component health, cache hit rates

### Distributed Tracing

Optional Jaeger tracing integration:
```bash
# Enable tracing
export JAEGER_ENABLED=true
export JAEGER_ENDPOINT=http://jaeger:14268/api/traces
```

### Log Aggregation

Structured logging with multiple outputs:
- **Console**: For development and debugging
- **Files**: For local storage and rotation
- **External**: For centralized log management

## 🤝 Contributing

### Development Setup

1. Clone the repository
2. Install dependencies: `./automation/scripts/sophia-start.sh install`
3. Setup configuration: `./automation/scripts/sophia-start.sh config`
4. Start development environment: `./automation/scripts/sophia-start.sh --mode=development`

### Testing Changes

```bash
# Validate configuration changes
python3 automation/scripts/config-manager.py --action=validate

# Test health monitoring
python3 automation/scripts/health-check.py --check-only

# Run integration tests
docker-compose -f docker-compose.enhanced.yml up -d
pytest tests/integration/
```

## 📄 License

This automation system is part of the Sophia Intel AI platform and follows the same licensing terms.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review logs for error messages
3. Run health checks for system status
4. Validate configuration settings

---

**🧠 Sophia Intel AI Automation System** - Production-ready, cross-platform, intelligent startup automation.