# Environment Variable Separation Strategy

## Overview
Clear separation of environment variables between Sophia Intel AI (business services) and Artemis CLI (AI coding agents) with MCP servers providing the bridge.

## Environment Structure

### Sophia Intel AI (.env)
```bash
# ===== BUSINESS SERVICE API KEYS (SOPHIA ONLY) =====
APOLLO_API_KEY=sophia_apollo_key_here
SLACK_BOT_TOKEN=sophia_slack_token_here  
SLACK_APP_TOKEN=sophia_slack_app_token_here
SALESFORCE_CLIENT_ID=sophia_sf_client_id_here
SALESFORCE_CLIENT_SECRET=sophia_sf_secret_here
AIRTABLE_API_KEY=sophia_airtable_key_here
ASANA_ACCESS_TOKEN=sophia_asana_token_here
LINEAR_API_KEY=sophia_linear_key_here
HUBSPOT_API_KEY=sophia_hubspot_key_here
LOOKER_CLIENT_ID=sophia_looker_client_here
LOOKER_CLIENT_SECRET=sophia_looker_secret_here
NETSUITE_CONSUMER_KEY=sophia_netsuite_key_here
NETSUITE_CONSUMER_SECRET=sophia_netsuite_secret_here

# ===== SOPHIA INFRASTRUCTURE =====
SOPHIA_DATABASE_URL=postgresql://sophia_user:pass@localhost:5432/sophia_db
SOPHIA_REDIS_URL=redis://localhost:6380/0
SOPHIA_WEAVIATE_URL=http://localhost:8080
SOPHIA_API_PORT=8000

# ===== MCP BRIDGE SETTINGS =====
MCP_BRIDGE_HOST=localhost
MCP_BRIDGE_PORT=8050
MCP_SHARED_SECRET=shared_mcp_secret_here
```

### Artemis CLI (~/.artemis/.env)
```bash
# ===== AI MODEL API KEYS (ARTEMIS ONLY) =====
ANTHROPIC_API_KEY=artemis_anthropic_key_here
OPENAI_API_KEY=artemis_openai_key_here
OPENROUTER_API_KEY=artemis_openrouter_key_here
GROQ_API_KEY=artemis_groq_key_here
TOGETHER_API_KEY=artemis_together_key_here
PORTKEY_API_KEY=artemis_portkey_key_here
COHERE_API_KEY=artemis_cohere_key_here

# ===== ARTEMIS INFRASTRUCTURE =====
ARTEMIS_DATABASE_URL=postgresql://artemis_user:pass@localhost:5433/artemis_db
ARTEMIS_REDIS_URL=redis://localhost:6381/0
ARTEMIS_CACHE_DIR=~/.artemis/cache
ARTEMIS_MODEL_CACHE=~/.artemis/models

# ===== MCP CONNECTION TO SOPHIA =====
MCP_SOPHIA_ENDPOINT=ws://localhost:8050/sophia
MCP_BRIDGE_TOKEN=artemis_bridge_token_here
```

### MCP Bridge (.env.bridge)
```bash
# ===== MCP BRIDGE CONFIGURATION =====
BRIDGE_HOST=localhost
BRIDGE_PORT=8050
BRIDGE_SECRET=shared_mcp_secret_here

# ===== CROSS-DOMAIN SERVICES =====
SHARED_DATABASE_URL=postgresql://shared_user:pass@localhost:5434/shared_db
SHARED_REDIS_URL=redis://localhost:6379/0
SHARED_ELASTICSEARCH_URL=http://localhost:9200

# ===== SECURITY =====
JWT_SECRET=bridge_jwt_secret_here
ENCRYPTION_KEY=bridge_encryption_key_here
```

## Security Principles

1. **Domain Isolation**: No cross-domain API key sharing
2. **Principle of Least Privilege**: Each service only accesses what it needs
3. **Secure Communication**: All MCP traffic encrypted and authenticated
4. **Environment Separation**: Dev/staging/prod isolation maintained
5. **Key Rotation**: Regular rotation of all secrets and tokens

## Access Patterns

- **Sophia → Artemis**: Via MCP bridge only (no direct API key sharing)
- **Artemis → Sophia**: Via MCP bridge only (business data requests)
- **Both → Shared**: Via shared MCP servers (memory, indexing, embeddings)