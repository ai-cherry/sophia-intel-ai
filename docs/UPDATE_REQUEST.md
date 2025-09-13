# Documentation Update Request

## Current State
- Repository consolidated from 400+ docs to a clean, enforceable structure.
- Sophia separated into sidecar repository (ai-cherry/sophia-cli).
- MCP servers running locally but previously under-documented.
- Sophia connection now via local path (SOPHIA_PATH preferred; legacy ARTEMIS_PATH supported) with planned HTTP bridge.

## Required Updates
1) LOCAL_DEV_AND_DEPLOYMENT.md
   - Add complete startup sequence with verification (infra → MCP → dev shell).
   - Document MCP server integration and health checks.
   - Clarify Sophia connection options (local vs remote via future HTTP bridge).

2) MCP Integration Guide
   - Create docs/guides/mcp-integration.md covering capabilities and verification.

3) README.md
   - Ensure simplified structure, quick verification, and troubleshooting are present and current.

## Key Information
- MCP servers: 8081 (memory), 8082 (filesystem), 8084 (git)
- Weaviate readiness: 8080 (.well-known/ready)
- Sophia dev shell: `agent-dev` container
- Sophia: Separate repo; optional integration via SOPHIA_PATH (legacy ARTEMIS_PATH works); HTTP bridge planned.

## Open Questions
1) Remote Sophia bridge
   - Implement `SOPHIA_URL` HTTP client for remote sidecar, or continue local-only integration?
2) MCP endpoint contracts
   - Standardize request/response payloads and add simple examples where appropriate.
