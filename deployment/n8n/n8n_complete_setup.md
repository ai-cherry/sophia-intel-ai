# Complete n8n Cloud Setup Guide with Your Credentials

## 🔐 Your Complete Credentials

### n8n Cloud
```yaml
Username: scoobyjava
Password: Huskers1974###
API Key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzN2Y4NTVkMi05ODIwLTQ2ZmMtYjlhMS1kMjdlN2ZhMGQ3MDIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUwMjgyMjU5LCJleHAiOjE3NTgwMDYwMDB9.5uLdSTZdIwlSld3WpVGC0TVm97vvzXs3y44FNeRm3N8
Instance URL: https://scoobyjava.app.n8n.cloud
```

### Neon PostgreSQL
```yaml
Host: app-sparkling-wildflower-99699121.dpl.myneon.app
Database: sophia
Project ID: rough-union-72390895
API Token: napi_r3gsuacduzw44nqdqav1u0hr2uv4bb2if48r8627jkxo7e4b2sxn92wsgf6zlxby
Endpoint: https://app-sparkling-wildflower-99699121.dpl.myneon.app
```

### Redis
```yaml
Host: redis-15014.fcrce172.us-east-1-1.ec2.redns.redis-cloud.com
Port: 15014
User Key: S666q3cr9wmzpetc6iud02iqv26774azveodh2pfadrd7pgq8l7
Account Key: A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2
URL: redis-15014.force172.us-east-1-1.ec2.redns.redis-cloud.com:15014
```

### Gong API
```yaml
Access Key: TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N
Client Secret: eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU
```

---

## 📋 Step-by-Step Setup in n8n UI

### Step 1: Login to n8n Cloud
```
URL: https://app.n8n.cloud
Username: scoobyjava
Password: Huskers1974###
```

### Step 2: Create Credentials

#### A. Gong API Credential
1. Click **Credentials** → **Add Credential**
2. Search: **"Basic Auth"**
3. Fill in:
   ```
   Name: Gong API
   Username: TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N
   Password: eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU
   ```
4. Click **Create**

#### B. Neon PostgreSQL Credential
1. Click **Add Credential**
2. Search: **"Postgres"**
3. Fill in:
   ```
   Name: Neon PostgreSQL
   Host: app-sparkling-wildflower-99699121.dpl.myneon.app
   Database: sophia
   User: [You need to provide the Neon username]
   Password: [You need to provide the Neon password]
   Port: 5432
   SSL: Required (Enable SSL)
   ```
4. Click **Create**

#### C. Redis Credential
1. Click **Add Credential**
2. Search: **"Redis"**
3. Fill in:
   ```
   Name: Redis Cache
   Host: redis-15014.fcrce172.us-east-1-1.ec2.redns.redis-cloud.com
   Port: 15014
   Password: A4mmxx43yms087hucu51sxbau5mi9hmnz6u33k43mpauhof6rz2
   ```
4. Click **Create**

### Step 3: Create the Workflow

#### Option A: Manual Creation
1. Click **Workflows** → **Add Workflow**
2. Add **Webhook** node:
   - HTTP Method: POST
   - Path: gong-webhook
   - Response Mode: On Received
   
3. Add **Function** node:
   ```javascript
   // Parse Gong webhook
   const data = $input.first().json;
   const eventType = data.eventType;
   const callId = data.callId;
   
   console.log(`Processing ${eventType} for call ${callId}`);
   
   return {
     eventType,
     callId,
     timestamp: new Date().toISOString(),
     data: data
   };
   ```

4. Add **Postgres** node:
   - Credential: Select "Neon PostgreSQL"
   - Operation: Insert
   - Schema: gong_data
   - Table: webhook_events
   
5. Connect nodes: Webhook → Function → Postgres

#### Option B: Import via UI
1. Download the corrected workflow JSON below
2. In n8n: **Workflows** → **Import from File**
3. Select the JSON file
4. Update credentials in each node

### Step 4: Activate the Workflow
1. Open your workflow
2. Toggle **Active** switch (top right)
3. Copy the webhook URL shown

---

## 🔗 Your Webhook URLs

Once the workflow is active, your webhook URLs will be:

