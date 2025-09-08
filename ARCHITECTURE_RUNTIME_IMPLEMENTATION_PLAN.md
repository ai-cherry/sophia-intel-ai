# Architecture/Runtime Standardization Implementation Plan
**Sophia Intel AI - Zero Friction Cross-Platform Development**

## Executive Summary

This plan implements a comprehensive architecture/runtime standardization strategy to eliminate "it works on my machine" issues across Mac (arm64/x86_64) and Linux (amd64/arm64) platforms. The goal is deterministic installs, early actionable preflight failures, and production-aligned Docker/CI matrices.

## Current State Assessment

### ✅ **Already Implemented**
- **Preflight Validator**: `scripts/agents_env_check.py` with arch/Rosetta/pydantic_core checks
- **Unified Startup**: `unified-start.sh` canonical entry point  
- **Basic Makefile**: env.check, rag.start, rag.test, lint targets
- **Devcontainer Structure**: `.devcontainer/` with setup scripts
- **Environment Separation**: .env.sophia vs Artemis CLI separation

### ❌ **Missing Critical Components**

## Phase A Implementation: Preflight & Polish (Day 1-2)

### A1: Enhanced Preflight Validator

**Current**: Basic arch/Python/pydantic_core checks  
**Required**: Add comprehensive dependency and environment validation

```python
# Enhance scripts/agents_env_check.py with:
def check_required_dependencies() -> List[CheckResult]:
    """Check critical runtime dependencies"""
    
def check_environment_files() -> List[CheckResult]:
    """Validate .env.* configuration consistency"""
    
def check_docker_availability() -> List[CheckResult]:
    """Check Docker setup for devcontainer option"""
    
def check_wheel_architecture() -> List[CheckResult]:
    """Deep wheel/arch validation beyond pydantic_core"""
```

### A2: Memory API Polish Enhancement

**Current**: Basic memory services exist  
**Required**: Standardized error handling, OpenAPI security, rate limiting

**Missing Components**:
1. **Retry-After Headers**: 429 responses need proper backoff timing
2. **OpenAPI Security Scheme**: Bearer authentication documentation
3. **JSON Error Envelope**: Consistent error response format
4. **Health Check Matrix**: /health, /ready, /live, /version endpoints

### A3: Orchestrator RAG Integration

**Current**: `unified-start.sh` exists but missing RAG service definitions  
**Required**: Optional RAG service management

```bash
# Add to unified-start.sh:
--with-rag          # Start sophia_memory:8767, artemis_memory:8768
--no-rag            # Explicitly disable RAG services
```

## Phase B Implementation: Toolchain Determinism (Day 2-4)

### B1: Python Version Policy

**Missing**: `.python-version` file and version enforcement
```bash
# Create .python-version
3.11.10
```

**Required**: Update preflight to enforce blessed version policy

### B2: Requirements Management Strategy

**Current State**: Scattered requirements across multiple files  
**Target Architecture**:
```
requirements/
├── base.txt              # Core runtime dependencies
├── dev.txt               # Development tools (ruff, pytest, etc.)
├── optional-rag.txt      # RAG-specific dependencies
├── lock-linux.txt        # Platform-specific locks for CI/prod
└── lock-macos.txt        # macOS compatibility matrix
```

### B3: Architecture-Aware Installation

**Missing**: Platform-specific installation guidance
```python
# Add to scripts/agents_env_check.py
def check_installation_path() -> List[CheckResult]:
    """Recommend installation method based on platform/arch"""
    # Recommend devcontainer for macOS mixed-arch scenarios
    # Guide pip vs source builds for pydantic-core conflicts
```

## Phase C Implementation: Devcontainers & Docker (Day 3-5)

### C1: Devcontainer Enhancement

**Current**: Basic devcontainer scripts exist  
**Required**: Multi-architecture support

```json
// .devcontainer/devcontainer.json
{
  "name": "Sophia Intel AI",
  "dockerComposeFile": "docker-compose.yml",
  "service": "sophia-dev",
  "workspaceFolder": "/workspace",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    }
  },
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff"
      ]
    }
  },
  "postCreateCommand": "make env.check && pip3 install -r requirements/dev.txt"
}
```

### C2: Multi-Architecture Docker Strategy

**Missing**: Buildx multi-platform images
```dockerfile
# Update Dockerfile for multi-arch
FROM python:3.11-slim

# Install platform-specific optimizations
RUN if [ "$(uname -m)" = "aarch64" ]; then \
        pip install --extra-index-url https://www.piwheels.org/simple/ pydantic-core; \
    else \
        pip install pydantic-core; \
    fi
```

### C3: Docker Compose Enhancement

