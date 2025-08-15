# SOPHIA Intel Architecture Overview

## Executive Summary

SOPHIA Intel is a modern, CPU-optimized, API-first platform featuring autonomous agent capabilities. The architecture prioritizes cost efficiency, scalability, and AI-powered development workflows while maintaining production-grade reliability and security.

## Architecture Principles

### Core Principles
1. **CPU-First Optimization**: Designed for cost-effective CPU instances rather than expensive GPU infrastructure
2. **API-First Design**: All functionality exposed through well-defined REST APIs
3. **Agent-Centric**: Autonomous agents handle complex development tasks
4. **Cloud-Native**: Kubernetes-based with horizontal scaling capabilities
5. **Security by Design**: SSL, CORS, and secure secret management throughout

### Design Philosophy
- **Cost Optimization**: 80% cost reduction through intelligent architecture choices
- **Simplicity**: Reduced complexity while maintaining functionality
- **Scalability**: Horizontal scaling with Kubernetes orchestration
- **Reliability**: Comprehensive health monitoring and automated recovery
- **Maintainability**: Clear separation of concerns and modular design

## System Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    Internet / Users                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 DNSimple DNS                                │
│  • www.sophia-intel.ai                                      │
│  • api.sophia-intel.ai                                      │
│  • dashboard.sophia-intel.ai                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Lambda Labs CPU Cluster                        │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                K3s Kubernetes                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │              Kong Ingress                           │ │ │
│  │  │  • SSL Termination (Let's Encrypt)                 │ │ │
│  │  │  • Load Balancing                                  │ │ │
│  │  │  • Rate Limiting                                   │ │ │
│  │  └─────────────────┬───────────────────────────────────┘ │ │
│  │                    │                                     │ │
│  │  ┌─────────────────▼───────────────────────────────────┐ │ │
│  │  │            Application Layer                        │ │ │
│  │  │  ┌─────────────┬─────────────┬─────────────────────┐ │ │ │
│  │  │  │ AI Router   │ Agent Swarm │ Dashboard           │ │ │ │
│  │  │  │ (Port 5000) │ (Port 5001) │ (Port 3000)         │ │ │ │
│  │  │  │             │             │                     │ │ │ │
│  │  │  │ • Claude S4 │ • Planner   │ • Web Interface     │ │ │ │
│  │  │  │ • OpenRouter│ • Coder     │ • Mission Control   │ │ │ │
│  │  │  │ • Routing   │ • Orchestr. │ • Monitoring        │ │ │ │
│  │  │  └─────────────┴─────────────┴─────────────────────┘ │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Infrastructure Components

#### Lambda Labs CPU Cluster
- **Instance Type**: cpu.c2-2 (2 vCPU, 4GB RAM)
- **Cluster Size**: 3 nodes (1 master, 2 workers)
- **Operating System**: Ubuntu 22.04 LTS
- **Network**: Private networking with public IPs
- **Storage**: SSD-backed ephemeral storage

#### Kubernetes (K3s)
- **Distribution**: K3s (lightweight Kubernetes)
- **Version**: Latest stable
- **Components**: 
  - etcd (embedded)
  - CoreDNS
  - Traefik (replaced with Kong)
  - Local-path provisioner
  - Metrics server

#### Ingress & Load Balancing
- **Ingress Controller**: Kong
- **SSL Termination**: Let's Encrypt certificates
- **Features**:
  - Automatic certificate renewal
  - Rate limiting
  - Request/response transformation
  - Health checks

## Application Architecture

### AI Router Service

#### Purpose
Central routing service for AI model selection and request handling.

#### Key Features
- **Primary Model**: Claude Sonnet 4 (95%+ usage)
- **Fallback Models**: OpenRouter integration for redundancy
- **Intelligent Routing**: Cost and performance optimization
- **Request Handling**: Async processing with connection pooling

#### API Endpoints
```
GET  /api/health              - Health check
POST /api/ai/route            - Route AI requests
GET  /api/ai/models           - List available models
POST /api/ai/chat             - Direct chat interface
```

#### Architecture
```python
class AIRouter:
    def __init__(self):
        self.model_registry = {
            "claude-sonnet-4": {
                "provider": "openrouter",
                "cost_per_token": 0.000003,
                "priority": 1,
                "capabilities": ["chat", "code", "analysis"]
            }
        }
    
    async def route_request(self, task_type, prompt, preferences):
        # Intelligent model selection
        selected_model = self._select_optimal_model(task_type, preferences)
        
        # Execute request
        response = await self._execute_request(selected_model, prompt)
        
        return response
```

### Agent Swarm Service

#### Purpose
Autonomous agent framework for complex development tasks.

#### Agent Types
1. **Base Agent**: Common functionality and AI integration
2. **Planner Agent**: Task decomposition and strategic planning
3. **Coder Agent**: Code generation and implementation

#### Swarm Orchestrator
```python
class SwarmOrchestrator:
    def __init__(self):
        self.agent_pool = []
        self.mission_queue = []
        self.active_missions = {}
    
    async def start_mission(self, description, requirements, priority):
        # Create mission
        mission = Mission(description, requirements, priority)
        
        # Decompose into tasks
        tasks = await self._decompose_mission(mission)
        
        # Assign to agents
        await self._assign_tasks(tasks)
        
        return mission.id
```

#### API Endpoints
```
GET  /api/swarm/health        - Health check
GET  /api/swarm/status        - Swarm status and metrics
POST /api/swarm/missions      - Start new mission
GET  /api/swarm/missions/:id  - Get mission status
DELETE /api/swarm/missions/:id - Cancel mission
GET  /api/swarm/agents        - List agents and capabilities
```

### Dashboard Service

#### Purpose
Web-based interface for monitoring and controlling the SOPHIA Intel platform.

#### Features
- **Mission Control**: Start and monitor development missions
- **Agent Monitoring**: Real-time agent status and performance
- **System Health**: Infrastructure and service monitoring
- **Cost Analytics**: Usage and cost tracking

#### Technology Stack
- **Frontend**: React with TypeScript
- **State Management**: Redux Toolkit
- **UI Components**: Material-UI
- **Charts**: Chart.js for metrics visualization
- **WebSocket**: Real-time updates

## Data Architecture

### Data Flow
```
User Request → Kong Ingress → Service Router → AI Router/Agent Swarm
                                                      ↓
                                              Claude Sonnet 4
                                                      ↓
                                              Response Processing
                                                      ↓
                                              Dashboard Updates
```

### State Management
- **Mission State**: In-memory with periodic persistence
- **Agent State**: Local to each agent instance
- **Configuration**: Kubernetes ConfigMaps and Secrets
- **Metrics**: Prometheus-compatible metrics (future enhancement)

### Caching Strategy
- **AI Responses**: LRU cache for common requests
- **Model Metadata**: In-memory registry with TTL
- **Static Assets**: CDN caching for dashboard resources

## Security Architecture

### Authentication & Authorization
- **API Keys**: Secure API key management via Kubernetes Secrets
- **CORS**: Configured for cross-origin requests
- **Rate Limiting**: Kong-based rate limiting
- **SSL/TLS**: End-to-end encryption with Let's Encrypt

### Secret Management
```
GitHub Organization Secrets
           ↓
    Pulumi ESC (centralized)
           ↓
    Kubernetes Secrets
           ↓
    Application Runtime
```

### Network Security
- **Private Networking**: Internal service communication
- **Firewall Rules**: Restricted ingress to necessary ports
- **SSL Termination**: Kong handles SSL/TLS termination
- **Certificate Management**: Automated Let's Encrypt renewal

## Deployment Architecture

### CI/CD Pipeline
```
Code Changes → Git Push → GitHub Actions → Build → Deploy → Validate
```

### Deployment Strategy
- **Blue-Green**: Zero-downtime deployments
- **Rolling Updates**: Kubernetes rolling update strategy
- **Health Checks**: Readiness and liveness probes
- **Rollback**: Automated rollback on health check failures

### Environment Management
- **Production**: Lambda Labs CPU cluster
- **Configuration**: Environment-specific ConfigMaps
- **Secrets**: Pulumi ESC integration
- **Monitoring**: Health checks and metrics collection

## Scaling Architecture

### Horizontal Scaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sophia-intel-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sophia-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Vertical Scaling
- **Resource Limits**: CPU and memory limits per container
- **Request/Limit Ratios**: Optimized for cost efficiency
- **Node Scaling**: Manual Lambda Labs instance addition

### Load Distribution
- **Kong Load Balancing**: Round-robin with health checks
- **Service Mesh**: Future consideration for advanced routing
- **Database Scaling**: Horizontal read replicas (future)

## Performance Architecture

### Response Time Optimization
- **Async Processing**: Non-blocking I/O throughout
- **Connection Pooling**: Efficient HTTP client management
- **Caching**: Multi-layer caching strategy
- **CDN**: Static asset delivery optimization

### Resource Optimization
- **CPU Efficiency**: Optimized for CPU-only workloads
- **Memory Management**: Efficient memory usage patterns
- **I/O Optimization**: Async file and network operations
- **Container Optimization**: Minimal base images

### Monitoring & Observability
- **Health Checks**: Comprehensive health monitoring
- **Metrics Collection**: Performance and usage metrics
- **Logging**: Structured logging with correlation IDs
- **Alerting**: Automated alert system (future enhancement)

## Cost Architecture

### Cost Optimization Strategy
```
Previous Architecture (GPU):
- 3x GPU instances: $250/month each = $750/month
- Vercel Pro: $20/month
- Total: $770/month

Current Architecture (CPU):
- 3x CPU instances: $50/month each = $150/month
- DNS: $5/month
- Total: $155/month

Savings: 80% reduction ($615/month saved)
```

### Cost Monitoring
- **Instance Costs**: Lambda Labs usage tracking
- **API Costs**: OpenRouter usage monitoring
- **Resource Utilization**: Kubernetes resource metrics
- **Cost Alerts**: Automated cost threshold alerts

## Future Architecture Considerations

### Planned Enhancements
1. **Additional Agents**: Reviewer, Integrator, Tester, Documenter
2. **Database Integration**: PostgreSQL for persistent data
3. **Message Queue**: Redis for async task processing
4. **Monitoring Stack**: Prometheus + Grafana
5. **Service Mesh**: Istio for advanced traffic management

### Scalability Roadmap
1. **Multi-Region**: Deploy across multiple Lambda Labs regions
2. **CDN Integration**: CloudFlare for global content delivery
3. **Database Scaling**: Read replicas and sharding
4. **Microservices**: Further service decomposition

### Technology Evolution
1. **Container Optimization**: Distroless images
2. **Serverless Integration**: Lambda functions for specific tasks
3. **AI Model Updates**: Integration with newer models
4. **Edge Computing**: Edge deployment for reduced latency

## Architecture Decisions

### Key Decisions & Rationale

#### 1. CPU-Only Architecture
- **Decision**: Use CPU instances instead of GPU
- **Rationale**: 80% cost savings with Claude Sonnet 4 handling AI workloads
- **Trade-offs**: Dependency on external AI services vs. cost efficiency

#### 2. K3s vs. Full Kubernetes
- **Decision**: Use K3s lightweight distribution
- **Rationale**: Reduced resource overhead, simpler management
- **Trade-offs**: Some advanced features unavailable vs. resource efficiency

#### 3. Kong vs. Nginx Ingress
- **Decision**: Use Kong for ingress
- **Rationale**: Advanced API gateway features, better SSL management
- **Trade-offs**: Slightly higher resource usage vs. feature richness

#### 4. Claude Sonnet 4 Primary Model
- **Decision**: Use Claude Sonnet 4 as primary AI model
- **Rationale**: Superior performance, cost-effective via OpenRouter
- **Trade-offs**: External dependency vs. performance and cost

## Conclusion

The SOPHIA Intel architecture represents a modern, cost-optimized approach to AI-powered development platforms. By prioritizing CPU efficiency, API-first design, and autonomous agent capabilities, the architecture achieves significant cost savings while maintaining production-grade reliability and scalability.

The architecture is designed for evolution, with clear paths for enhancement and scaling as requirements grow. The modular design ensures that individual components can be upgraded or replaced without affecting the overall system stability.

---

*This architecture overview should be reviewed quarterly and updated to reflect any significant changes or enhancements to the system.*

