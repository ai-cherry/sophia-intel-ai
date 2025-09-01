# 🤖 AI Agent Rules Framework

## Overview
This framework ensures all AI coding agents (Claude Coder, Roo Coder, and custom swarms) follow strict quality standards, avoid mock implementations, and maintain zero technical debt.

## Quick Start

### 1. Validate Current Codebase
```bash
python3 .ai/scripts/validate_rules.py
```

### 2. Clean Up Technical Debt
```bash
.ai/scripts/cleanup_debris.sh
```

### 3. Check Agent Rules
```bash
cat .ai/MASTER_RULES.yaml  # Universal rules
cat .ai/agents/claude.mdc  # Claude-specific
cat .ai/agents/roo.mdc     # Roo-specific
```

## Directory Structure

```
.ai/
├── MASTER_RULES.yaml           # Universal enforcement rules
├── README.md                   # This file
├── agents/                     # Agent-specific configurations
│   ├── claude.mdc             # Claude Coder rules
│   ├── roo.mdc                # Roo Coder rules
│   └── swarm/                 # Swarm agent rules
│       ├── strategic.mdc
│       ├── development.mdc
│       └── security.mdc
├── workflows/                  # Orchestration workflows
│   └── feature_development.yaml
├── scripts/                    # Validation and cleanup
│   ├── validate_rules.py      # Validate compliance
│   └── cleanup_debris.sh      # Remove tech debt
└── contexts/                   # Context-specific rules
    └── (future expansion)
```

## Key Principles

### 1. Truth Verification
- **REQUIRED**: Terminal output, test results, actual file paths
- **FORBIDDEN**: "should work", "in theory", "placeholder", "mock implementation"

### 2. Anti-Mock Policy
- **PROHIBITED**: Mock*, Fake*, Stub*, Example*, Demo*, Sample*
- **REQUIRED**: Real API endpoints, actual database writes, persistent files

### 3. Zero Debris
- **AUTO-CLEANUP**: Old files, backups, empty files, temporary files
- **MAX AGE**: 24 hours for temporary files

### 4. Tech Stack Discipline
- **USE EXISTING**: 90% of problems solved with current stack
- **NEW ADDITIONS**: Require 10x improvement + ADR documentation

## Agent Roles & Priorities

| Agent | Role | Priority | Primary Tasks |
|-------|------|----------|---------------|
| Claude | Architect | 100 | System design, complex logic, documentation |
| Roo | Builder | 90 | Implementation, optimization, refactoring |
| Strategic Swarm | Planner | 95 | Task breakdown, dependency analysis |
| Development Swarm | Implementer | 85 | Coding, testing, debugging |
| Security Swarm | Validator | 80 | Security audit, compliance |
| Research Swarm | Explorer | 70 | Research, documentation |

## Quality Gates

### Code Quality
- Python: `ruff check`, `mypy --strict`, `black`, `pytest --cov-min=80`
- TypeScript: `eslint`, `tsc --noEmit`, `jest --coverage`

### Performance
- API latency: < 200ms (p99)
- Memory usage: < 512MB
- Startup time: < 30s

### Reliability
- Accuracy: > 90%
- Uptime: > 99.9%
- Error rate: < 0.1%

## Integration Points

### VSCode/Cursor
Configuration in `.vscode/settings.json`:
- Auto-loads agent rules
- Validates on save
- Blocks on violations

### Python Integration
```python
from app.swarms.rule_loader import RuleLoader, RuleEnforcer

# Load rules
loader = RuleLoader()
enforcer = RuleEnforcer(loader)

# Validate agent output
is_valid, violations = loader.validate_output(output, "claude")

# Match agent to task
best_agent = loader.match_agent_to_task("implement feature")
```

### Workflow Orchestration
```yaml
# Use predefined workflows
workflow: feature_development
stages:
  - planning (Claude)
  - implementation (Roo)
  - validation (Security Swarm)
  - documentation (Research Swarm)
```

## Validation & Enforcement

### Pre-Commit Validation
All changes are validated before commit:
```bash
# Automatic validation on git commit
git commit -m "feat: new feature"
# Runs: python3 .ai/scripts/validate_rules.py
```

### Continuous Monitoring
```bash
# Check for violations
python3 .ai/scripts/validate_rules.py

# Clean up debris
.ai/scripts/cleanup_debris.sh

# Test agent integration
python3 -m pytest tests/test_rule_loader.py
```

## Common Commands

```bash
# Validate everything
make validate

# Clean all debris
make clean-debris

# Test agent rules
make test-agents

# Full cleanup and validation
make ai-clean
```

## Troubleshooting

### Mock Implementations Detected
- Check if in test files (acceptable)
- If in production: Remove immediately
- Use real implementations only

### Forbidden Phrases Found
- Review context
- Replace with concrete statements
- Include evidence (output, metrics)

### Tech Stack Violations
- Check if existing solution works
- Document 10x improvement requirement
- Create ADR if proceeding

## Updates & Maintenance

Rules are versioned and dated. To update:
1. Edit relevant YAML/MDC files
2. Update version and modified date
3. Run validation
4. Commit with clear message

## Contact & Support

For questions or improvements to the AI rules framework:
- Create issue in repository
- Tag with `ai-rules`
- Include validation output