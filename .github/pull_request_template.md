# 🚀 SOPHIA v4.2 — Pull Request

> **Rules:** Cloud-only. No mocks. No fakes. No sims. Prove everything with real artifacts.

## 0) Summary
**Title:**  
**Scope / Component(s):**  
**Why:**  
**What changed (1–3 bullets):**
- 
- 
- 

---

## 1) Acceptance Checklist (HARD GATES)

### 🟢 Reality Proof (required)
- [ ] **Curl proof(s) committed** under `proofs/` (headers + body), e.g.:
  - `proofs/healthz/<service>.txt`
  - Any endpoint proofs relevant to this PR
- [ ] **GitHub evidence** (if code flow): PR links/commit SHAs included below
- [ ] **Screenshots/recordings** (if UI): linked or added to PR

### 🩺 Health & Ports
- [ ] All changed services expose **`GET /healthz`** returning JSON `{ "status": "ok", "service": "<name>", "version": "4.2.0" }`
- [ ] Fly config(s) use **`internal_port = 8080`** and **single** `[checks.http]` with `path="/healthz"`
- [ ] Docker `CMD` binds **`0.0.0.0:$PORT`** with `PORT=8080`

### 🧠 ActionEngine Contracts
- [ ] New/changed endpoints registered in **`ACTION_SCHEMAS.md`** (schema version bumped if needed)
- [ ] Contract tests updated (if applicable)

### 🧪 CI / Quality
- [ ] CI green (ruff, mypy, pytest, contract tests)
- [ ] **No-mocks gate** (repo-wide) passes (no `mock|stub|fake|placeholder|simulate|noop|dummy` in non-test code)
- [ ] Secrets **not** echoed or logged (validated by reviewers)

### 🔒 Security & Observability
- [ ] Sentry breadcrumbs added/updated (where applicable)
- [ ] Prometheus metrics updated (counters/histograms for new handlers)
- [ ] Inputs validated; external calls time-bounded; error paths normalized

---

## 2) Proof Artifacts (paste links/inline)

### Health Check Proofs
```bash
# Example:
curl -i https://sophia-<service>.fly.dev/healthz
# HTTP/1.1 200 OK
# {"status":"ok","service":"<service>","version":"4.2.0"}
```

### GitHub Evidence
- **Commit SHA:** `<commit-hash>`
- **Related PRs:** #<number>
- **Branch:** `<branch-name>`

### Screenshots/Recordings
<!-- Attach or link screenshots for UI changes -->

---

## 3) Deployment & Rollback Plan

### Pre-Deploy
- [ ] Secrets verified (no missing env vars)
- [ ] Dependencies updated in `requirements.txt`
- [ ] Fly.io config validated

### Deploy Command
```bash
fly deploy --app sophia-<service> --build-arg CACHE_BUSTER=$(date +%s)
```

### Rollback Plan
```bash
# If deployment fails:
fly machines list --app sophia-<service>
fly machines restart <machine-id>
# Or rollback to previous image
```

### Post-Deploy Verification
- [ ] Health check passes: `curl https://sophia-<service>.fly.dev/healthz`
- [ ] Functional test passes
- [ ] No error spikes in logs

---

## 4) Review Notes

<!-- Any additional context for reviewers -->

---

## 5) Breaking Changes

- [ ] **No breaking changes**
- [ ] **Breaking changes documented below:**

<!-- If breaking changes, document migration path -->

---

**By submitting this PR, I confirm:**
- All artifacts are real (no mocks/fakes/sims)
- Health checks follow v4.2 standards
- ActionEngine contracts are updated
- CI passes and security validated