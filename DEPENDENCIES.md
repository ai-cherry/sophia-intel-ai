# Dependency Management Guide

## Overview

This document outlines the dependency management strategy for the Sophia Intel AI project. We maintain strict version pinning and security policies to ensure reproducible builds and production stability.

## Core Dependencies

### Framework & API
- **FastAPI** (0.116.1): Modern async web framework for building APIs
- **Uvicorn** (0.30.0): Lightning-fast ASGI server with uvloop support
- **Pydantic** (2.8.2): Data validation using Python type annotations
- **Pydantic Settings** (2.3.0): Settings management using Pydantic

### AI/ML Integrations
- **OpenAI** (1.50.0): OpenAI GPT models integration
- **Anthropic** (0.25.0): Claude AI models integration
- **Agno** (1.8.1): Ultra-fast agent framework for swarm intelligence
- **Portkey AI** (1.3.2): Unified LLM routing and management
- **Together** (0.2.11): Together AI platform integration

### Storage & Databases
- **SQLAlchemy** (2.0.29): SQL toolkit and ORM
- **Redis** (5.0.1): In-memory data structure store for caching and queues
- **Weaviate Client** (4.16.4): Vector database for semantic search
- **Neo4j** (5.24.0): Graph database for knowledge graphs
- **AsyncPG** (0.29.0): PostgreSQL async driver

### Task Queues & Background Jobs
- **Celery** (5.3.4): Distributed task queue
- **Arq** (0.26.0): Async Redis-based task queue
- **APScheduler** (3.10.4): Advanced Python scheduler

### Monitoring & Observability
- **Prometheus Client** (0.19.0): Metrics collection
- **OpenTelemetry** (1.22.0): Distributed tracing
- **Structlog** (24.1.0): Structured logging
- **Loguru** (0.7.2): Advanced logging with rotation
- **Sentry SDK** (1.45.0): Error tracking and monitoring

### Performance & Optimization
- **HTTPX** (0.27.0): Async HTTP client with HTTP/2 support
- **Orjson** (3.10.12): Fastest JSON serialization
- **Uvloop** (0.19.0): Ultra-fast async event loop
- **Aiocache** (0.12.2): Async caching with Redis support

### Security
- **Cryptography** (44.0.1): Cryptographic recipes and primitives
- **PyJWT** (2.8.0): JSON Web Token implementation
- **Passlib** (1.7.4): Password hashing library
- **Authlib** (1.3.0): OAuth 2.0 implementation

### Search & Web Tools
- **DuckDuckGo Search** (6.3.7): Privacy-focused web search API

## Version Pinning Policy

### Production Dependencies
All production dependencies MUST be pinned to exact versions using `==`:
```toml
fastapi==0.116.1  # ✅ Correct
fastapi>=0.116.0  # ❌ Not allowed
```

### Development Dependencies
Development dependencies should be pinned to exact versions for consistency:
```toml
pytest==8.3.3     # ✅ Correct
black==25.1.0     # ✅ Correct
```

### Lock Files
We maintain three lock files:
1. `requirements-lock.txt` - Production dependencies with hashes
2. `requirements-dev-lock.txt` - Development dependencies
3. `requirements-test-lock.txt` - Testing dependencies

## Dependency Management Commands

### Check Dependencies
```bash
# Full dependency report
python scripts/pin_dependencies.py check

# Check for unpinned dependencies
python scripts/pin_dependencies.py pin

# Security vulnerability scan
python scripts/pin_dependencies.py security

# Check for virtualenvs in repo
python scripts/pin_dependencies.py clean
```

### Generate Lock Files
```bash
# Install pip-tools
pip install pip-tools

# Generate production lock file
pip-compile --generate-hashes -o requirements-lock.txt pyproject.toml

# Generate dev lock file
pip-compile --extra=dev --generate-hashes -o requirements-dev-lock.txt pyproject.toml
```

### Install Dependencies
```bash
# Production environment
pip install -r requirements-lock.txt

# Development environment
pip install -r requirements-dev-lock.txt

# From pyproject.toml (development)
pip install -e ".[dev,test]"
```

## Security Policies

### Vulnerability Scanning
- Weekly automated scans via GitHub Actions
- Multiple scanners: Safety, Bandit, pip-audit
- Critical vulnerabilities block PR merges
- Security reports uploaded as artifacts

### License Compliance
- Automated license checking in CI/CD
- Restricted licenses flagged:
  - GPL, AGPL, LGPL, SSPL
- MIT, Apache 2.0, BSD preferred

### Update Process
1. Weekly dependency audit (automated)
2. Security patches applied immediately
3. Minor updates tested in develop branch
4. Major updates require full regression testing

