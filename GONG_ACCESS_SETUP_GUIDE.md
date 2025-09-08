# 🔐 Gong Integration Access Setup Guide

## Current Access Status

✅ **What's Working:**

- Basic API connection (authentication successful)
- Call metadata (titles, dates, participants, duration)
- User list access
- Call listing and filtering

❌ **What's Not Accessible:**

- Call transcripts (404 errors)
- Call recordings
- Email content
- Detailed analytics

## 🎯 How to Grant Full Access to Gong Integration

### Option 1: Enable Through Gong Admin Portal (Recommended)

1. **Log into Gong as an Admin**

   - Go to <https://app.gong.io>
   - Click on your profile → Company Settings

2. **Navigate to API Settings**

   ```
   Company Settings → Integrations → API
   ```

3. **Check/Enable These Permissions for Your API Key**

   Your current API key: `TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N`

   Required scopes (may need to regenerate key with these):

   - ☐ `api:calls:read` - Read call metadata
   - ☐ `api:calls:transcript:read` - **Read call transcripts** ⚠️ MISSING
   - ☐ `api:calls:media:read` - Access call recordings
   - ☐ `api:calls:statistics:read` - Call analytics
   - ☐ `api:emails:read` - Email content
   - ☐ `api:users:read` - User information
   - ☐ `api:library:read` - Content library
   - ☐ `api:stats:read` - Statistics and analytics

4. **Enable Transcript Processing**

   ```
   Settings → Call Recording → Transcription Settings
   ```

   Ensure these are ON:

   - ☐ Automatic transcription for all calls
   - ☐ API access to transcripts
   - ☐ Include speaker separation
   - ☐ Process historical calls

5. **Set Data Retention**

   ```
   Settings → Data Management → API Access
   ```

   - ☐ Enable API access to historical data
   - ☐ Set retention period (recommend 365 days)

### Option 2: Create New API Integration

If current key has limited scope, create a new one:

1. **Create New Integration**

   ```
   Company Settings → Integrations → API → Create New Integration
   ```

2. **Configure Integration**

   - Name: `Sophia AI Full Access`
   - Type: `Server-to-Server`
   - Scopes: Select ALL read permissions
   - IP Restrictions: None (or add your server IPs)

3. **Generate New Credentials**
   - You'll get new Access Key and Secret
   - Update `.env.gong_pipeline` with new credentials

### Option 3: Request Via Gong Support

If you don't see these options:

1. **Contact Gong Support**

   ```
   Email: support@gong.io
   Subject: Enable API Transcript Access

   Message:
   We need to enable transcript API access for our integration.
   Account: Pay Ready
   API Key ID: [Your key ID]
   Required: Transcript read access via API
   Use case: AI-powered sales intelligence system
   ```

2. **They will enable:**
   - Transcript API endpoint access
   - Historical data processing
   - Increased rate limits if needed

## 🔍 Verify Access After Changes

Run this test to confirm transcript access:

```python
#!/usr/bin/env python3
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv('.env.gong_pipeline')

# Test transcript access
auth = HTTPBasicAuth(
    os.getenv("GONG_ACCESS_KEY"),
    os.getenv("GONG_ACCESS_SECRET")
)

# Get a call
calls_response = requests.get(
    "https://us-70092.api.gong.io/v2/calls",
    auth=auth,
    params={"limit": 1}
)

if calls_response.status_code == 200:
    calls = calls_response.json().get("calls", [])
    if calls:
        call_id = calls[0]["id"]

        # Try to get transcript
        transcript_response = requests.get(
            f"https://us-70092.api.gong.io/v2/calls/{call_id}/transcript",
            auth=auth
        )

        if transcript_response.status_code == 200:
            print("✅ TRANSCRIPT ACCESS GRANTED!")
            print(f"   Call: {calls[0].get('title')}")
            transcript = transcript_response.json().get("transcript", [])
            print(f"   Segments: {len(transcript)}")
        else:
            print(f"❌ No transcript access: {transcript_response.status_code}")
            print("   Follow the setup guide above")
```

## 📊 What Happens After Access is Granted

Once transcripts are accessible, Sophia will automatically:

1. **Ingest All Call Data**

   - Fetch transcripts for all 100+ calls
   - Chunk conversations by speaker (700 tokens)
   - Create semantic embeddings
   - Store in Weaviate for instant search

2. **Enable Natural Language Queries**

   ```python
   # You'll be able to ask:
   "What pricing objections came up with Cushman?"
   "Show me all discussions about Yardi integration"
   "Which clients mentioned competitors?"
   ```

3. **Generate Deep Insights**

   - Sentiment analysis per account
   - Common objection patterns
   - Successful talk tracks
   - Deal velocity metrics

4. **Automated Intelligence**
   - Daily briefs on key accounts
   - Alert on negative sentiment
   - Track commitment follow-through
   - Identify coaching opportunities

## 🚨 Common Issues & Solutions

### Issue: "404 Not Found" for transcripts

**Solution**: Transcripts not enabled in Gong settings or call not yet processed

### Issue: "403 Forbidden"

**Solution**: API key lacks transcript read scope - regenerate with correct permissions

### Issue: "429 Rate Limited"

**Solution**: Default is 10 requests/second - request increase from Gong support

### Issue: Empty transcript arrays

**Solution**: Calls may be too recent (processing takes 30-60 minutes after call ends)

## 📞 Gong Support Contacts

- **Support Email**: <support@gong.io>
- **API Documentation**: <https://gong.io/api>
- **Admin Portal**: <https://app.gong.io/company/api-management>
- **Rate Limit Increase Form**: <https://gong.io/api-limits>

## ✅ Success Checklist

After setup, verify you have:

- [ ] Transcript API endpoint returns 200 status
- [ ] Can retrieve speaker-separated text
- [ ] Historical calls have transcripts available
- [ ] Rate limits sufficient for your volume
- [ ] Webhooks configured for real-time updates (optional)

---

**Note**: Transcript access is typically included in Gong Enterprise plans. If you're on a different plan, you may need to contact your account manager to enable API transcript access.
