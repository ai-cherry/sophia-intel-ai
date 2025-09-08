# Production Deployment Checklist for Sophia Intel AI

## 🚨 Critical Gaps for Production

### 1. **Testing Infrastructure - CRITICAL**
```yaml
Status: ❌ NOT PRODUCTION READY
Issues:
  - Test coverage target: 80% (currently unknown)
  - pytest configured but Artemis tests mixed in
  - No CI/CD test automation
  - Missing integration tests for core services
```

**Required Actions:**
```bash
# Install all dependencies
pip install -r requirements/base.txt -r requirements/dev.txt

# Run tests excluding Artemis
pytest tests/ -v -k "not artemis" --cov=app --cov-report=xml --cov-fail-under=80

# Quick test run
pytest -q -k "not artemis"

# Check coverage report
open htmlcov/index.html
```

### 2. **Secrets Management - CRITICAL**
```yaml
Status: ⚠️  PARTIALLY READY
Issues:
  - Secrets in .env files (not secure for production)
  - No vault integration (HashiCorp Vault, AWS Secrets Manager)
  - JWT_SECRET needs rotation mechanism
```

**Required Actions:**
```bash
# Move all secrets to secure vault locally
mkdir -p ~/.config/artemis
cat > ~/.config/artemis/env << 'EOF'
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
PORTKEY_API_KEY=pk-...
JWT_SECRET=$(openssl rand -hex 32)
EOF
chmod 600 ~/.config/artemis/env

# Production: Use AWS Secrets Manager or HashiCorp Vault
# Inject via ECS/Helm envFrom or compose secrets
```

### 3. **Database Migrations - MISSING**
```yaml
Status: ❌ NOT READY
Issues:
  - No migration system (Alembic required)
  - PostgreSQL schema not versioned
  - No rollback procedures
```

**Required Actions:**
```bash
# Install and initialize Alembic
pip install alembic
alembic init migrations

# Configure migrations/alembic.ini
# Set: sqlalchemy.url = ${POSTGRES_URL}

# Create initial migration
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Add migrate service to compose for auto-migration on deploy
```

### 4. **Monitoring & Observability - PARTIAL**
```yaml
Status: ⚠️  BASIC ONLY
Issues:
  - Prometheus metrics exposed but no Grafana dashboards
  - OpenTelemetry config exists but not wired
  - No log aggregation (ELK/Loki)
  - No error tracking (Sentry)
```

**Required Actions:**
```bash
# Enable OpenTelemetry (already in app/api/opentelemetry_config.py)
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Add Sentry
pip install sentry-sdk[fastapi]
export SENTRY_DSN=https://...@sentry.io/...
# Add Sentry init in app startup
```

### 5. **Load Balancing & Scaling - NOT CONFIGURED**
```yaml
Status: ❌ NOT READY
Issues:
  - Single instance deployment only
  - No nginx/traefik reverse proxy
  - No horizontal scaling config
  - Rate limiting (slowapi) in requirements but not fully configured
```

**Required Actions:**
```bash
# Add reverse proxy (nginx/traefik)
# - TLS termination, HTTP/2
# - Rate limiting per-route
# - Forward to app on port 8003

# Configure slowapi middleware globally
# Lock down CORS allow_origins to production domains
```

## ✅ What's Ready for Production

### 1. **Core Services**
```yaml
Status: ✅ READY
- Redis: Configured with persistence (appendonly yes)
- PostgreSQL: Version 15 with health checks
- Weaviate: Vector store configured
- MCP Servers:
  - Memory (8081)
  - Filesystem (8082)
  - Git (8084)
```

### 2. **Docker Infrastructure**
```yaml
Status: ✅ READY
- Multi-stage Dockerfile optimized
- Health checks configured
- Non-root user (sophia)
- Correct port: 8003 (API)
```

### 3. **API Framework**
```yaml
Status: ✅ READY
- FastAPI on port 8003
- OpenAPI docs at /docs
- Async support
- Rate limiting (slowapi) available
```

## 🎯 Use Make Targets

**Always prefer Make targets to prevent configuration drift:**

```bash
# Start full stack in order
make full-start

# Check infrastructure health
make health-infra

# Test MCP endpoints
make mcp-test

# Run all health checks
make health
```

## 📋 Pre-Production Checklist

### Environment Setup
- [ ] All API keys in ~/.config/artemis/env
- [ ] JWT_SECRET rotated and secured
- [ ] Database credentials in secure vault
- [ ] SSL certificates configured

### Testing
- [ ] Unit test coverage > 80% (excluding Artemis)
- [ ] Integration tests passing
- [ ] Load tests completed
- [ ] Security scan: `bandit -r app/`

### Database
- [ ] Alembic migrations configured
- [ ] Backup strategy: `pg_dump` scheduled
- [ ] Connection pooling configured
- [ ] Weaviate backup plan defined

