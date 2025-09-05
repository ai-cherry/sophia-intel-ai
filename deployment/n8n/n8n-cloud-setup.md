# n8n Cloud Setup Guide for Gong Integration

## ✅ Your n8n Account Information

```yaml
Username: scoobyjava
Password: [Stored Securely]
API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8
Instance URL: https://scoobyjava.app.n8n.cloud
```

## 🚀 Quick Setup Steps

### Step 1: Access Your n8n Cloud Instance

1. **Login to n8n Cloud**:
   ```
   URL: https://app.n8n.cloud
   Username: scoobyjava
   Password: Huskers1974###
   ```

2. **Your Instance URL** (once logged in):
   ```
   https://scoobyjava.app.n8n.cloud
   ```

### Step 2: Import the Gong Webhook Workflow

1. Click **"Workflows"** in the left sidebar
2. Click **"Add Workflow"** → **"Import from File"**
3. Upload: `/deployment/n8n/gong-webhook-workflow.json`
4. Click **"Save"**

### Step 3: Configure Credentials

#### A. Gong API Credentials
1. Go to **Credentials** (left sidebar)
2. Click **"Add Credential"**
3. Search for **"Basic Auth"**
4. Configure:
   ```
   Credential Name: Gong API
   Username: TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N
   Password: eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU
   ```
5. Click **"Create"**

#### B. PostgreSQL (Neon) Credentials
1. Click **"Add Credential"**
2. Search for **"Postgres"**
3. Configure:
   ```
   Credential Name: Neon PostgreSQL
   Host: [Your Neon Host]
   Database: sophia
   User: [Your DB User]
   Password: [Your DB Password]
   SSL: Required
   Port: 5432
   ```
4. Click **"Create"**

#### C. Redis Credentials
1. Click **"Add Credential"**
2. Search for **"Redis"**
3. Configure:
   ```
   Credential Name: Redis Cache
   Host: [Your Redis Host]
   Port: 6379
   Password: [If required]
   ```
4. Click **"Create"**

#### D. Weaviate Credentials
1. Click **"Add Credential"**
2. Search for **"HTTP Header Auth"**
3. Configure:
   ```
   Credential Name: Weaviate
   Header Name: Authorization
   Header Value: Bearer [Your Weaviate API Key]
   ```
4. Click **"Create"**

### Step 4: Get Your Webhook URL

1. Open the imported workflow
2. Click on the **"Gong Webhook Trigger"** node
3. You'll see your webhook URL:
   ```
   https://scoobyjava.app.n8n.cloud/webhook/gong-webhook
   ```
4. **Copy this URL** - you'll need it for Gong configuration

### Step 5: Configure Environment Variables

1. Go to **Settings** → **Variables**
2. Add these variables:
   ```
   GONG_WEBHOOK_SECRET: [Will be provided by Gong when you create webhook]
   SOPHIA_API_URL: [Your Sophia API URL]
   SOPHIA_DASHBOARD_URL: [Your Dashboard URL]
   OPENAI_API_KEY: [Your OpenAI Key if using AI features]
   ```

### Step 6: Activate the Workflow

1. Open your Gong workflow
2. Toggle the **"Active"** switch in the top-right
3. The webhook is now listening!

## 🔗 Gong Admin Configuration

Now configure Gong to send webhooks to your n8n instance:

### In Gong Admin Panel:

1. **Navigate to**: Admin → Automation Rules
2. **Create New Rule**:
   ```yaml
   Name: n8n Cloud Webhook - Call Ended
   Event: Call Ended
   Action: Send Webhook
   URL: https://scoobyjava.app.n8n.cloud/webhook/gong-webhook
   Method: POST
   ```
3. **Copy the Webhook Secret** provided by Gong
4. **Add it to n8n Variables** (Step 5 above)

## 📊 Testing Your Setup

### Test 1: Manual Webhook Test
```bash
curl -X POST https://scoobyjava.app.n8n.cloud/webhook/gong-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "test",
    "callId": "test123",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
```

### Test 2: From Gong
1. In Gong Admin → Automation Rules
2. Find your webhook rule
3. Click **"Test"**
4. Check n8n executions

## 🔧 Advanced Configuration

### API Access from External Apps

Use your API key to programmatically manage workflows:

```python
import requests

headers = {
    "X-N8N-API-KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8",
    "Content-Type": "application/json"
}

# Get all workflows
response = requests.get(
    "https://scoobyjava.app.n8n.cloud/api/v1/workflows",
    headers=headers
)

# Execute a workflow
response = requests.post(
    "https://scoobyjava.app.n8n.cloud/api/v1/workflows/{workflow_id}/execute",
    headers=headers,
    json={"data": {"test": "value"}}
)
```

### Monitoring & Logs

1. **View Executions**: Workflows → Your Workflow → Executions
2. **Check Logs**: Each execution shows detailed logs
3. **Error Notifications**: Settings → Error Workflows

## 🎯 Your Specific Webhook URLs

Based on your n8n cloud instance, here are your webhook endpoints:

```yaml
Main Webhook: https://scoobyjava.app.n8n.cloud/webhook/gong-webhook
Test Webhook: https://scoobyjava.app.n8n.cloud/webhook-test/gong-webhook
Wait Webhook: https://scoobyjava.app.n8n.cloud/webhook-waiting/gong-webhook
```

## ✅ Next Steps

1. ✅ Login to n8n Cloud
2. ✅ Import workflow
3. ✅ Configure credentials
4. ✅ Activate workflow
5. ⏳ Configure Gong webhooks (use URL above)
6. ⏳ Test the integration
7. ⏳ Monitor executions

## 🚨 Important Security Notes

- Your API key expires: 2025-02-17 (based on timestamp 1758006000)
- Keep your webhook secret secure
- Use environment variables for sensitive data
- Enable 2FA on your n8n account

## 📞 Support

- n8n Community: https://community.n8n.io
- n8n Docs: https://docs.n8n.io
- Your Instance: https://scoobyjava.app.n8n.cloud