# 🚀 Code Refactoring Swarm

**Revolutionary AI-Powered Code Transformation System**

A production-ready, multi-agent swarm that intelligently refactors code at enterprise scale with safety guarantees, debate-driven validation, and comprehensive monitoring.

## 🎯 Overview

The Code Refactoring Swarm leverages the Artemis agent factory framework to orchestrate 10 specialized AI agents through a 13-phase pipeline, delivering safe, intelligent code transformations with enterprise-grade reliability.

### Key Features

- **🤖 Multi-Agent Intelligence**: 10 specialized agents working in concert
- **🛡️ Enterprise Safety**: 7 safety gates with rollback capabilities
- **🎯 13-Phase Pipeline**: Comprehensive discovery → validation → execution
- **⚖️ Debate-Driven Quality**: Multi-agent consensus before any changes
- **📊 Production Monitoring**: Full observability and metrics
- **🔄 Session Management**: Complete audit trail and rollback support

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 CODE REFACTORING SWARM                     │
├─────────────────────────────────────────────────────────────┤
│  Discovery → Analysis → Planning → Validation → Execution  │
│     ↓           ↓         ↓          ↓           ↓        │
│  Safety Gates + Debate System + Rollback Mechanism        │
└─────────────────────────────────────────────────────────────┘
```

### Agent Roles

| Team          | Agents                                                                   | Responsibility                     |
| ------------- | ------------------------------------------------------------------------ | ---------------------------------- |
| **Analysis**  | CodeScanner, ArchitecturalAnalyzer, PerformanceProfiler, SecurityAuditor | Identify refactoring opportunities |
| **Planning**  | RefactoringPlanner, RiskAssessor, ImpactAnalyzer, QualityValidator       | Validate and plan changes          |
| **Execution** | CodeTransformer, DocumentationUpdater                                    | Execute approved transformations   |

### Execution Pipeline

1. **Discovery Phase** (1-3): Scan → Analyze → Profile
2. **Planning Phase** (4-6): Risk → Impact → Plan
3. **Validation Phase** (7-9): Debate → Consensus → Safety
4. **Execution Phase** (10-13): Transform → Test → Document → Deploy

## 🚀 Quick Start

### 1. Basic Usage

```python
from app.swarms.refactoring.deployment_utils import deploy_development_swarm
from app.swarms.refactoring.code_refactoring_swarm import RefactoringType, RefactoringRisk

# Deploy swarm
manager = await deploy_development_swarm()

# Execute refactoring session
result = await manager.swarm.execute_refactoring_session(
    codebase_path="/path/to/your/code",
    refactoring_types=[RefactoringType.QUALITY, RefactoringType.PERFORMANCE],
    risk_tolerance=RefactoringRisk.MEDIUM,
    dry_run=True  # Safe mode - analyze only
)

print(f"Found {len(result.executed_opportunities)} opportunities")
print(f"Quality improvement: {result.quality_metrics.get('quality_improvement', 0)*100:.1f}%")

# Cleanup
await manager.shutdown()
```

### 2. Production Deployment

```python
from app.swarms.refactoring.deployment_utils import deploy_production_swarm

# Deploys with full validation and monitoring
manager = await deploy_production_swarm()

# Execute with real changes
result = await manager.swarm.execute_refactoring_session(
    codebase_path="/production/codebase",
    refactoring_types=[RefactoringType.SECURITY],
    risk_tolerance=RefactoringRisk.LOW,
    dry_run=False  # Live execution
)

# Rollback if needed
if not result.success and result.rollback_available:
    await manager.swarm.rollback_changes(result.plan_id)
```

## 📋 Configuration

### Environment Configurations

| Environment     | Safety Level | Agents | Max Files | Risk Tolerance           |
| --------------- | ------------ | ------ | --------- | ------------------------ |
| **Development** | Basic        | 5      | 20        | Critical only            |
| **Staging**     | Standard     | 8      | 35        | High + Critical          |
| **Production**  | Maximum      | 10     | 50        | High + Critical          |
| **Enterprise**  | Maximum      | 20     | 100       | Medium + High + Critical |

### Custom Configuration

```python
from app.swarms.refactoring.refactoring_swarm_config import RefactoringSwarmConfiguration

