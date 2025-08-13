# MCP Migration Guide

This document tracks the migration of direct API clients to the Model Context Protocol (MCP) architecture.

## Migration Status

| Service    | Status          | Legacy Path                   | New MCP Path                | Completion Date |
|------------|-----------------|------------------------------|----------------------------|----------------|
| Gong       | A1 ✅ (refined) | `integrations/gong_client.py` | `libs/mcp_client/gong.py`  | Pending A2     |

## Gong Migration

### Current Status

The Gong integration has been migrated from a direct API client to an MCP server architecture.

- ✅ New MCP server: `mcp/gong/server.py`
- ✅ New MCP client: `libs/mcp_client/gong.py`
- ✅ New schemas: `schemas/gong.py`
- ✅ MCP refinements completed (A1): error standardization, consistent backoff, test coverage expansion, configurable health check

### Migration Steps

1. ✅ Create MCP server, client, and schemas (A1)
2. ✅ Apply backoff consistency, error normalization, health mode, pagination compliance (A1 refinements)
3. ⬜ Update all consumers to use the new MCP client (A2)
4. ⬜ Add temporary import shim for backward compatibility
5. ⬜ Remove legacy client once all consumers are migrated

### Consumers to Update

The following components currently use the direct Gong API client and need to be updated:

- `agents/sales_coach_agent.py` (or equivalent)
- `apps/api/routers/sales_router.py`

### Health Check Configuration

The Gong MCP health check can operate in two modes:

- `strict` (default): Returns non-200 status code when Gong API auth fails
- `degraded`: Returns 200 with `status: "degraded"` when auth fails

Set the mode via the `GONG_HEALTH_MODE` environment variable.

### Error Type Standardization

Error types have been standardized across the MCP server and client:

| Original Error Type | Standardized Type |
|---------------------|-------------------|
| `gong_api_error`    | `upstream_error`  |
| `api_error`         | `request_error`   |
| `missing_api_key`   | `missing_api_key` |

Standard types are preserved: `validation_error`, `internal_error`, etc.

### Pagination Contract

All list endpoints now guarantee the presence of pagination metadata with these fields:

```json
{
  "meta": {
    "has_more": false,
    "next_cursor": null
  }
}
```

### Deprecation Timeline

- Direct Gong API client (`integrations/gong_client.py`) will be deprecated once all consumers are migrated
- A temporary shim will be provided to maintain backward compatibility during the transition
- Full removal planned after verification of all consumers using the new MCP client