**Current**: Basic services defined  
**Required**: Platform specification and health checks
```yaml
# docker-compose.dev.yml
services:
  sophia-dev:
    platform: linux/amd64  # Standardize on amd64 for consistency
    build:
      context: .
      platforms:
        - linux/amd64
        - linux/arm64
```

## Phase D Implementation: CI/CD Matrix (Day 4-6)

### D1: GitHub Actions Multi-Platform Matrix

**Missing**: `.github/workflows/ci.yml` with architecture matrix
```yaml
strategy:
  matrix:
    include:
      - os: ubuntu-latest
        platform: linux/amd64
        test_level: full
      - os: ubuntu-latest  
        platform: linux/arm64
        test_level: build_smoke
      - os: macos-14  # Apple Silicon
        platform: darwin/arm64
        test_level: preflight_only
      - os: macos-13  # Intel
        platform: darwin/x86_64
        test_level: preflight_only
```

### D2: Preflight Gating

**Required**: CI integration of environment checks
```yaml
- name: Environment Preflight
  run: |
    python3 scripts/agents_env_check.py --json > preflight.json
    if [ $? -eq 2 ]; then
      echo "Preflight failed - see details above"
      exit 1
    fi
```

### D3: Multi-Architecture Build Pipeline

**Missing**: Docker buildx integration
```yaml
- name: Build Multi-Arch Images
  uses: docker/build-push-action@v5
  with:
    platforms: linux/amd64,linux/arm64
    tags: sophia-intel-ai:${{ github.sha }}
```

## Phase E Implementation: Developer Onboarding (Day 5-7)

### E1: Onboarding Documentation

**Missing**: `DEVELOPER_ONBOARDING.md` with platform-specific flows

### E2: Platform-Specific Setup Guides

**Required**: Remediation playbooks per platform
```markdown
## macOS Apple Silicon Setup
1. Run preflight: `python3 scripts/agents_env_check.py`
2. If pydantic_core fails:
   - Option A: Use devcontainer (recommended)
   - Option B: `pip3 uninstall pydantic-core && pip3 install --force-reinstall pydantic-core`
   - Option C: Build from source: `brew install rust && pip3 install --no-binary :all: pydantic-core`
```

## Implementation Timeline

| Phase | Duration | Key Deliverables | Priority |
|-------|----------|-----------------|----------|
| **A** | 1-2 days | Enhanced preflight, memory API polish, RAG integration | Critical |
| **B** | 2-3 days | Python policy, requirements structure, arch-aware installs | High |
| **C** | 2-3 days | Multi-arch devcontainers, Docker buildx, compose updates | High |
| **D** | 2-3 days | CI matrix, preflight gating, multi-arch builds | Medium |
| **E** | 1-2 days | Onboarding docs, platform guides | Medium |

**Total Duration**: 8-13 days

## Success Metrics

### Acceptance Criteria
- [ ] `make env.check` reports 0% architecture mismatches
- [ ] Devcontainer works consistently on Intel/Apple Silicon Macs
- [ ] CI passes on Linux amd64/arm64, macOS Intel/Apple Silicon
- [ ] `make rag.start && make rag.test` succeeds locally and in CI
- [ ] Memory APIs return proper Retry-After headers on 429
- [ ] Zero "pydantic_core won't import" support requests

### Performance Targets
- Environment setup time: < 10 minutes (any platform)
- Preflight check time: < 30 seconds
- Docker build time: < 5 minutes (cached)
- CI pipeline duration: < 15 minutes

## Risk Mitigation

### High-Risk Components
1. **pydantic-core wheel mismatches**: Multiple remediation paths documented
2. **Docker multi-arch complexity**: Staged rollout with amd64 first
3. **CI cost implications**: ARM64 builders cost optimization

### Rollback Strategy
```bash
# Emergency rollback to working state
git checkout HEAD~1 -- scripts/agents_env_check.py
git checkout HEAD~1 -- requirements/
git checkout HEAD~1 -- .devcontainer/
```

## Immediate Next Steps (Day 1)

1. **Enhance Preflight Validator** (2 hours):
   ```bash
   # Add dependency and wheel arch validation
   # Extend scripts/agents_env_check.py
   ```

2. **Memory API Polish** (3 hours):
   ```bash
   # Add Retry-After headers
   # Implement JSON error envelope
   # Add OpenAPI security scheme
   ```

3. **RAG Services Integration** (2 hours):
   ```bash
   # Update unified-start.sh with --with-rag flag
   # Add sophia_memory and artemis_memory service definitions
   ```

4. **Requirements Restructure** (2 hours):
   ```bash
   # Create requirements/ directory structure
   # Split base/dev/optional dependencies
   ```

This plan provides a systematic approach to eliminate architecture/runtime mismatches while maintaining the established patterns of unified startup and environment separation.