## Virtual Environment Policy

### Strict No-Venv Policy
Virtual environments are **NEVER** committed to the repository.

### Excluded Patterns
The following patterns are strictly excluded via `.gitignore`:
- `venv/`, `env/`, `.venv/`, `.env/`
- `virtualenv/`, `pyenv/`, `.pyenv/`
- `__pycache__/`, `*.pyc`, `*.pyo`
- All Python bytecode and cache files

### Pre-commit Checks
Pre-commit hooks automatically check for:
- Virtual environment directories
- Python cache files
- Unpinned dependencies

## CI/CD Gates

### Required Checks (Block Merge)
1. **Version Pinning**: All dependencies must be pinned
2. **Virtual Environment**: No venv directories in repo
3. **Reproducibility**: Dependencies install on Python 3.10-3.12
4. **Code Coverage**: Minimum 80% coverage
5. **Type Checking**: MyPy passes with strict mode

### Advisory Checks (Warnings)
1. **Security Scan**: Known vulnerabilities flagged
2. **License Check**: Restrictive licenses warned
3. **Outdated Packages**: Update recommendations

## Updating Dependencies

### Process
1. **Identify Update Need**
   - Security vulnerability
   - Bug fix required
   - New feature needed

2. **Test Compatibility**
   ```bash
   # Create test environment
   python -m venv test-env
   source test-env/bin/activate
   
   # Install new version
   pip install package==new.version
   
   # Run tests
   pytest
   ```

3. **Update pyproject.toml**
   ```toml
   # Update version
   package==new.version
   ```

4. **Regenerate Lock Files**
   ```bash
   pip-compile --generate-hashes -o requirements-lock.txt pyproject.toml
   ```

5. **Test Installation**
   ```bash
   pip install -r requirements-lock.txt
   pytest
   ```

6. **Create PR**
   - Include reason for update
   - Link to changelog
   - Test results

## Emergency Procedures

### Critical Security Patch
1. Create hotfix branch from main
2. Update affected package version
3. Regenerate lock files
4. Run security scan
5. Fast-track PR with single approval
6. Deploy immediately

### Dependency Conflict Resolution
1. Identify conflicting packages
2. Use pip-tools resolver:
   ```bash
   pip-compile --resolver=backtracking pyproject.toml
   ```
3. If unresolvable, consider:
   - Downgrading one package
   - Finding alternative package
   - Vendoring if critical

## Tools & Scripts

### pin_dependencies.py
Main dependency management script:
- Check for unpinned dependencies
- Security vulnerability scanning
- Virtual environment detection
- Lock file generation
- Outdated package detection

### Pre-commit Hooks
Automated checks on every commit:
- Version pinning verification
- Security scanning
- Virtual environment detection
- Import sorting and formatting

### GitHub Actions
Continuous dependency monitoring:
- `dependency-check.yml`: Comprehensive dependency validation
- Weekly security scans
- Automated issue creation for updates

## Best Practices

1. **Always Pin Versions**: Never use `>=`, `~=`, or `*` in production
2. **Regular Updates**: Review dependencies weekly
3. **Security First**: Patch vulnerabilities immediately
4. **Test Thoroughly**: Full test suite before updating
5. **Document Changes**: Clear commit messages for dependency updates
6. **Use Lock Files**: Always install from lock files in production
7. **No Local Overrides**: Never use `pip install --force-reinstall`
8. **Clean Environments**: Start fresh when debugging dependency issues

## Troubleshooting

### Common Issues

**Issue**: Dependency conflict during installation
```bash
# Solution: Use pip-tools resolver
pip-compile --resolver=backtracking pyproject.toml
```

**Issue**: Package not found
```bash
# Solution: Clear pip cache
pip cache purge
pip install --no-cache-dir -r requirements-lock.txt
```

**Issue**: Different behavior in production
```bash
# Solution: Verify exact versions
pip freeze > current.txt
diff current.txt requirements-lock.txt
```

## Contact & Support

For dependency-related issues:
1. Check this documentation first
2. Run `python scripts/pin_dependencies.py check`
3. Create issue with full error output
4. Tag with `dependencies` label

## Appendix: Critical Dependencies Explained

### Why These Specific Versions?

- **FastAPI 0.116.1**: Latest stable with all security patches
- **Pydantic 2.8.2**: V2 for performance, exact version for stability
- **Redis 5.0.1**: Stable version with cluster support
- **Agno 1.8.1**: Required version for swarm intelligence features
- **Structlog 24.1.0**: Latest with async context support
- **Neo4j 5.24.0**: Graph database for knowledge relationships

These versions have been tested together and provide optimal performance and stability for our use case.