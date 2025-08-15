# Estuary Flow Integration

## Current Status: BLOCKED - DNS Resolution Failure

### Issue Summary
Estuary Flow integration is currently blocked due to DNS resolution failure for the API endpoint.

### Evidence
```bash
# DNS Resolution Test
nslookup api.estuary.dev
# Output: ** server can't find api.estuary.dev: NXDOMAIN

# API Connection Test  
python scripts/estuary/estuary_check.py
# Output: ConnectError('[Errno -2] Name or service not known')
```

### Technical Details
- **API Base URL**: `https://api.estuary.dev`
- **DNS Status**: NXDOMAIN (domain does not exist)
- **Token Format**: Valid JWT (1129 characters)
- **Refresh Token**: Present and valid format

### Credentials Available
- ✅ **ESTUARY_ACCESS_TOKEN**: JWT format, 1129 characters
- ✅ **ESTUARY_REFRESH_TOKEN**: Base64 encoded, valid format
- ❌ **API Endpoint**: DNS resolution fails

### Root Cause Analysis
The domain `api.estuary.dev` does not resolve to any IP address, indicating either:
1. **Service Discontinued**: Estuary Flow service may have been discontinued
2. **Domain Changed**: API endpoint may have moved to different domain
3. **Network Restrictions**: Sandbox environment may have DNS restrictions
4. **Temporary Outage**: DNS servers may be temporarily unavailable

### Attempted Solutions
1. **Multiple DNS Servers**: Tested with default DNS (8.8.8.8)
2. **Network Tools**: Installed dnsutils and iputils-ping
3. **Alternative Endpoints**: No alternative endpoints documented
4. **Token Validation**: Tokens appear valid but cannot be tested due to DNS failure

### Next Steps
1. **Verify Service Status**: Check if Estuary Flow is still operational
2. **Alternative Endpoints**: Research current API endpoints for Estuary
3. **Contact Support**: Reach out to Estuary team for current API documentation
4. **Alternative Solutions**: Consider alternative data streaming platforms

### Implementation Status
- ✅ **Integration Scripts**: Complete and ready for testing
- ✅ **Authentication**: JWT tokens available and properly formatted
- ✅ **Error Handling**: Comprehensive error capture and logging
- ❌ **Connectivity**: Blocked by DNS resolution failure

### Files Created
- `scripts/estuary/estuary_check.py`: Complete integration test script
- `config/estuary/`: Directory structure ready for flow configurations
- `docs/estuary_flow_integration.md`: This documentation

### Recommendation
**DEFER ESTUARY INTEGRATION** until DNS/connectivity issues are resolved. Focus on other integrations (OpenRouter, Qdrant, Neon, Redis) that are accessible.

---

**Last Updated**: August 14, 2025  
**Status**: BLOCKED - DNS Resolution Failure  
**Next Review**: After service status verification

---

## Original Integration Plan

This document describes the Estuary Flow integration for the Sophia Intel platform, providing real-time data streaming and ETL capabilities.

## Overview

Estuary Flow is integrated into the Sophia Intel platform to provide:

- **Real-time data capture** from various sources
- **Stream processing** and transformation
- **Data materialization** to multiple targets
- **Schema evolution** and data quality management

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Estuary Flow   │───▶│   Data Targets  │
│                 │    │   (Captures)    │    │ (Materializations)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ • HTTP APIs     │    │ • Collections   │    │ • PostgreSQL    │
│ • File Systems  │    │ • Transformations│    │ • Redis         │
│ • Prometheus    │    │ • Schema Mgmt   │    │ • S3 Archive    │
│ • Agent Logs    │    │ • Real-time     │    │ • Dashboards    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Configuration

### Environment Variables

The following environment variables must be set for Estuary Flow integration:

