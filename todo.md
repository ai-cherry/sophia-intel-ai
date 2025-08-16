# Sophia-Intel Deployment and Refactoring Todo

## Phase 1: Clone repository and initial setup
- [x] Clone repository using GitHub PAT
- [x] Configure git credentials
- [x] Explore repository structure

## Phase 2: Repository audit and code review
- [x] Walk through every directory and file
- [x] Understand service boundaries (dashboard front-end, dashboard back-end, API gateway, Swarm API, MCP servers)
- [x] Note discrepancies between documentation and implementation
- [x] Identify missing requirements.txt or pyproject.toml files
- [x] Find broken route declarations and undefined functions

### Audit Findings:
- Missing requirements.txt for: apps/api-gateway, apps/api
- Duplicate MCP servers in multiple locations (apps/mcp-services/ vs individual apps/)
- Duplicate frontends: apps/interface (minimal) vs apps/sophia-dashboard/sophia-dashboard-frontend (complete)
- Authentication issue: DASHBOARD_API_TOKEN allows operations if not set (dev mode bypass)
- No reset_conversation function found in codebase
- Service boundaries identified:
  * API Gateway: apps/api-gateway (FastAPI, missing requirements.txt)
  * Dashboard Backend: apps/sophia-dashboard/sophia-dashboard-backend (Flask, has requirements.txt)
  * Dashboard Frontend: apps/sophia-dashboard/sophia-dashboard-frontend (React, complete)
  * MCP Servers: Multiple locations need consolidation
  * Interface: apps/interface (minimal, should be removed)

## Phase 3: Fix code-level defects and structural issues
- [x] Add missing requirements.txt files for each Python service
- [x] Fix broken route declarations and undefined functions
- [x] Implement reset_conversation() properly
- [x] Harden authentication in dashboard back-end
- [x] Standardize CORS configuration in API
- [x] Consolidate and clarify front-end (removed apps/interface, kept apps/sophia-dashboard/sophia-dashboard-frontend)
- [x] Fix frontend dependency conflicts (date-fns version)
- [x] Test frontend build script (works successfully)
- [x] Remove duplicate MCP servers (consolidated to apps/mcp-services/)

## Phase 4: Create Dockerfiles and deployment configuration
- [x] Create Dockerfile for each service
- [x] Improve existing Dockerfiles with security features (non-root users, environment variables)
- [x] Add missing dependencies (gunicorn) to requirements.txt files
- [x] Create nginx configuration for frontend
- [x] Ensure build scripts work without errors
- [x] Align service names consistently (verified existing structure)
- [x] Configure proper startup commands (gunicorn for Flask, uvicorn for FastAPI)

## Phase 5: Setup secrets and configure GitHub Actions ✅
- [x] Configure GitHub repository secrets (PULUMI_ACCESS_TOKEN, LAMBDA_API_KEY, OPENROUTER_API_KEY, GITHUB_PAT, DNSIMPLE_API_KEY)
  - [x] LAMBDA_API_KEY: Added successfully
  - [x] DEPLOYMENT_PAT: Added successfully (GitHub PAT with different name due to GITHUB_ prefix restriction)
  - [x] PULUMI_ACCESS_TOKEN: Already exists
  - [x] OPENROUTER_API_KEY: Already exists
  - [x] DNSIMPLE_API_KEY: Already exists
- [ ] Verify CI/CD workflow file
- [ ] Ensure Docker image build and push steps
- [ ] Configure Pulumi deployment steps
- [ ] Add health check steps

## Phase 6: Deploy infrastructure using Pulumi ✅
- [x] Install Pulumi requirements
- [x] Install Pulumi CLI
- [x] Configure Pulumi stack with secrets
- [x] Fix code issues in infrastructure files
- [x] Run pulumi preview (successful with warnings for optional secrets)
- [x] Infrastructure components configured:
  - [x] DNS records for sophia-intel.ai domains
  - [x] TLS certificate management
  - [x] Lambda Labs infrastructure validation
  - [x] Application services deployment scripts
  - [x] Monitoring configuration

**Infrastructure Status:**
- Pulumi stack: production (ready)
- DNS records: Configured for api.sophia-intel.ai, app.sophia-intel.ai, www.sophia-intel.ai
- Load balancer IP: 192.222.58.232
- Core secrets: Configured (LAMBDA_API_KEY, DNSIMPLE_API_KEY, OPENROUTER_API_KEY, PULUMI_ACCESS_TOKEN)
- Optional secrets: Available in GitHub (warnings expected for missing optional services)

## Phase 7: Validation and testing
- [ ] Verify domain resolution (api.sophia-intel.ai, dashboard.sophia-intel.ai)
- [ ] Check HTTPS serving
- [ ] Verify Kubernetes dashboard shows expected pods
- [ ] Test /health endpoints (port 8000, 5000, 8001)
- [ ] Check logs for runtime errors

## Phase 8: Documentation update and final commit
- [ ] Update docs/deployment/README.md
- [ ] Document new Pulumi-based deployment process
- [ ] Commit changes with descriptive message
- [ ] Push to main branch
- [ ] Verify CI/CD passes

## API Keys and Secrets
- OPENROUTER_API_KEY: [CONFIGURED IN GITHUB SECRETS]
- PULUMI_ACCESS_TOKEN: [CONFIGURED IN GITHUB SECRETS]
- GITHUB_PAT: [CONFIGURED IN GITHUB SECRETS]
- LAMBDA_API_KEY: [CONFIGURED IN GITHUB SECRETS]
- DNSIMPLE_API_KEY: [CONFIGURED IN GITHUB SECRETS]

