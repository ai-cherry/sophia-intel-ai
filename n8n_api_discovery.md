# N8N API Discovery Results

## API Configuration
- **Authentication**: API Key via `X-N8N-API-KEY` header
- **API Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8`

## User Credentials
- **Username**: `scoobyjava`
- **Password**: `Huskers1974###`

## API Requirements
- N8N API is not available during free trial - requires upgrade
- For self-hosted instances: API available at `https://<your-instance>/api/v1/`
- For N8N Cloud: API available at `https://<your-cloud-instance>/api/v1/`

## Available Endpoints (from documentation)
- `/workflows` - List all workflows
- `/workflows/{id}` - Get specific workflow (may contain webhook URLs)
- `/executions` - List executions
- `/users` - User management

## Webhook URL Discovery
- Webhook URLs are typically embedded in workflow definitions
- Need to:
  1. Find the correct N8N instance URL
  2. Authenticate with API key
  3. Retrieve workflows that contain webhook nodes
  4. Extract webhook URLs from workflow definitions

## Next Steps
1. Determine the actual N8N instance URL (could be self-hosted or cloud)
2. Test API access with the provided key
3. Retrieve workflows to find webhook URLs
4. Configure webhook URLs in SOPHIA V4

## Example API Call Format
```bash
curl -H "X-N8N-API-KEY: <api_key>" \
     -H "Accept: application/json" \
     "https://<n8n-instance>/api/v1/workflows"
```