```bash
# Estuary Authentication
ESTUARY_JWT_TOKEN=eyJhbGciOiJIUzI1NiIs...
ESTUARY_REFRESH_TOKEN=eyJpZCI6IjEyOjExOjc0...

# Database Connections (for materializations)
POSTGRES_HOST=localhost
POSTGRES_USER=sophia
POSTGRES_PASSWORD=your_postgres_password
REDIS_HOST=localhost
REDIS_PASSWORD=your_redis_password

# AWS S3 (for archival materialization)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### Configuration Files

- **Main Config**: `config/estuary/estuary_flow.json`
- **Python Client**: `config/estuary/estuary_config.py`
- **Test Script**: `scripts/test_estuary_integration.py`

## Data Flows

### 1. Sophia AI Data Capture

**Source**: Sophia AI Platform API  
**Target**: `sophia/sophia_raw_data` collection  
**Frequency**: Every 5 minutes  

Captures:
- Agent interactions
- User queries and responses
- Performance metrics
- System events

### 2. Agent Logs Capture

**Source**: File system (`/var/log/sophia/agents/`)  
**Target**: `sophia/sophia_agent_logs` collection  
**Frequency**: Every 1 minute  

Captures:
- Agent execution logs
- Error messages
- Debug information
- Performance traces

### 3. Metrics Capture

**Source**: Prometheus metrics endpoint  
**Target**: `sophia/sophia_metrics` collection  
**Frequency**: Every 30 seconds  

Captures:
- System performance metrics
- Resource utilization
- API response times
- Error rates

## Materializations

### 1. PostgreSQL Materialization

**Target**: PostgreSQL database  
**Schema**: `estuary`  
**Tables**: 
- `sophia_processed_data`
- `sophia_agent_logs`
- `sophia_metrics`

Used for:
- Structured data storage
- Complex queries and analytics
- Data integrity and ACID compliance

### 2. Redis Materialization

**Target**: Redis cache  
**Database**: 0  

Used for:
- Real-time data access
- Caching frequently accessed data
- Session storage
- Rate limiting

### 3. S3 Archival Materialization

**Target**: AWS S3  
**Bucket**: `sophia-intel-data`  
**Prefix**: `estuary/`  

Used for:
- Long-term data archival
- Compliance and audit trails
- Data lake storage
- Backup and disaster recovery

## Data Schemas

### Raw Data Collection

```json
{
  "type": "object",
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "source": {
      "type": "string"
    },
    "data": {
      "type": "object"
    },
    "metadata": {
      "type": "object"
    }
  },
  "required": ["timestamp", "source", "data"]
}
```

### Processed Data Collection

```json
{
  "type": "object",
  "properties": {
    "id": {
      "type": "string"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "source": {
      "type": "string"
    },
    "processed_data": {
      "type": "object"
    },
    "enrichments": {
      "type": "object"
    },
    "confidence_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    }
  },
  "required": ["id", "timestamp", "source", "processed_data"]
}
```

## Transformations

### Data Enrichment

**SQL Transformation**:
```sql
SELECT 
  *,
  CURRENT_TIMESTAMP as processed_at,
  CASE 
    WHEN data->>'type' = 'agent_interaction' THEN 'high'
    WHEN data->>'type' = 'system_metric' THEN 'medium'
    ELSE 'low'
  END as priority
FROM sophia_raw_data 
WHERE data IS NOT NULL
```

## API Usage

### Python Client

```python
from config.estuary.estuary_config import EstuaryClient

async def main():
    async with EstuaryClient() as client:
        # Health check
        health = await client.health_check()
        print(f"Status: {health['status']}")
        
        # List collections
        collections = await client.list_collections()
        print(f"Collections: {collections['count']}")
        
        # Create capture
        result = await client.create_capture(
            "my_capture",
            {"endpoint": "https://api.example.com/data"}
        )
        print(f"Capture created: {result['success']}")
```

### Testing

Run the integration test suite:

```bash
python scripts/test_estuary_integration.py
```

Expected output:
```
🚀 Estuary Flow Integration Test Suite
==================================================
🔐 Testing Estuary Flow Authentication...
✅ Authentication successful!
   User: musillynn@gmail.com
   Status: healthy

📋 Testing Estuary Flow Collections...
✅ Collections retrieved successfully!
   Count: 3

🎉 Estuary Flow integration is functional!
```

## Deployment

### 1. Set Environment Variables

Add to your `.env` file or deployment environment:

```bash
ESTUARY_JWT_TOKEN=your_jwt_token_here
ESTUARY_REFRESH_TOKEN=your_refresh_token_here
```

### 2. Initialize Captures and Materializations

```bash
# Run setup script
python -c "
import asyncio
from config.estuary.estuary_config import setup_sophia_estuary_flow
asyncio.run(setup_sophia_estuary_flow())
"
```

### 3. Verify Integration

```bash
# Test the integration
python scripts/test_estuary_integration.py

# Check logs
tail -f /var/log/sophia/estuary.log
```

## Monitoring

### Health Checks

The Estuary integration provides health check endpoints:

- **Authentication Status**: Validates JWT token
- **API Connectivity**: Tests Estuary API endpoints
- **Collection Status**: Monitors data flow
- **Materialization Health**: Checks target systems

### Metrics

Key metrics to monitor:

- **Capture Lag**: Time between data generation and capture
- **Processing Rate**: Records processed per second
- **Error Rate**: Failed operations percentage
- **Storage Growth**: Data volume trends

### Alerts

Set up alerts for:

- Authentication failures
- Capture failures
- Materialization errors
- High processing lag
- Storage quota exceeded

## Troubleshooting

### Common Issues

**1. Authentication Errors**
```bash
# Check token expiry
python -c "
import jwt
token = 'your_jwt_token'
decoded = jwt.decode(token, options={'verify_signature': False})
print(f'Expires: {decoded.get(\"exp\")}')
"

# Refresh token if needed
# (Implementation depends on Estuary's refresh mechanism)
```

**2. Capture Failures**
```bash
# Check capture status
python -c "
import asyncio
from config.estuary.estuary_config import EstuaryClient

async def check():
    async with EstuaryClient() as client:
        status = await client.get_capture_status('sophia_ai_data')
        print(status)

asyncio.run(check())
"
```

**3. Materialization Issues**
- Verify target database connectivity
- Check schema permissions
- Monitor storage capacity
- Review error logs

### Log Analysis

```bash
# View Estuary logs
grep "estuary" /var/log/sophia/*.log

# Check specific capture
grep "sophia_ai_data" /var/log/sophia/estuary.log

# Monitor real-time
tail -f /var/log/sophia/estuary.log | grep ERROR
```

## Security

### Token Management

- JWT tokens expire after 14 days
- Refresh tokens should be rotated regularly
- Store tokens in secure environment variables
- Never commit tokens to version control

### Data Privacy

- All data is encrypted in transit (HTTPS)
- Sensitive data should be masked or encrypted
- Access controls are enforced at the collection level
- Audit logs track all data access

### Network Security

- API endpoints use TLS 1.2+
- IP whitelisting can be configured
- VPC peering for private connectivity
- Network monitoring and intrusion detection

## Performance Optimization

### Capture Optimization

- Adjust capture intervals based on data velocity
- Use incremental sync modes when possible
- Implement data deduplication
- Monitor capture lag and adjust resources

### Materialization Optimization

- Use appropriate indexes on target tables
- Implement data partitioning for large datasets
- Configure connection pooling
- Monitor target system performance

### Cost Optimization

- Archive old data to cheaper storage
- Use compression for large datasets
- Implement data retention policies
- Monitor usage and optimize resource allocation

## References

- [Estuary Flow Documentation](https://docs.estuary.dev/)
- [Estuary Flow API Reference](https://docs.estuary.dev/reference/)
- [Sophia Intel Platform Documentation](../README.md)
- [Configuration Management](./dependency_management.md)