### Monitoring
- [ ] Grafana dashboards created
- [ ] OTEL_EXPORTER_OTLP_ENDPOINT configured
- [ ] Sentry DSN configured
- [ ] Log aggregation active

### Deployment
- [ ] CI/CD pipeline with tests
- [ ] Blue-green deployment ready
- [ ] Rollback procedures tested
- [ ] Resource limits set

### Security
- [ ] Rate limiting configured (slowapi)
- [ ] CORS properly set for production domains
- [ ] Input validation active
- [ ] SQL injection prevention verified

## 🚀 Quick Production Deployment

### Step 1: Install Dependencies
```bash
# Production dependencies
pip install -r requirements/base.txt

# Dev dependencies (if testing on host)
pip install -r requirements/dev.txt
```

### Step 2: Run Tests
```bash
# Full test suite excluding Artemis
pytest tests/ -v -k "not artemis" --cov=app --cov-fail-under=80

# Security scan
pip install bandit
bandit -r app/
```

### Step 3: Build Production Image
```bash
# Build optimized multi-stage image
docker build -t sophia-prod:latest .

# Scan for vulnerabilities
docker scan sophia-prod:latest
# Or use Trivy: trivy image sophia-prod:latest
```

### Step 4: Deploy Services
```bash
# Preferred: Use Make targets
make full-start

# Or manually:
docker compose -f docker-compose.yml up -d redis postgres weaviate
sleep 10
alembic upgrade head
docker compose -f docker-compose.yml up -d api
# Note: api service runs python -m app.api.unified_server on port 8003
```

### Step 5: Verify Deployment
```bash
# API health (port 8003)
curl http://localhost:8003/openapi.json
curl http://localhost:8003/docs

# Infrastructure health
make health-infra

# MCP health
make mcp-test
# Or manually:
curl http://localhost:8081/health  # Memory
curl http://localhost:8082/health  # Filesystem
curl http://localhost:8084/health  # Git

# Weaviate health (port varies by compose file)
# Dev compose:
curl -sf http://localhost:8080/v1/.well-known/ready
# Prod compose:
curl -sf http://localhost:8081/v1/.well-known/ready

# Smoke tests
pytest -m smoke -q
```

## 🔴 Blocking Issues for Production

1. **No test coverage metrics** - Run `pytest -k "not artemis" --cov`
2. **Secrets in plaintext** - Move to ~/.config/artemis/env minimum
3. **No database migrations** - Implement Alembic immediately
4. **No monitoring dashboards** - Wire OTEL and Grafana
5. **No reverse proxy** - Add nginx/traefik for TLS and load balancing

## 🟡 CI/CD Next Steps

### Add Test Workflow
Create `.github/workflows/tests.yml`:
```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.11]

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -r requirements/base.txt -r requirements/dev.txt

      - name: Start infrastructure
        run: |
          docker compose -f docker-compose.yml up -d redis postgres weaviate
          sleep 10

      - name: Run tests
        run: |
          pytest tests/ -v -k "not artemis" --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs
          path: tests/logs/
```

## 🔧 Disaster Recovery

### Database Backups
```bash
# PostgreSQL backup
pg_dump -h localhost -U sophia -d sophia > backup_$(date +%Y%m%d).sql

# Restore
psql -h localhost -U sophia -d sophia < backup_20240908.sql
```

### Weaviate Backup
```bash
# Export Weaviate data
curl -X POST http://localhost:8080/v1/backups \
  -H "Content-Type: application/json" \
  -d '{"id": "backup-1", "backend": "filesystem"}'
```

### Redis Persistence
```yaml
# Already configured in docker-compose.yml:
command: redis-server --appendonly yes
```

## 📊 Current Production Readiness Score

```yaml
Overall: 45/100

✅ Infrastructure: 80/100
✅ Code Quality: 70/100
⚠️  Security: 40/100
❌ Testing: 20/100 (needs coverage metrics)
❌ Monitoring: 30/100 (OTEL not wired)
❌ Deployment: 30/100 (no CI/CD)
```

## Next Immediate Actions

1. **Fix testing now:**
```bash
pytest -q -k "not artemis"
make health
```

2. **Check infrastructure:**
```bash
make health-infra
make mcp-test
```

3. **Secure secrets:**
```bash
make env.doctor
# Move all keys to ~/.config/artemis/env
```

4. **Update pytest.ini:**
Add to existing pytest.ini:
```ini
[pytest]
addopts = -rA -k "not artemis"
filterwarnings = ignore::DeprecationWarning
markers =
    smoke: Quick smoke tests
    artemis: Artemis-specific tests (skip in Sophia)
```

**RECOMMENDATION:** Do not deploy to production until:
1. Test coverage verified > 80% (excluding Artemis)
2. Secrets moved to secure storage
3. Alembic migrations configured
4. API verified on port 8003

