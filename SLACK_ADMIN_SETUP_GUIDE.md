# Slack Integration Setup Guide for Admins

## Quick Setup: Create New Bot Token (5 minutes)

### 1. Create Slack App

1. Go to <https://api.slack.com/apps>
2. Click **"Create New App"** → **"From scratch"**
3. Name: `Sophia AI Assistant`
4. Workspace: Select your Pay Ready workspace

### 2. Configure Bot Permissions

Go to **OAuth & Permissions** and add these Bot Token Scopes:

```
channels:read      - List channels
channels:join      - Join channels
chat:write         - Send messages
chat:write.public  - Send to public channels
users:read         - Read user info
conversations:read - Access conversations
conversations:history - Read message history
```

### 3. Install App & Get Token

1. Click **"Install to Workspace"**
2. Authorize the permissions
3. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### 4. Replace in Code

Update this line in `/app/api/integrations_config.py`:

```python
"bot_token": "xoxb-YOUR-NEW-TOKEN-HERE"
```

## Option 2: Fix Current App (Alternative)

If you want to keep the existing app, the issue is the `account_inactive` error. This means:

1. **Check App Status**: Go to <https://api.slack.com/apps> → Find your app → Check if it's active
2. **Reinstall App**: Sometimes re-installing fixes activation issues
3. **Verify Workspace**: Ensure the workspace URL matches the token

## Option 3: Admin Override Token (Fastest)

As workspace admin, you can create a legacy token:

1. Go to <https://api.slack.com/legacy/custom-integrations/legacy-tokens>
2. Click **"Create token"** for your workspace
3. This gives you a `xoxp-` token with full admin permissions

⚠️ **Warning**: Legacy tokens are deprecated but work immediately.

## Test the Fix

Once you have a new token, run:

```bash
python3 test_sophia_slack_integration.py
```

The test will show ✅ instead of ❌ for Slack API calls.

## What Sophia Will Be Able to Do

With proper token, Sophia can:

- ✅ Send automated business alerts to channels
- ✅ Respond to mentions with AI insights
- ✅ Create channels for project teams
- ✅ Post daily/weekly business intelligence reports
- ✅ Alert on deal changes from HubSpot/Salesforce
- ✅ Share Gong call insights automatically

## Single Command Setup

Once you get the token, just replace it in the config and restart:

```bash
# Update bot_token in integrations_config.py
# Then restart Sophia:
pkill -f sophia_server && sleep 2 && SOPHIA_PORT=9000 python3.12 sophia_server_standalone.py
```

That's it! The integration will work immediately.