config = RefactoringSwarmConfiguration(
    environment=DeploymentEnvironment.PRODUCTION,
    enabled_refactoring_types=[RefactoringType.SECURITY, RefactoringType.PERFORMANCE],
    default_risk_tolerance=RefactoringRisk.LOW,

    # Safety settings
    safety=SafetyConfiguration(
        max_files_per_session=25,
        require_backup=True,
        require_tests=True,
        forbidden_paths=["/config/", "/secrets/"]
    ),

    # Resource limits
    resources=ResourceConfiguration(
        max_concurrent_agents=10,
        max_execution_time_minutes=60,
        circuit_breaker_threshold=3
    ),

    # Monitoring
    monitoring=MonitoringConfiguration(
        level=MonitoringLevel.COMPREHENSIVE,
        alerts_enabled=True,
        export_prometheus=True
    )
)
```

## 🛡️ Safety Features

### Safety Gates

1. **Opportunity Gate**: Validates refactoring candidates
2. **Architecture Gate**: Ensures structural soundness
3. **Risk Gate**: Assesses change safety levels
4. **Impact Gate**: Verifies acceptable consequences
5. **Consensus Gate**: Requires agent agreement
6. **Quality Gate**: Validates refactoring standards
7. **Deployment Gate**: Final production readiness

### Risk Management

- **Low Risk**: Simple formatting, documentation
- **Medium Risk**: Function signatures, minor logic
- **High Risk**: Architecture changes, data structures
- **Critical Risk**: Core systems, security-sensitive code

### Rollback Capabilities

```python
# Check rollback availability
if result.rollback_available:
    # Restore previous state
    success = await swarm.rollback_changes(result.plan_id)

# Create backup before changes
backup_path = await manager.create_backup()

# Restore from backup if needed
await manager.restore_from_backup(backup_path)
```

## 📊 Monitoring & Metrics

### Health Monitoring

```python
# Comprehensive health check
health_status = await manager.health_check()

print(f"Health: {'✅' if health_status['healthy'] else '❌'}")
print(f"Agents: {health_status['checks']['agents_initialized']}")
print(f"Memory: {health_status['checks']['memory_available_mb']}MB")

# Warnings and errors
for warning in health_status.get('warnings', []):
    print(f"⚠️ {warning}")
```

### Session Metrics

```python
# Get session history
history = swarm.get_session_history()

# Quality metrics from results
metrics = result.quality_metrics
print(f"Success rate: {metrics['success_rate']*100:.1f}%")
print(f"Quality improvement: {metrics['quality_improvement']*100:.1f}%")
print(f"Technical debt reduction: {metrics['technical_debt_reduction']*100:.1f}%")
```

### Prometheus Integration

The swarm exports metrics to Prometheus when enabled:

- `refactoring_sessions_total`: Total refactoring sessions
- `refactoring_opportunities_found`: Opportunities identified
- `refactoring_success_rate`: Success rate percentage
- `refactoring_execution_time_seconds`: Session duration
- `refactoring_quality_improvement`: Quality metrics

## 🔧 Integration Examples

### CLI Usage

```bash
# Run specific example
python app/swarms/refactoring/example_integration.py 1

# Run all integration examples
python app/swarms/refactoring/example_integration.py all
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Code Refactoring Analysis
  run: |
    python -c "
    import asyncio
    from app.swarms.refactoring.deployment_utils import deploy_development_swarm

    async def analyze():
        manager = await deploy_development_swarm()
        result = await manager.swarm.execute_refactoring_session(
            codebase_path='.',
            dry_run=True
        )
        print(f'Found {len(result.executed_opportunities)} opportunities')
        await manager.shutdown()

    asyncio.run(analyze())
    "