```
Main Webhook: https://scoobyjava.app.n8n.cloud/webhook/gong-webhook
Test Webhook: https://scoobyjava.app.n8n.cloud/webhook-test/gong-webhook
```

---

## 🚀 Testing Your Setup

### Test 1: Direct Webhook Test
```bash
curl -X POST "https://scoobyjava.app.n8n.cloud/webhook/gong-webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "eventType": "test",
    "callId": "test123",
    "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
  }'
```

### Test 2: Database Connection Test
In n8n, create a test workflow with a Postgres node:
1. Operation: Execute Query
2. Query: `SELECT 1 as test`
3. Run the workflow to test connection

### Test 3: Redis Connection Test
Create a workflow with Redis node:
1. Operation: Get
2. Key: test_key
3. Run to verify connection

---

## 🎯 Gong Admin Configuration

### In Gong Admin Panel:

1. **Navigate to**: Admin → Automation Rules → New Rule

2. **Create "Call Ended" Webhook**:
   ```yaml
   Name: n8n Cloud - Call Ended
   Event: Call Ended
   Action: Send Webhook
   URL: https://scoobyjava.app.n8n.cloud/webhook/gong-webhook
   Method: POST
   Headers:
     Content-Type: application/json
   ```

3. **Create "Transcript Ready" Webhook**:
   ```yaml
   Name: n8n Cloud - Transcript Ready  
   Event: Transcript Ready
   Action: Send Webhook
   URL: https://scoobyjava.app.n8n.cloud/webhook/gong-webhook
   Method: POST
   ```

4. **Save Webhook Secret**:
   - Gong will provide a webhook secret
   - Copy it and add to n8n Variables:
     - Settings → Variables → Add Variable
     - Name: `GONG_WEBHOOK_SECRET`
     - Value: [Paste secret from Gong]

---

## 📊 Database Setup Commands

### Create Gong Tables in Neon:
```sql
-- Connect to your Neon database
-- Host: app-sparkling-wildflower-99699121.dpl.myneon.app

CREATE SCHEMA IF NOT EXISTS gong_data;

CREATE TABLE IF NOT EXISTS gong_data.webhook_events (
    id SERIAL PRIMARY KEY,
    webhook_id VARCHAR(255) UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    call_id VARCHAR(255),
    payload JSONB NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS gong_data.calls (
    id VARCHAR(255) PRIMARY KEY,
    gong_call_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    scheduled_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_webhook_events_status ON gong_data.webhook_events(processing_status);
CREATE INDEX idx_calls_scheduled ON gong_data.calls(scheduled_at);
```

---

## ✅ Final Checklist

- [ ] Login to n8n Cloud
- [ ] Create Gong API credential (Basic Auth)
- [ ] Create Neon PostgreSQL credential
- [ ] Create Redis credential
- [ ] Create/Import workflow
- [ ] Activate workflow
- [ ] Copy webhook URL
- [ ] Configure webhooks in Gong Admin
- [ ] Save Gong webhook secret to n8n Variables
- [ ] Test webhook endpoint
- [ ] Verify database connection
- [ ] Monitor first real webhook

---

## 🆘 Troubleshooting

### Issue: Webhook returns 404
**Solution**: Ensure workflow is active and path matches exactly

### Issue: Database connection fails
**Solution**: 
- Verify SSL is enabled in Postgres credential
- Check firewall/IP whitelist in Neon dashboard
- Ensure database user has proper permissions

### Issue: Redis connection fails
**Solution**:
- Verify port 15014 is correct
- Check password matches Account Key
- Ensure Redis instance is running

### Issue: Gong webhooks not arriving
**Solution**:
- Verify webhook rule is active in Gong
- Check webhook URL is publicly accessible
- Review Gong webhook logs for errors

---

## 📞 Support Contacts

- **n8n Community**: https://community.n8n.io
- **Neon Support**: https://neon.tech/support
- **Redis Cloud**: https://redis.com/support
- **Gong Support**: support@gong.io

---

## 🔒 Security Notes

- Rotate API keys every 90 days
- Use environment variables for sensitive data
- Enable 2FA on all accounts
- Monitor webhook logs for suspicious activity
- Implement webhook signature validation

---

Your n8n instance is ready at: **https://scoobyjava.app.n8n.cloud**