# Pay Ready Business Intelligence Dashboard

## Overview
The Pay Ready BI platform surfaces executive analytics, Flowwise Agent Factory workflows, and Agno v2 Developer Studio orchestration inside a single dashboard. This document summarizes the runnable components, API endpoints, and configuration required to operate the stack.

## Frontend Components
- `src/dashboard/DashboardAppShell.tsx` renders the three-tab navigation with routing state.
- `src/dashboard/BusinessIntelligenceTab.tsx` queries `/api/bi/metrics` and visualizes KPI cards with tag pills sourced from the metric schema.
- `src/dashboard/AgentFactoryTab.tsx` consumes `/api/flowwise/factories` through `FlowwiseClient` to display factory health and agent launch links.
- `src/dashboard/DeveloperStudioTab.tsx` consumes `/api/agno/workspaces` via `AgnoClient` to list Agno v2 workspaces and registered agents.

All dashboard component filenames follow the `[Section][Component].tsx` convention and rely on `src/lib/dashboardTypes.ts` for shared contracts.

## Agent Integrations
- Flowwise definitions live in `config/agents/flowwise_factories.json` and are served by `FlowwiseGateway`. Canonical agent IDs follow `FLW_[DEPT]_[FUNCTION]`.
- Agno v2 workspaces are maintained in `config/agents/agno_workspaces.json` with IDs matching `AGN_[PURPOSE]_vVERSION`.
- MCP receivers register `workbench.flowwise.dispatch` and `workbench.agno.dispatch` tools through `app/mcp/receivers/workbench.py`, wiring workbench-ui requests into the unified MCP server.

## Data & Embeddings
- Business metric schema: `schemas/business_metrics/pay_ready_metrics.yaml`.
- Meta-tagging rules: `schemas/business_metrics/meta_tags.yaml`, enforced by `app/indexing/meta_tagging.py`.
- Metric loading and indexing pipeline: `app/services/business_metrics.py` and `app/embeddings/business_embeddings.py`. Embeddings write into the unified vector store namespace `pay_ready_business_intelligence` and capture canonical tags.

## API Endpoints
- `GET /api/bi/metrics` → `BusinessMetric` list with background embedding refresh.
- `GET /api/flowwise/factories` → `FlowwiseFactory` records.
- `GET /api/agno/workspaces` → `AgnoWorkspace` records.

Routers are added in `app/api/routers/bi_dashboard.py` and mounted from `app/api/main.py`.

## Configuration
- Environment profile: `config/environments/pay_ready_bi.json` declares dedicated Flowwise and Agno base URLs plus the BI vector namespace.
- Required secrets: `FLOWWISE_API_KEY`, `AGNO_API_KEY`.

## Validation
- Python modules compile successfully: `python3 -m compileall app/services/business_metrics.py app/services/flowwise_gateway.py app/services/agno_workspaces.py app/embeddings/business_embeddings.py app/indexing/meta_tagging.py app/mcp/receivers/workbench.py`.
- TypeScript sources covered by `tsconfig.json`; install dependencies with `npm install` and run `npx tsc --noEmit` once packages are available.

## Follow-up
- Connect Flowwise and Agno environment secrets in deployment vaults.
- Extend dashboard styling to match Pay Ready brand system once design tokens land in workbench-ui.
- Add end-to-end tests once the frontend build pipeline is wired into CI.
