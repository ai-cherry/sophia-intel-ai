# Changelog

All notable changes to the SOPHIA Intel project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

