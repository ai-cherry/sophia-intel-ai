# Database Setup Guide for Sophia AI

## Overview
This guide helps you configure Redis Cloud and Neon PostgreSQL databases for the Sophia AI platform.

## Redis Cloud Setup

### Account Information
- Account: scoobyjava #2384302
- API Account Key: A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2
- API User Key: S2ujqhjd8evq894cdaxnli4fp667s7cn31fmah0lqqvp4foszo4

### Steps
1. Go to [Redis Cloud Console](https://cloud.redis.io/)
2. Log in with your account
3. Create a new database or use existing one:
   - Name: `sophia-ai-cache`
   - Memory: 100MB (free tier)
   - Region: Any (prefer US West for Neon compatibility)
4. Once created, get the connection details:
   - Endpoint (e.g., `redis-12345.c1.us-west1-2.gce.cloud.redislabs.com`)
   - Port (usually `12345`)
   - Password (auto-generated)
5. Construct the Redis URL:
   ```
   redis://default:PASSWORD@ENDPOINT:PORT
   ```

## Neon PostgreSQL Setup

### Account Information
- Project: sophia
- Region: AWS US West 2 (Oregon)
- API Token: napi_5rvzi31qllpu0zrlhgjwfhz9308k8y0yudw3oz23h2ix5no1yr3roin7wtp9vqu7

### Steps
1. Go to [Neon Console](https://console.neon.tech/)
2. Navigate to your "sophia" project
3. Go to "Connection Details" or "Settings"
4. Copy the connection string (should look like):
   ```
   postgresql://username:password@ep-endpoint.us-west-2.aws.neon.tech/sophia?sslmode=require
   ```

## Configuration

### Environment Files
Update these files with your actual database URLs:
- `.env`
- `infra/.env.remediation`
- `.env.remediation`

Add or update these lines:
```bash
REDIS_URL=redis://default:YOUR_PASSWORD@YOUR_ENDPOINT:YOUR_PORT
DATABASE_URL=postgresql://username:password@ep-endpoint.us-west-2.aws.neon.tech/sophia?sslmode=require
```

### Testing
After configuration, test the connections:
```bash
python3 scripts/test_database_connections.py
```

## Troubleshooting

### Redis Issues
- Verify endpoint and port are correct
- Check password (no spaces or special characters issues)
- Ensure firewall allows connections
- Try `rediss://` for SSL connections if needed

### PostgreSQL Issues
- Verify the connection string format
- Check that `sslmode=require` is included
- Ensure the database name is correct
- Verify username and password

### Common Errors
- `Connection refused`: Check endpoint and port
- `Authentication failed`: Verify credentials
- `SSL required`: Add `sslmode=require` for PostgreSQL

## Security Notes
- Never commit actual credentials to git
- Use environment variables for all sensitive data
- Consider using GitHub Secrets for production deployment
- Rotate credentials periodically

## Next Steps
1. Configure actual database URLs
2. Test connections with the test script
3. Update Pulumi configuration to use these databases
4. Deploy and verify in production environment
