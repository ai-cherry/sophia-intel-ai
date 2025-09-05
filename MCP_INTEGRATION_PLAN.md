# MCP Integration Plan: Sophia Intel AI

## Overview

This document outlines the integration strategy for the MCP (Multi-Context Platform) server with all external tools and services. The MCP server now runs on port `8003` (previously `8004`), and all endpoints have been verified to use the correct port.

## Key Changes

- **MCP Server Port**: Updated from `8004` to `8003` (all references updated)
- **Health Check Endpoint**: Now `/health` instead of `/mcp/health`
- **Bridge Configuration**: All service discovery endpoints now use `/health`

## Verification Steps

1. **MCP Server Status**:

   ```bash
   curl http://localhost:8003/health
   # Expected: {"status":"healthy","mcp_server":"running"}
   ```

2. **Tool Integration**:
   - **Roo/Cursor**: Verify `.cursor/mcp.json` points to `http://localhost:8003`
   - **Cline**: Confirm `settings.json` uses port `8003`
   - **Claude Desktop**: Check `claude.config.json` for `MCP_SERVER_URL=http://localhost:8003`

## Documentation Updates

All documentation files have been updated to reflect the new port and endpoints. Key files:

- `TESTING_MCP_CONNECTIONS.md` (updated)
- `MCP_INTEGRATION_PLAN.md` (this file)
- `SWARM_INTEGRATION_ENHANCEMENTS.md` (updated)

## Next Steps

1. Verify all tools connect to port `8003`
2. Run integration tests (`pytest tests/api/test_mcp_endpoints.py`)
3. Monitor performance metrics for MCP server endpoints
