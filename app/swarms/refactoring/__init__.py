"""
Code Refactoring Swarm Package

Revolutionary AI-powered code transformation system with multi-agent orchestration,
safety guarantees, and enterprise-grade deployment capabilities.
"""

from app.swarms.refactoring.code_refactoring_swarm import (
    CodeRefactoringSwarm,
    RefactoringType,
    RefactoringRisk,
    RefactoringOpportunity,
    RefactoringPlan,
    RefactoringResult
)

from app.swarms.refactoring.refactoring_swarm_config import (
    RefactoringSwarmConfiguration,
    DeploymentEnvironment,
    MonitoringLevel,
    SafetyConfiguration,
    ResourceConfiguration,
    MonitoringConfiguration,
    DEVELOPMENT_CONFIG,
    STAGING_CONFIG,
    PRODUCTION_CONFIG,
    ENTERPRISE_CONFIG
)

from app.swarms.refactoring.deployment_utils import (
    SwarmDeploymentManager,
    SwarmOperations,
    deploy_development_swarm,
    deploy_production_swarm
)

# Package metadata
__version__ = "1.0.0"
__author__ = "Sophia Intel AI Team"
__description__ = "Revolutionary AI-powered code refactoring swarm"

# Public API
__all__ = [
    # Core swarm classes
    "CodeRefactoringSwarm",
    "RefactoringType", 
    "RefactoringRisk",
    "RefactoringOpportunity",
    "RefactoringPlan",
    "RefactoringResult",
    
    # Configuration classes
    "RefactoringSwarmConfiguration",
    "DeploymentEnvironment",
    "MonitoringLevel",
    "SafetyConfiguration",
    "ResourceConfiguration", 
    "MonitoringConfiguration",
    
    # Predefined configurations
    "DEVELOPMENT_CONFIG",
    "STAGING_CONFIG",
    "PRODUCTION_CONFIG",
    "ENTERPRISE_CONFIG",
    
    # Deployment utilities
    "SwarmDeploymentManager",
    "SwarmOperations",
    "deploy_development_swarm",
    "deploy_production_swarm",
    
    # Package metadata
    "__version__",
    "__author__",
    "__description__"
]

# Quick start examples in docstring
__doc__ += """

## Quick Start

### Basic Usage
```python
from app.swarms.refactoring import deploy_development_swarm, RefactoringType, RefactoringRisk

# Deploy and use swarm
manager = await deploy_development_swarm()
result = await manager.swarm.execute_refactoring_session(
    codebase_path="/your/code",
    refactoring_types=[RefactoringType.QUALITY],
    risk_tolerance=RefactoringRisk.LOW,
    dry_run=True
)
await manager.shutdown()
```

### Production Deployment
```python
from app.swarms.refactoring import deploy_production_swarm

# Full validation and monitoring
manager = await deploy_production_swarm()
result = await manager.swarm.execute_refactoring_session(
    codebase_path="/production/code",
    dry_run=False
)
```

### Custom Configuration
```python
from app.swarms.refactoring import (
    RefactoringSwarmConfiguration, 
    DeploymentEnvironment,
    SwarmDeploymentManager
)

config = RefactoringSwarmConfiguration.for_environment(
    DeploymentEnvironment.ENTERPRISE
)
manager = SwarmDeploymentManager(config)
await manager.deploy()
```

See README.md for complete documentation and examples.
"""