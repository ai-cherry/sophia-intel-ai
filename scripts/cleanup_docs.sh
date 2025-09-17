#!/bin/bash

# Document Cleanup Script for Sophia Intel AI
# This script implements the document management strategy

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}📚 Starting Documentation Cleanup${NC}"
echo "===================================="

# Create new directory structure
echo -e "${YELLOW}Creating new directory structure...${NC}"
mkdir -p docs/{guides/{deployment,development,operations,integrations},archive/{2024-reports,historical-plans,completed-work}}
mkdir -p docs/{api,swarms,notes}

# Phase 1: Archive old reports and completed work
echo -e "${YELLOW}Archiving old reports and completed work...${NC}"

# Move historical reports
for file in AGNO_UPGRADE_SUMMARY.md UI_IMPLEMENTATION_REPORT.md UNIFIED_SYSTEM_REPORT.md COMPLETE_SYSTEM_TEST.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/2024-reports/
        echo -e "  ${GREEN}✓${NC} Archived $file"
    fi
done

# Move completed work summaries
for file in SWARM_REFACTORING_SUMMARY.md DEDUPLICATION_STRATEGY.md SECURITY_SUMMARY.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/completed-work/
        echo -e "  ${GREEN}✓${NC} Archived $file"
    fi
done

# Move historical plans
if [ -f "UPGRADE_Q3_2025.md" ]; then
    mv UPGRADE_Q3_2025.md docs/archive/historical-plans/
    echo -e "  ${GREEN}✓${NC} Archived UPGRADE_Q3_2025.md"
fi

# Phase 2: Consolidate duplicate deployment documents
echo -e "${YELLOW}Consolidating deployment documents...${NC}"

cat > docs/guides/deployment/README.md << 'EOF'
---
title: Unified Deployment Guide
type: guide
status: active
version: 2.0.0
last_updated: 2024-09-01
ai_context: high
dependencies: []
tags: [deployment, fly.io, pulumi, infrastructure]
---

# 🚀 Unified Deployment Guide

## 🎯 Purpose
Single source of truth for deploying Sophia Intel AI across all environments.

## 📋 Prerequisites
- Python 3.11+
- Node.js 18+
- Docker
- Fly.io CLI (for cloud deployment)
- Pulumi CLI (for infrastructure as code)

## 🔧 Implementation

### Local Development
```bash
# Quick start
./scripts/start-local.sh

# With monitoring
./scripts/start-mcp-system.sh
```

### Cloud Deployment (Fly.io)
```bash
# Deploy all services
fly deploy --config fly.api.toml
fly deploy --config fly.ui.toml
```

### Infrastructure as Code (Pulumi)
```bash
# Deploy infrastructure
cd infra/pulumi
pulumi up
```

## ✅ Validation
- Health check: http://localhost:8000/health
- Metrics: http://localhost:9090
- UI: http://localhost:3000

## 🚨 Common Issues
See TROUBLESHOOTING.md

## 📚 Related
- [Architecture Overview](../../architecture/system-design.md)
- [API Documentation](../../api/rest-api.md)
- [Monitoring Guide](../operations/monitoring.md)
EOF

# Archive original deployment files
mkdir -p docs/archive/historical-plans/deployment-versions/
for file in DEPLOYMENT.md DEPLOYMENT_*.md FLY_DEPLOYMENT*.md SOPHIA_INTEL_AI_DEPLOYMENT*.md PULUMI_2025_DEPLOYMENT_GUIDE.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/historical-plans/deployment-versions/
        echo -e "  ${GREEN}✓${NC} Archived $file"
    fi
done

# Phase 3: Consolidate Portkey documentation
echo -e "${YELLOW}Consolidating Portkey documentation...${NC}"

cat > docs/guides/integrations/portkey.md << 'EOF'
---
title: Portkey Integration Guide
type: guide
status: active
version: 1.0.0
last_updated: 2024-09-01
ai_context: medium
dependencies: []
tags: [portkey, llm, api-gateway]
---

# 🔌 Portkey Integration Guide

## 🎯 Purpose
Complete guide for Portkey AI Gateway integration.

## 📋 Prerequisites
- Portkey API key
- LLM provider API keys

## 🔧 Implementation

### Basic Setup
```python
from portkey_ai import Portkey

portkey = Portkey(
    api_key="your-api-key",
    virtual_key="your-virtual-key"
)
```

### Virtual Keys Configuration
[Configuration details from PORTKEY_VIRTUAL_KEYS_SETUP.md]

### Usage Examples
[Examples from PORTKEY_USAGE_EXAMPLES.md]

## ✅ Validation
Test with: `python -m app.test_portkey`

## 📚 Related
- [API Keys Guide](API_KEYS_GUIDE.md)
EOF

# Archive original Portkey files
for file in PORTKEY*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/historical-plans/
        echo -e "  ${GREEN}✓${NC} Archived $file"
    fi
done

# Phase 4: Create INDEX.md
echo -e "${YELLOW}Creating documentation index...${NC}"

cat > docs/INDEX.md << 'EOF'
---
title: Documentation Index
type: index
status: active
version: 1.0.0
last_updated: 2024-09-01
ai_context: high
---

# 📚 Documentation Index

## Core Documents
- [README](../README.md) - Project overview
- [QUICKSTART](../QUICKSTART.md) - 5-minute setup
- [CURRENT_STATE](CURRENT_STATE.md) - Live system state

## Guides
### Deployment
- [Unified Deployment Guide](guides/deployment/README.md)

### Development
- [Setup Guide](guides/development/setup.md)
- [Testing Guide](guides/development/testing.md)