```

### API Integration

```python
from app.swarms.refactoring.deployment_utils import SwarmDeploymentManager
from fastapi import FastAPI

app = FastAPI()
swarm_manager = None

@app.post("/refactor")
async def refactor_code(request: RefactorRequest):
    global swarm_manager

    if not swarm_manager:
        swarm_manager = await deploy_production_swarm()

    result = await swarm_manager.swarm.execute_refactoring_session(
        codebase_path=request.codebase_path,
        refactoring_types=request.refactoring_types,
        risk_tolerance=request.risk_tolerance,
        dry_run=request.dry_run
    )

    return {
        "session_id": result.plan_id,
        "success": result.success,
        "opportunities": len(result.executed_opportunities),
        "quality_metrics": result.quality_metrics
    }
```

## 📚 Advanced Usage

### Custom Agent Models

```python
config.agent_model_overrides = {
    "security_auditor": "claude-3-5-sonnet-20241022",
    "performance_profiler": "gpt-4o",
    "architectural_analyzer": "deepseek-chat"
}
```

### Multi-Environment Deployment

```python
# Development pipeline
dev_manager = await deploy_development_swarm()
dev_result = await dev_manager.swarm.execute_refactoring_session(...)

# If successful, promote to staging
if dev_result.success:
    staging_config = RefactoringSwarmConfiguration.for_environment(
        DeploymentEnvironment.STAGING
    )
    staging_manager = SwarmDeploymentManager(staging_config)
    await staging_manager.deploy()
```

### Batch Processing

```python
# Process multiple codebases
codebases = ["/app1", "/app2", "/app3"]
results = {}

for path in codebases:
    result = await swarm.execute_refactoring_session(
        codebase_path=path,
        refactoring_types=[RefactoringType.SECURITY],
        risk_tolerance=RefactoringRisk.LOW
    )
    results[path] = result

# Analyze batch results
total_opportunities = sum(len(r.executed_opportunities) for r in results.values())
success_rate = sum(1 for r in results.values() if r.success) / len(results)
```

## 🔍 Troubleshooting

### Common Issues

**Deployment Fails**

```python
# Check configuration validation
config = RefactoringSwarmConfiguration.for_environment(env)
issues = config.validate()
if issues:
    print("Configuration issues:", issues)
```

**Low Memory Warning**

```python
# Reduce concurrent agents
config.resources.max_concurrent_agents = 5
config.resources.max_memory_per_agent_mb = 256
```

**Agent Initialization Errors**

```python
# Check agent connectivity
health = await manager.health_check()
if not health['healthy']:
    print("Errors:", health['errors'])
    print("Warnings:", health['warnings'])
```

### Performance Tuning

- **Memory**: Adjust `max_memory_per_agent_mb` based on available RAM
- **Concurrency**: Set `max_concurrent_agents` to match CPU cores
- **Timeout**: Increase `max_execution_time_minutes` for large codebases
- **Caching**: Enable `cache_enabled` for repeated operations

## 📈 Best Practices

### Safety First

- Always test with `dry_run=True` first
- Use appropriate risk tolerance for environment
- Monitor health status regularly
- Keep backups of critical changes

### Performance Optimization

- Configure resource limits appropriately
- Use specialized models for specific tasks
- Enable caching for repeated operations
- Monitor execution metrics

### Production Deployment

- Run production readiness checklist
- Enable comprehensive monitoring
- Set up alerting for failures
- Implement proper rollback procedures

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** Pull Request

### Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/test_refactoring_swarm.py

# Run integration examples
python app/swarms/refactoring/example_integration.py all
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: [Internal Wiki](wiki/refactoring-swarm)
- **Issues**: [GitHub Issues](https://github.com/your-org/sophia-intel-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/sophia-intel-ai/discussions)
- **Email**: <refactoring-swarm-support@your-org.com>

---

**The Code Refactoring Swarm represents the future of intelligent code transformation - safe, scalable, and revolutionary.** 🚀
