# Sophia Intel Deployment Ship Checklist

## Pre-Deployment Validation

### ✅ CI/CD Pipeline Status
All CI jobs must be green before deployment:

1. **Dependencies & Lock File** (`deps_uv_lock`)
   - ✅ uv sync --frozen completes successfully
   - ✅ Core imports (loguru, qdrant_client, fastapi, uvicorn, httpx) work
   - 📁 Artifacts: `uv.lock.sha256`

2. **Code Hygiene** (`hygiene_sweep`)
   - ✅ No forbidden patterns (roo|portkey|backup) in codebase
   - ✅ No .venv directory committed
   - 📁 Artifacts: `hygiene.log`

3. **Router Allow-List Enforcement** (`router_allowlist_test`)
   - ✅ Only approved models (gpt-4o, gpt-4o-mini) allowed
   - ✅ Unapproved models correctly rejected
   - 📁 Artifacts: `router-allowlist-test-results`

4. **Secrets Presence Gate** (`secrets_presence_gate`)
   - ✅ OPENROUTER_API_KEY present
   - ✅ QDRANT_API_KEY present
   - ✅ QDRANT_URL present
   - ✅ NEON_DATABASE_URL present
   - ✅ REDIS_URL present
   - 📁 Artifacts: `secrets-status`

5. **Connectivity Smoke Tests** (`connectivity_smoke`)
   - ✅ OpenRouter API: GET /models returns 200, approved models present
   - ✅ OpenRouter API: POST /chat/completions returns 200, valid response
   - ✅ Qdrant: GET /collections returns 200, collections listed
   - ✅ Neon PostgreSQL: Connection successful, database/timestamp returned
   - ✅ Redis: PING returns PONG
   - 📁 Artifacts: `connectivity-smoke-logs` (openrouter.log, qdrant.log, neon.log, redis.log)

6. **Code Quality** (`lint`)
   - ✅ Python compilation check passes
   - ✅ Black formatting check passes
   - ✅ MyPy type checking (optional)

7. **Test Suite** (`test`)
   - ✅ All unit tests pass
   - ✅ Health checks pass
   - ✅ Integration tests with mock services

8. **Security Scan** (`security`)
   - ✅ Bandit security scan completed
   - ✅ Safety vulnerability check completed

### 🔗 CI Job Links
- **Latest CI Run**: https://github.com/ai-cherry/sophia-intel/actions
- **Dependencies**: Look for `deps_uv_lock` job
- **Hygiene**: Look for `hygiene_sweep` job  
- **Router Tests**: Look for `router_allowlist_test` job
- **Secrets**: Look for `secrets_presence_gate` job
- **Connectivity**: Look for `connectivity_smoke` job
- **Build Status**: Look for `build-status` job

### 📊 Evidence Requirements
Each deployment must have:
1. **Green CI badge** on main branch
2. **Connectivity logs** showing real API responses
3. **Secrets validation** confirming all required credentials present
4. **Router enforcement** proving only approved models allowed

### 🚨 Deployment Blockers
Do NOT deploy if:
- Any CI job is red/failing
- Connectivity smoke tests show API failures
- Required secrets are missing
- Forbidden patterns detected in code
- Router allows unapproved models

### 📈 Success Metrics
- **OpenRouter**: 200 responses, approved models available
- **Qdrant**: 200 response, collections accessible  
- **Neon**: Connection successful, query returns data
- **Redis**: PING/PONG successful
- **Router**: Only gpt-4o and gpt-4o-mini allowed

## Post-Deployment Verification

### 🔍 Production Health Checks
After deployment, verify:
1. All endpoints return expected responses
2. Database connections are stable
3. Vector search is functional
4. LLM routing works correctly
5. No error spikes in logs

### 📝 Rollback Plan
If issues detected:
1. Revert to previous known-good commit
2. Re-run CI pipeline
3. Validate connectivity smoke tests
4. Monitor for 15 minutes post-rollback

---

**Last Updated**: August 14, 2025  
**Version**: 1.0  
**Maintainer**: Sophia Intel DevOps Team