### Operations
- [Monitoring](guides/operations/monitoring.md)
- [Troubleshooting](guides/operations/troubleshooting.md)

### Integrations
- [Portkey](guides/integrations/portkey.md)
- [MCP Protocol](guides/integrations/mcp.md)

## Architecture
- [System Design](architecture/system-design.md)
- [Component Map](architecture/component-map.md)
- [Decision Records](architecture/decisions/README.md)

## API Documentation
- [REST API](api/rest-api.md)
- [WebSocket API](api/websocket-api.md)
- [MCP Protocol](api/mcp-protocol.md)

## Swarms
- [Patterns](swarms/patterns.md)
- [Orchestration](swarms/orchestration.md)
- [Optimization](swarms/optimization.md)

## Recent Changes
- [MCP Bridge Integration](SWARM_MCP_INTEGRATION.md)
- [UI Integration Plan](UI_INTEGRATION_PLAN.md)
- [Phase 2 Implementation](../PHASE_2_IMPLEMENTATION_PLAN.md)
EOF

# Phase 5: Create CURRENT_STATE.md
echo -e "${YELLOW}Creating current state document...${NC}"

cat > docs/CURRENT_STATE.md << 'EOF'
---
title: Current System State
type: reference
status: active
version: 1.0.0
last_updated: 2024-09-01
ai_context: high
auto_update: true
---

# 🔄 Current System State

## Active Services

### API Endpoints
- **Unified API**: http://localhost:8000
  - Health: `/health`
  - Swarms: `/teams/run`
  - NL Interface: `/api/nl/process`
  - Memory: `/memory/search`, `/memory/add`

- **MCP Server v2**: http://localhost:8004
  - Health: `/health`
  - Metrics: `/metrics`

### UI Applications
- **Agent UI**: http://localhost:3000
- **Streamlit Chat**: http://localhost:8501

### Infrastructure
- **Redis**: redis://localhost:6379
- **Weaviate**: http://localhost:8080
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

## Configuration
- **Environment**: development
- **Optimization Modes**: lite, balanced, quality
- **Active Swarms**: coding-debate, improved-solve, simple-agents, mcp-coordinated

## Recent Deployments
- Last deployment: 2024-09-01
- Version: 2.0.0
- Status: Healthy

## Active Features
- ✅ Unified Orchestrator Facade
- ✅ MCP Bridge System
- ✅ WebSocket Real-time Updates
- ✅ Memory Context Integration
- ✅ Mode Normalization
- ✅ Circuit Breakers
- ✅ Performance Monitoring

## Known Issues
- None currently

## Next Maintenance
- Scheduled: 2024-09-08
- Type: Documentation review
EOF

# Phase 6: Create QUICKSTART.md if it doesn't exist
if [ ! -f "QUICKSTART.md" ]; then
    echo -e "${YELLOW}Creating QUICKSTART.md...${NC}"
    cat > QUICKSTART.md << 'EOF'
# 🚀 Quick Start Guide

## 5-Minute Setup

### 1. Clone and Install
```bash
git clone https://github.com/yourusername/sophia-intel-ai.git
cd sophia-intel-ai
pip install -r requirements.txt
npm install
```

### 2. Configure Environment
```bash
cp .env.template .env
# Edit .env with your API keys
```

### 3. Start Everything
```bash
./scripts/start-mcp-system.sh
```

### 4. Test
- Open http://localhost:3000
- Try: "Implement a binary search algorithm"

That's it! 🎉

For detailed setup, see [docs/guides/development/setup.md](docs/guides/development/setup.md)
EOF
    echo -e "  ${GREEN}✓${NC} Created QUICKSTART.md"
fi

# Phase 7: Move remaining documents to appropriate locations
echo -e "${YELLOW}Organizing remaining documents...${NC}"

# Move implementation plans to guides
for file in *IMPLEMENTATION*.md *PLAN*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/guides/development/
        echo -e "  ${GREEN}✓${NC} Moved $file to guides/development/"
    fi
done

# Move infrastructure reports to archive
for file in *INFRASTRUCTURE*.md *REPORT*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/archive/2024-reports/
        echo -e "  ${GREEN}✓${NC} Archived $file"
    fi
done

# Move troubleshooting to operations
if [ -f "TROUBLESHOOTING.md" ]; then
    mv TROUBLESHOOTING.md docs/guides/operations/troubleshooting.md
    echo -e "  ${GREEN}✓${NC} Moved TROUBLESHOOTING.md to operations"
fi

# Final statistics
echo -e "\n${GREEN}📊 Cleanup Complete!${NC}"
echo "===================================="

# Count files
ROOT_DOCS=$(ls -1 *.md 2>/dev/null | wc -l)
ARCHIVED=$(find docs/archive -name "*.md" | wc -l)
ORGANIZED=$(find docs/guides -name "*.md" | wc -l)

echo -e "Root-level docs remaining: ${GREEN}$ROOT_DOCS${NC} (target: < 10)"
echo -e "Documents archived: ${YELLOW}$ARCHIVED${NC}"
echo -e "Documents organized: ${GREEN}$ORGANIZED${NC}"

echo -e "\n${GREEN}✅ Documentation is now AI-swarm optimized!${NC}"
echo -e "Next steps:"
echo -e "  1. Review ${YELLOW}docs/INDEX.md${NC}"
echo -e "  2. Update ${YELLOW}docs/CURRENT_STATE.md${NC} with latest info"
echo -e "  3. Add metadata headers to remaining active docs"
echo -e "  4. Set up CI validation for documentation"
