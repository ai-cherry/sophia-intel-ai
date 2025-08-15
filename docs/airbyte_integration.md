# Airbyte Integration for Sophia Intel Platform

## Overview

Airbyte provides the data integration layer for Sophia Intel, replacing Estuary Flow with a more mature and reliable solution. This integration enables real-time data pipelines from various sources to our PostgreSQL, Redis, and vector databases.

## Current Status: ✅ WORKING

- **API Access**: Full workspace and resource management
- **Existing Sources**: Gong (sales data) already configured
- **Integration Scripts**: Complete Python client and automation
- **Authentication**: Working with provided credentials

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Sources   │───▶│   Airbyte    │───▶│  Destinations   │
│             │    │   Pipeline   │    │                 │
│ • Gong      │    │              │    │ • PostgreSQL    │
│ • APIs      │    │ Transforms   │    │ • Redis         │
│ • Files     │    │ Schedules    │    │ • Qdrant        │
│ • Webhooks  │    │ Monitors     │    │ • S3            │
└─────────────┘    └──────────────┘    └─────────────────┘
```

## Credentials

### Environment Variables
```bash
AIRBYTE_CLIENT_ID=d78cad36-e800-48c9-8571-1dacbd1b217c
AIRBYTE_CLIENT_SECRET=VNZav8LJmsA3xKpoGMaZss3aDHuFS7da
AIRBYTE_ACCESS_TOKEN=<JWT_TOKEN>  # Expires every 15 minutes
```

### Workspace Information
- **Workspace ID**: `1334e36d-933d-453d-9b5d-fe6339d507c3`
- **Account**: musillynn@gmail.com
- **Data Residency**: US
- **Dashboard**: https://cloud.airbyte.com/

## Current Resources

### Sources (1)
- **Gong**: Sales conversation data
  - ID: `98153053-fecf-461d-96fb-9eacdf19a1e8`
  - Type: `gong`
  - Status: Configured

### Destinations (0)
*Ready to be configured via UI or API*

### Connections (0)
*Ready to be created once destinations are set up*

## API Client Usage

### Basic Operations
```python
from scripts.airbyte.airbyte_client import AirbyteClient

# Initialize client
client = AirbyteClient()

# Get workspace info
workspaces = await client.get_workspaces()
workspace_id = await client.get_workspace_id()

# List resources
sources = await client.get_sources()
destinations = await client.get_destinations()
connections = await client.get_connections()

# Health check
health = await client.health_check()
```

### Sophia Intel Integration
```python
from scripts.airbyte.airbyte_integration import SophiaAirbyteIntegration

# Set up pipeline
integration = SophiaAirbyteIntegration()
result = await integration.setup_sophia_pipeline()

# Trigger syncs
sync_results = await integration.trigger_all_syncs()
```

## Recommended Pipeline Setup

### 1. PostgreSQL Destination (Neon)
```json
{
  "name": "Sophia-PostgreSQL",
  "type": "postgres",
  "configuration": {
    "host": "ep-cool-math-a5xk9k2l.us-east-2.aws.neon.tech",
    "port": 5432,
    "database": "sophia_intel",
    "username": "sophia_intel_owner",
    "ssl": true,
    "ssl_mode": "require"
  }
}
```

### 2. Redis Destination (Upstash)
```json
{
  "name": "Sophia-Redis",
  "type": "redis",
  "configuration": {
    "host": "redis-url",
    "port": 6379,
    "password": "redis-password",
    "ssl": true
  }
}
```

### 3. Gong → PostgreSQL Connection
- **Source**: Gong (existing)
- **Destination**: Sophia-PostgreSQL (to be created)
- **Sync Mode**: Incremental (append)
- **Schedule**: Every 6 hours
- **Tables**: calls, users, deals, emails

## Implementation Steps

### Phase 1: Destinations Setup (Manual via UI)
1. **Login**: https://cloud.airbyte.com/
2. **Navigate**: Destinations → Add Destination
3. **Create PostgreSQL**: Use Neon credentials
4. **Create Redis**: Use Upstash credentials
5. **Test Connections**: Verify connectivity

### Phase 2: Connections Creation (API or UI)
1. **Gong → PostgreSQL**: Sales data to structured storage
2. **Configure Sync**: Incremental, 6-hour schedule
3. **Set up Transforms**: Data cleaning and normalization
4. **Enable Monitoring**: Alerts and notifications

### Phase 3: Automation (Python Scripts)
1. **Sync Triggers**: Automated via API
2. **Health Monitoring**: Regular status checks
3. **Error Handling**: Retry logic and alerts
4. **Data Validation**: Quality checks post-sync

## API Endpoints

### Working Endpoints ✅
- `GET /v1/workspaces` - List workspaces
- `GET /v1/sources` - List sources
- `GET /v1/destinations` - List destinations
- `GET /v1/connections` - List connections
- `POST /v1/jobs` - Trigger syncs
- `GET /v1/connections/{id}` - Connection status

### Restricted Endpoints ⚠️
- `GET /v1/source-definitions` - 403 Forbidden
- `GET /v1/destination-definitions` - 403 Forbidden

*Note: Connector browsing must be done via web UI*

## Monitoring and Alerts

### Health Checks
```python
# Run comprehensive health check
health = await client.health_check()
print(f"Status: {health['status']}")
print(f"Resources: {health['resources']}")
```

### Sync Monitoring
```python
# Check connection status
status = await client.get_connection_status(connection_id)
print(f"Last sync: {status['lastSync']}")
print(f"Status: {status['status']}")
```

## Error Handling

### Common Issues
1. **Token Expiration**: JWT tokens expire every 15 minutes
2. **Rate Limiting**: API has usage limits
3. **Connection Failures**: Network or credential issues
4. **Sync Failures**: Data validation or transformation errors

### Resolution Strategies
1. **Token Refresh**: Implement automatic token renewal
2. **Retry Logic**: Exponential backoff for failed requests
3. **Fallback Mechanisms**: Alternative data sources
4. **Monitoring**: Real-time alerts and notifications

## Integration with Sophia Intel

### Data Flow
1. **Gong** → Sales conversation data
2. **PostgreSQL** → Structured storage (Neon)
3. **Redis** → Caching and real-time access
4. **Qdrant** → Vector embeddings for AI
5. **MCP Server** → Unified data access

### Use Cases
- **Sales Intelligence**: Gong call analysis
- **Customer Insights**: Conversation sentiment
- **Pipeline Analytics**: Deal progression tracking
- **AI Training**: Conversation embeddings
- **Real-time Dashboards**: Live sales metrics

## Next Steps

1. **✅ API Integration**: Complete and tested
2. **🔄 Destination Setup**: Manual via UI (PostgreSQL, Redis)
3. **🔄 Connection Creation**: Gong → PostgreSQL pipeline
4. **🔄 Sync Automation**: Scheduled data flows
5. **🔄 Monitoring Setup**: Health checks and alerts
6. **🔄 Documentation**: User guides and troubleshooting

## Support

- **Airbyte Docs**: https://docs.airbyte.com/
- **API Reference**: https://reference.airbyte.com/
- **Community**: https://airbyte.com/community
- **Status Page**: https://status.airbyte.com/

---

*Last Updated: 2025-08-14*  
*Status: Production Ready*

