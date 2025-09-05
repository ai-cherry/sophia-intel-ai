# 🚀 Airtable Setup Guide for Sophia Intelligence

## ⏱️ Total Setup Time: 5-10 minutes

---

## 📋 STEP 1: Create Airtable Account (1 minute)

1. Go to **[airtable.com/signup](https://airtable.com/signup)**
2. Sign up with your email (or use Google/Apple SSO)
3. Verify your email if needed
4. **You get FREE**:
   - Unlimited bases
   - 1,200 records per base
   - 2GB attachments per base
   - Unlimited API calls

---

## 🔑 STEP 2: Get Your API Key (1 minute)

### Option A: Personal Access Token (Recommended - New Method)

1. Go to **[airtable.com/create/tokens](https://airtable.com/create/tokens)**
2. Click **"Create new token"**
3. Name it: `Sophia Intelligence API`
4. Add these scopes:
   - ✅ `data.records:read`
   - ✅ `data.records:write`
   - ✅ `data.recordComments:read`
   - ✅ `data.recordComments:write`
   - ✅ `schema.bases:read`
   - ✅ `schema.bases:write`
5. Click **"Create token"**
6. **COPY THE TOKEN** (you won't see it again!)

### Option B: Legacy API Key (Simpler)

1. Go to **[airtable.com/account](https://airtable.com/account)**
2. Scroll to **"API"** section
3. Click **"Generate API key"**
4. Copy your key (starts with `key...`)

---

## 🏗️ STEP 3: Create Your Base (2 minutes)

1. Go to **[airtable.com/workspace](https://airtable.com/workspace)**
2. Click **"Start from scratch"**
3. Name it: **"Sophia Intelligence Hub"**
4. You'll land in the base - note the URL:

   ```
   https://airtable.com/appXXXXXXXXXXXXXX/...
                        ↑ This is your BASE_ID
   ```

5. **Copy your BASE_ID** (starts with `app...`)

---

## 📊 STEP 4: Create Tables (3 minutes)

### Table 1: Knowledge Base

1. Rename "Table 1" to **"Knowledge Base"**
2. Add these fields (click **"+"** to add):

| Field Name    | Field Type             | Options                                         |
| ------------- | ---------------------- | ----------------------------------------------- |
| Name          | Single line text       | (default)                                       |
| Type          | Single select          | Document, Person, Company, Project, Insight     |
| Category      | Single select          | Strategy, Operations, Sales, Marketing, Finance |
| Priority      | Rating                 | Max: 5 stars                                    |
| Tags          | Multiple select        | (add as needed)                                 |
| Summary       | Long text              | Enable rich text                                |
| AI Analysis   | Long text              | Enable rich text                                |
| Confidence    | Percent                | Show as percentage                              |
| Last Updated  | Last modified time     | Include time                                    |
| Attachments   | Attachment             | Allow multiple                                  |
| Related Items | Link to another record | Link to: Knowledge Base                         |

### Table 2: Insights

1. Click **"Add or import"** → **"Create empty table"**
2. Name it: **"Insights"**
3. Add these fields:

| Field Name     | Field Type             | Options                           |
| -------------- | ---------------------- | --------------------------------- |
| Insight        | Single line text       | (default)                         |
| Generated      | Created time           | Include time                      |
| Category       | Single select          | Opportunity, Risk, Trend, Anomaly |
| Impact         | Single select          | Critical, High, Medium, Low       |
| Confidence     | Percent                | Show as percentage                |
| Source         | Link to another record | Link to: Knowledge Base           |
| Recommendation | Long text              | Enable rich text                  |
| Status         | Single select          | New, Reviewed, Actioned           |
| Owner          | User                   | Allow multiple                    |

### Table 3: Conversations

1. Add another table: **"Conversations"**
2. Add these fields:

| Field Name       | Field Type             | Options                     |
| ---------------- | ---------------------- | --------------------------- |
| Title            | Single line text       | (default)                   |
| Date             | Date                   | Include time                |
| Participants     | Multiple select        | (add names)                 |
| Type             | Single select          | Meeting, Call, Email, Slack |
| Summary          | Long text              | Enable rich text            |
| Key Points       | Long text              | Enable rich text            |
| Action Items     | Long text              | Enable rich text            |
| Sentiment        | Single select          | Positive, Neutral, Negative |
| Recording        | URL                    | (optional)                  |
| Related Insights | Link to another record | Link to: Insights           |

---

## 🔗 STEP 5: Get Table IDs (1 minute)

1. In your base, go to **"Help"** menu (top right)
2. Select **"API documentation"**
3. You'll see your table IDs:
   - Knowledge Base: `tblXXXXXXXXXXXXXX`
   - Insights: `tblYYYYYYYYYYYYYY`
   - Conversations: `tblZZZZZZZZZZZZZZ`
4. **Copy these IDs**

---

## ⚙️ STEP 6: Update Sophia Configuration (1 minute)

Add this to your `integrations_config.py`:

```python
"airtable": {
    "enabled": True,
    "status": "connected",
    "api_key": "YOUR_API_KEY_HERE",  # From Step 2
    "base_id": "appXXXXXXXXXXXXXX",  # From Step 3
    "tables": {
        "knowledge": "tblXXXXXXXXXXXXXX",  # From Step 5
        "insights": "tblYYYYYYYYYYYYYY",   # From Step 5
        "conversations": "tblZZZZZZZZZZZZZZ" # From Step 5
    },
    "webhook_url": None,  # Optional: add later
    "stats": {"records": 0, "api_calls": "unlimited"}
}
```

---

## 🧪 STEP 7: Test the Connection (1 minute)

Run this Python code to test:

```python
# Install the SDK first
pip install pyairtable

# Test connection
from pyairtable import Api

api = Api('YOUR_API_KEY')
base = api.base('YOUR_BASE_ID')
table = base.table('Knowledge Base')

# Create a test record
test_record = table.create({
    'Name': 'Test Document',
    'Type': 'Document',
    'Priority': 5,
    'Summary': 'Testing Sophia integration',
    'Confidence': 0.95
})

print(f"✅ Success! Created record: {test_record['id']}")

# List all records
all_records = table.all()
print(f"📊 Total records: {len(all_records)}")
```

---

## 🎯 STEP 8: Enable Automations (Optional - 2 minutes)

1. In your base, click **"Automations"** (lightning bolt icon)
2. Click **"Create automation"**
3. Popular automations for Sophia:

### Automation 1: New Record Alert

- **Trigger**: When record created in Knowledge Base
- **Action**: Send webhook to Sophia endpoint

### Automation 2: High Priority Alert

- **Trigger**: When Priority = 5 in Knowledge Base
- **Action**: Send email/Slack notification

### Automation 3: Weekly Summary

- **Trigger**: Every Monday at 9am
- **Action**: Find records created last week → Send summary

---

## 🚀 QUICK START COMMANDS

```bash
# 1. Install Python SDK
pip install pyairtable

# 2. Set environment variables
export AIRTABLE_API_KEY="your_key"
export AIRTABLE_BASE_ID="your_base_id"

# 3. Test with Python
python3 -c "
from pyairtable import Api
api = Api('$AIRTABLE_API_KEY')
base = api.base('$AIRTABLE_BASE_ID')
print('✅ Connected to Airtable!')
"
```

---

## 📱 BONUS: Mobile & Integrations

### Mobile Access

1. Download **Airtable app** (iOS/Android)
2. Sign in with same account
3. Full access to your bases on mobile!

### Integrations

1. **Zapier**: Connect to 5000+ apps
2. **Make/Integromat**: Advanced workflows
3. **Slack**: Get notifications
4. **Gmail**: Auto-create records from emails

---

## ✅ VERIFICATION CHECKLIST

- [ ] Account created at airtable.com
- [ ] API key/token obtained
- [ ] Base created: "Sophia Intelligence Hub"
- [ ] Base ID copied (starts with `app`)
- [ ] 3 tables created (Knowledge, Insights, Conversations)
- [ ] Table IDs copied (start with `tbl`)
- [ ] Configuration added to `integrations_config.py`
- [ ] Test record created successfully
- [ ] (Optional) Automations configured

---

## 🎉 DONE! What Sophia Can Now Do

✅ **Create** records programmatically
✅ **Read** all data with filters and formulas
✅ **Update** records with AI analysis
✅ **Delete** outdated information
✅ **Upload** files and attachments
✅ **Search** with complex queries
✅ **Batch** operations (10 records at once)
✅ **Real-time** webhooks (with automations)
✅ **Link** records to show relationships
✅ **Track** changes with revision history

---

## 💡 Pro Tips

1. **Use Views**: Create filtered views for different perspectives
2. **Color Coding**: Use colors in select fields for visual organization
3. **Formulas**: Add calculated fields for insights
4. **Grouping**: Group records by category/status
5. **Interfaces**: Build custom UIs with Interface Designer (paid feature)

---

## 🆘 Troubleshooting

**"Invalid API Key"**

- Make sure you copied the full key
- Try regenerating a new key

**"Base not found"**

- Verify base ID starts with `app`
- Check you have access to the base

**"Table not found"**

- Verify table ID starts with `tbl`
- Check exact table name in API docs

**Rate Limits**

- Free tier: 5 requests/second
- Implement 200ms delay between calls

---

**Need help? Check [airtable.com/api](https://airtable.com/api) for full API documentation!**
