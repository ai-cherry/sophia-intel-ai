# Changelog

All notable changes to the SOPHIA Intel project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.2.0] — 2025-08-21
### Added
- PR title linter requiring `[proof]` prefix
- Endpoint proof steps in deploy workflow; manifest under `proofs/`
- Context MCP service with code indexing and RAG capabilities
- Comprehensive proof artifacts directory structure
- Machine-readable service manifest for deployment verification

### Changed
- Research MCP: fixed outage, standard healthz, 8080 ports
- Context MCP: deploy-ready (APIRouter + healthz)
- Unified Fly.io checks; single `[checks.http]` per service
- All services standardized on port 8080 with consistent /healthz endpoints
- Enhanced PR template with comprehensive quality gates

### Fixed
- Research MCP service complete non-responsiveness
- Health check endpoint inconsistencies across services
- Port binding configuration issues (8000 vs 8080)
- APIRouter vs FastAPI app architecture inconsistencies

### Security/QA
- No-mocks CI gate; ACTION_SCHEMAS enforcement in PR template
- Comprehensive deployment verification with real endpoint proofs
- Automated proof artifact generation and commitment

## [Unreleased]

### Added
- **Unified Chat Interface with Feature Toggles** - Consolidated chat and web research into single interface
  - Web Access toggle for real-time information and web search
  - Deep Research toggle for multi-step analysis capabilities  
  - Training Mode toggle for knowledge capture and learning
  - Smart status display showing active features
  - Contextual tooltips for feature guidance
- **Enhanced Backend API** - Updated chat endpoints to handle feature toggle flags
  - Feature flags passed to Lambda inference API
  - Context-aware system messages based on enabled features
  - Backward compatible with existing chat functionality

### Changed
- **Simplified Navigation** - Reduced main tabs from 6 to 5 by consolidating chat functionality
- **Improved User Experience** - Single entry point for all chat-related features
- **Cleaner Codebase** - Removed duplicate WebResearchPanel component

### Removed
- **Web Research Tab** - Functionality integrated into unified chat interface
- **Redundant Components** - Cleaned up unused imports and duplicate code

### Technical
- **Frontend**: React components with Radix UI toggles and visual feedback
- **Backend**: Updated Pydantic models and FastAPI endpoints
- **Build**: Verified successful compilation with 2,281 modules transformed
- **Documentation**: Comprehensive implementation guide and user documentation

## [1.1.0] - 2025-08-16

### Added
- Complete unified SOPHIA platform with chat, web research, and knowledge management
- Enhanced Unified MCP Server as primary orchestrator
- React dashboard with modern UI components (shadcn/ui, Tailwind CSS)
- Knowledge base with embedded documentation (16 chunks from 7 files)
- Web research panel with multi-provider support (Apify, Bright Data, ZenRows)
- Universal search across MCP services, vector databases, and Notion
- Comprehensive deployment documentation

### Fixed
- **CRITICAL**: Vite host restrictions preventing external domain access
  - Added `allowedHosts: true` to `vite.config.js`
  - Enables dashboard access from production domains
  - Resolves "This host is not allowed" errors
  - Fixes blank screens on external domains

### Changed
- Consolidated frontend to single React dashboard
- Removed duplicate interfaces and legacy components
- Updated Vite configuration for production deployment
- Improved error handling and logging throughout

### Removed
- Legacy financial analysis components
- Duplicate MCP server directories
- Unused AI agent swarms
- Generic components without business value

### Documentation
- Added [VITE_HOST_FIX.md](./docs/VITE_HOST_FIX.md) with detailed explanation
- Updated [deployment README](./docs/deployment/README.md) with frontend configuration
- Created [FRONTEND_DEPLOYMENT.md](./docs/deployment/FRONTEND_DEPLOYMENT.md) guide
- Added troubleshooting section to main README

### Technical Details
- **Repository**: https://github.com/ai-cherry/sophia-intel
- **Frontend**: React + Vite + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI with health monitoring and chat proxy
- **Knowledge**: Vector embeddings with retrieval capabilities
- **Deployment**: Production-ready with proper host configuration

## [1.0.0] - 2025-08-15

### Added
- Initial SOPHIA Intel platform
- Enterprise infrastructure with Pulumi
- Docker containerization
- GitHub Actions CI/CD
- Basic MCP server architecture
- API Gateway and routing
- Initial documentation

### Infrastructure
- Lambda Labs GPU integration
- Kubernetes deployment manifests
- DNS configuration with DNSimple
- SSL/TLS certificate management
- Load balancer setup

---

## Version History

- **v1.1.0**: Unified platform with Vite host fix
- **v1.0.0**: Initial enterprise infrastructure

## Breaking Changes

### v1.1.0
- Removed financial analysis components
- Consolidated frontend interfaces
- Updated Vite configuration (requires `allowedHosts: true`)

## Migration Guide

### From v1.0.0 to v1.1.0

1. **Update Vite Configuration**:
   ```javascript
   // apps/dashboard/vite.config.js
   preview: {
     host: '0.0.0.0',
     allowedHosts: true  // Add this line
   }
   ```

2. **Remove Legacy Components**:
   - Delete `apps/interface/` directory
   - Remove financial analysis agents
   - Clean up unused MCP servers

3. **Update Environment Variables**:
   - Check [environment-variables.md](./docs/environment-variables.md)
   - Ensure API endpoints are correctly configured

4. **Rebuild Frontend**:
   ```bash
   cd apps/dashboard
   npm install
   npm run build
   ```

## Support

For issues related to:
- **Vite Host Configuration**: See [VITE_HOST_FIX.md](./docs/VITE_HOST_FIX.md)
- **Deployment**: See [deployment/README.md](./docs/deployment/README.md)
- **General Issues**: Create an issue on [GitHub](https://github.com/ai-cherry/sophia-intel/issues)

