# 🔐 USER TOKEN SETUP - MAXIMUM ACCESS (60 seconds)

🚨 IMPORTANT: User token gives Sophia YOUR complete Slack permissions!
Sophia will act as YOUR user account in all interactions.

## STEP 1: Get Your User Token (30 seconds)

METHOD A - Legacy Token (Easiest):

1. Go to: <https://api.slack.com/legacy/custom-integrations/legacy-tokens>
2. Find "Pay Ready" workspace
3. Click "Create token"
4. Copy token (starts with xoxp-)

METHOD B - OAuth App (More Secure):

1. Go to: <https://api.slack.com/apps/new>
2. Create app → "From scratch"
3. App Name: "Personal Sophia Access"
4. Workspace: Pay Ready
5. OAuth & Permissions → User Token Scopes:
   ✅ channels:read ✅ channels:write
   ✅ groups:read ✅ groups:write  
   ✅ im:read ✅ im:write
   ✅ mpim:read ✅ mpim:write
   ✅ users:read ✅ files:read
   ✅ files:write ✅ chat:write
   ✅ channels:manage ✅ groups:manage
   ✅ admin (if you want admin access)

## STEP 2: Update Configuration (10 seconds)

Replace "REPLACE_WITH_YOUR_USER_TOKEN" with your actual token

## STEP 3: Test Access (20 seconds)

python3 scripts/test_user_token.py

## STEP 4: Deploy

Sophia now has YOUR complete Slack access!

# ⚠️ SECURITY CONSIDERATIONS

✅ PROS:
• Maximum possible access - everything you can do
• No channel invitation needed
• Admin capabilities (if you're admin)
• Can create channels, manage users
• Complete workspace control

⚠️ RISKS:
• Messages appear from YOUR account
• Audit trail shows YOUR name
• If token compromised = full account access  
• Sophia actions attributed to YOU

# 🎯 PERFECT FOR

• Personal AI assistant
• Complete workspace automation  
• When you want Sophia to have unlimited power
• Internal/private workspace usage
