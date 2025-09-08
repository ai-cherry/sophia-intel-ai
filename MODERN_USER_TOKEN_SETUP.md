# 🔐 Modern User Token Setup - Complete Slack Access

## 🚨 Legacy Tokens Deprecated - Use This Modern Method Instead

### **Method 1: OAuth App with User Scopes (3 minutes)**

#### **Step 1: Create OAuth App**

1. Go to: <https://api.slack.com/apps/new>
2. **Create app** → "From scratch"
3. **App Name**: `Sophia Personal Access`
4. **Workspace**: `Pay Ready`
5. Click **Create App**

#### **Step 2: Configure User Token Scopes**

Go to **OAuth & Permissions** → **User Token Scopes** and add:

**Essential Scopes for Complete Access:**

```
channels:read      - Read all public channels
channels:write     - Write to all public channels
channels:manage    - Create/manage channels
groups:read        - Read private channels
groups:write       - Write to private channels
groups:manage      - Manage private channels
im:read           - Read direct messages
im:write          - Send direct messages
mpim:read         - Read group DMs
mpim:write        - Send group DMs
users:read        - Read user info
files:read        - Access files
files:write       - Upload files
chat:write        - Write messages
pins:read         - Read pinned messages
pins:write        - Pin/unpin messages
reactions:read    - Read reactions
reactions:write   - Add reactions
team:read         - Read team info
```

**Optional Admin Scopes (if you're workspace admin):**

```
admin               - Full admin access
usergroups:read    - Read user groups
usergroups:write   - Manage user groups
```

#### **Step 3: Install App**

1. Click **Install to Workspace**
2. Review permissions → **Allow**
3. Copy **User OAuth Token** (starts with `xoxp-`)

#### **Step 4: Update Configuration**

```python
# In app/api/integrations_config.py:
"slack_user_token": {
    "enabled": True,  # Change to True
    "user_token": "xoxp-your-actual-token-here",  # Paste your token
    # ... rest stays the same
}
```

#### **Step 5: Test Access**

```bash
python3 test_user_token.py
```

---

### **Method 2: Workspace Admin Installation (Instant)**

If you're a **workspace admin**, you can also:

1. Go to **Slack Admin** → **Manage Apps**
2. **Browse App Directory** → Search "Workflow Builder"
3. **Install** → This gives admin-level user tokens
4. Get token from app settings

---

### **Method 3: Browser Token Extraction (Advanced)**

For developers who need immediate access:

1. Open Slack in browser
2. Open **Developer Tools** (F12)
3. Go to **Application/Storage** → **Cookies**
4. Find `d` cookie → Copy value
5. This acts as user session token

**Security Note**: Browser tokens expire and are less secure.

---

## 🎯 **What You Get with Modern User Token:**

### **Complete Access Capabilities:**

```python
✅ Read/write ALL channels (public + private)
✅ Create new channels and manage existing ones
✅ Invite/remove users from channels
✅ Upload files to any location
✅ Send direct messages to anyone
✅ Pin/unpin messages
✅ Add reactions to messages
✅ Access all workspace files
✅ Read team and user information
✅ Everything YOU can do in Slack
```

### **Business Intelligence Superpowers:**

```python
# Sophia can now automate Pay Ready BI:
sophia.read_any_channel("#executive")           # No invite needed
sophia.send_to_any_channel("#board", alert)    # Direct access
sophia.create_channel("ai-alerts", private=True) # Create dedicated channels
sophia.pin_message("#finance", important_msg)   # Highlight key insights
sophia.upload_report(["#exec", "#finance"])     # Share BI reports
```

## ⚡ **Quick Start Commands:**

### **Test Your Setup:**

```bash
# Verify token works:
python3 test_user_token.py

# Test complete access:
python3 -c "
from sophia_max_access_client import SophiaMaxAccess
sophia = SophiaMaxAccess()
print('✅ Sophia has complete access!')
"
```

### **Start Business Intelligence Automation:**

```python
from sophia_max_access_client import SophiaMaxAccess

sophia = SophiaMaxAccess()

# Send BI summary to executive team
sophia.automate_pay_ready_bi()

# Create dedicated alerts channel
sophia.create_channel("sophia-bi-alerts", private=True)

# Upload daily report
sophia.upload_file_anywhere(
    ["#finance", "#operations"],
    "daily_bi_report.pdf",
    "Daily Business Intelligence Report"
)
```

## 🔒 **Security Best Practices:**

### **Token Security:**

- Store token securely (environment variables)
- Rotate tokens periodically
- Monitor token usage in Slack audit logs
- Revoke if compromised

### **Usage Guidelines:**

- Messages will appear from YOUR account
- Actions are attributed to YOU
- Use responsibly for business automation
- Consider team communication about AI automation

## 🚀 **Ready for Production:**

Once you have your `xoxp-` user token:

1. **Update config** with your token
2. **Enable** user token integration
3. **Test** access with test script
4. **Deploy** Sophia with complete Slack access

**Total setup time: ~3 minutes for maximum Slack access!**

---

## 🆘 **Troubleshooting:**

**"Insufficient permissions" error:**

- Check you added all User Token Scopes (not Bot Token Scopes)
- Reinstall app with updated permissions

**"Token invalid" error:**

- Ensure token starts with `xoxp-` (user token)
- Verify app is installed in correct workspace

**"Channel not found" error:**

- User tokens require channel invitation for private channels
- Use `conversations_join` to join public channels

**Need help?** The modern OAuth method gives you the same complete access as legacy tokens, just more secure! 🎯
