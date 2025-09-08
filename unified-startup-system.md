# Unified Startup System Architecture

## Problem Statement
Currently managing 114+ shell scripts creates:
- Maintenance nightmare with duplicated logic
- Unclear startup order and dependencies
- Fragmented configuration management
- Difficult troubleshooting and monitoring

## Solution: Unified Startup Orchestrator

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────┐
│                 Unified Startup Orchestrator               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Config    │  │ Dependency  │  │ Health      │        │
│  │ Management  │  │  Manager    │  │ Monitor     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Service    │  │ Environment │  │   Logger    │        │
│  │ Registry    │  │  Manager    │  │ & Metrics   │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Consolidated Script Structure

### Single Entry Point: `sophia-startup`
```bash
#!/bin/bash
# Master startup script - replaces all 114+ scripts

./unified-startup-orchestrator \
    --profile production \
    --domain sophia,artemis,shared \
    --verify-health \
    --wait-for-dependencies \
    --config config/unified-startup.yaml
```

### Core Components

#### 1. Configuration Management (`config/unified-startup.yaml`)
```yaml
profiles:
  development:
    infrastructure:
      - postgres_dev
      - redis_dev
      - elasticsearch_dev
    
    services:
      sophia: ["web_search", "business_analytics", "api_server"]
      artemis: ["filesystem", "code_analysis", "ai_agent"]
      shared: ["database_mcp", "indexing_mcp", "embedding_mcp"]
    
    environment:
      log_level: DEBUG
      health_check_timeout: 30
      startup_timeout: 300

  production:
    infrastructure:
      - postgres_cluster
      - redis_cluster
      - elasticsearch_cluster
    
    services:
      sophia: ["all"]
      artemis: ["all"]
      shared: ["all"]
    
    environment:
      log_level: INFO
      health_check_timeout: 60
      startup_timeout: 600
      monitoring: enabled

service_definitions:
  # Infrastructure Services
  postgres_dev:
    command: "docker run -d --name postgres_sophia -p 5432:5432 postgres:15"
    health_check: "pg_isready -h localhost -p 5432"
    wait_for: []
    timeout: 60
    
  redis_dev:
    command: "docker run -d --name redis_sophia -p 6379:6379 redis:7-alpine"
    health_check: "redis-cli ping"
    wait_for: []
    timeout: 30
    
  # Sophia Services
  sophia_api_server:
    command: "cd app && uvicorn main:app --host 0.0.0.0 --port 8000"
    health_check: "curl -f http://localhost:8000/health"
    wait_for: ["postgres_dev", "redis_dev", "sophia_business_analytics"]
    timeout: 120
    environment_file: ".env.sophia"
    
  # Artemis Services  
  artemis_ai_agent:
    command: "python -m artemis.agent --config artemis.yaml"
    health_check: "curl -f http://localhost:8010/health"
    wait_for: ["artemis_filesystem", "artemis_code_analysis"]
    timeout: 180
    environment_file: ".env.artemis"
    
  # Shared MCP Services
  shared_database_mcp:
    command: "python -m mcp_servers.shared.database --port 8030"
    health_check: "curl -f http://localhost:8030/health"
    wait_for: ["postgres_dev", "redis_dev"]
    timeout: 90

dependency_graph:
  # Automatically resolves startup order
  phases:
    1: ["postgres_dev", "redis_dev", "elasticsearch_dev"]
    2: ["shared_database_mcp", "shared_indexing_mcp", "shared_embedding_mcp"]
    3: ["mcp_bridge"]
    4: ["sophia_services", "artemis_services"]  # Parallel
    5: ["ui_services", "monitoring_services"]
```

#### 2. Service Registry (`lib/service_registry.py`)
```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional

class ServiceState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"

@dataclass
class Service:
    name: str
    domain: str  # sophia, artemis, shared
    command: str
    health_check: str
    dependencies: List[str]
    port: Optional[int]
    environment_file: Optional[str]
    timeout: int = 60
    state: ServiceState = ServiceState.STOPPED
    pid: Optional[int] = None

class ServiceRegistry:
    def __init__(self):
        self.services: Dict[str, Service] = {}
        self.dependency_graph = {}
    
    def register_service(self, service: Service):
        """Register a service in the registry"""
        self.services[service.name] = service
    
    def resolve_dependencies(self) -> List[List[str]]:
        """Resolve service startup order based on dependencies"""
        # Topological sort implementation
        pass
    
    def start_service(self, name: str) -> bool:
        """Start a specific service"""
        pass
    
    def stop_service(self, name: str) -> bool:
        """Stop a specific service"""
        pass
    
    def get_health_status(self) -> Dict[str, ServiceState]:
        """Get health status of all services"""
        pass
```

#### 3. Environment Manager (`lib/environment_manager.py`)
```python
class EnvironmentManager:
    def __init__(self, profile: str):
        self.profile = profile
        self.env_vars = {}
    
    def load_environment(self, domain: str):
        """Load environment variables for specific domain"""
        env_file = f".env.{domain}"
        if self.profile != "development":
            env_file = f".env.{domain}.{self.profile}"
        
        # Load and validate environment variables
        self.validate_required_keys(domain)
    
    def validate_required_keys(self, domain: str):
        """Validate that required API keys are present"""
        if domain == "sophia":
            required = ["APOLLO_API_KEY", "SLACK_BOT_TOKEN", "SALESFORCE_CLIENT_ID"]
        elif domain == "artemis":
            required = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY"]
        elif domain == "shared":
            required = ["SHARED_DATABASE_URL", "MCP_BRIDGE_SECRET"]
        
        # Validation logic
        pass
```

## Implementation Plan

### Phase 1: Core Orchestrator (Week 1)
- [ ] Build service registry and dependency resolver
- [ ] Create configuration parser
- [ ] Implement basic service lifecycle management
- [ ] Add health checking capabilities

### Phase 2: Service Integration (Week 2)  
- [ ] Convert critical services to orchestrator format
- [ ] Add environment management
- [ ] Implement dependency waiting logic
- [ ] Add logging and metrics

### Phase 3: Full Migration (Week 3-4)
- [ ] Migrate all 114+ scripts to unified config
- [ ] Add advanced features (rollback, scaling)
- [ ] Comprehensive testing
- [ ] Documentation and training

## Benefits

1. **Maintainability**: Single codebase instead of 114+ scripts
2. **Reliability**: Proper dependency management and health checks  
3. **Observability**: Centralized logging and metrics
4. **Consistency**: Standardized service management across domains
5. **Scalability**: Easy to add new services and environments
6. **Recovery**: Built-in failure detection and recovery

## Migration Strategy

### Immediate Actions
1. **Audit Current Scripts**: Categorize by function and identify duplicates
2. **Extract Common Patterns**: Identify reusable startup patterns
3. **Create Service Definitions**: Convert scripts to declarative config
4. **Build Core Orchestrator**: Start with dependency resolution
5. **Gradual Migration**: Move services incrementally to avoid disruption

### Success Criteria
- Reduce 114+ scripts to 1 orchestrator + config files
- < 5 minute complete system startup
- Zero manual intervention for standard deployments
- 99.9% health check reliability
- Complete audit trail of all startup activities