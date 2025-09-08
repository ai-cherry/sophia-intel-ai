# Documentation Update Request

## Current State
- Repository consolidated from 400+ docs to a clean, enforceable structure.
- Artemis separated into sidecar repository (ai-cherry/artemis-cli).
- MCP servers running locally but previously under-documented.
- Artemis connection now via local path (ARTEMIS_PATH) with planned HTTP bridge.

## Required Updates
1) LOCAL_DEV_AND_DEPLOYMENT.md
   - Add complete startup sequence with verification (infra → MCP → dev shell).
   - Document MCP server integration and health checks.
   - Clarify Artemis connection options (local vs remote via future HTTP bridge).

2) MCP Integration Guide
   - Create docs/guides/mcp-integration.md covering capabilities and verification.

3) README.md
   - Ensure simplified structure, quick verification, and troubleshooting are present and current.

## Key Information
- MCP servers: 8081 (memory), 8082 (filesystem), 8084 (git)
- Weaviate readiness: 8080 (.well-known/ready)
- Sophia dev shell: `agent-dev` container
- Artemis: Separate repo; optional integration via ARTEMIS_PATH; HTTP bridge planned.

## Open Questions
1) Remote Artemis bridge
   - Implement `ARTEMIS_URL` HTTP client in Sophia for remote sidecar, or continue local-only integration?
2) MCP endpoint contracts
   - Standardize request/response payloads and add simple examples where appropriate.

