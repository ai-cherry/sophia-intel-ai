# 🚀 SIMPLE BOT TOKEN SETUP (30 seconds)

## STEP 1: Get Bot Token (2 minutes)

1. Go to Pay Ready Slack workspace
2. Click "Apps" in sidebar
3. Search for "Bots" → Click "Add"
4. Click "Add Bot Integration"
5. Choose username: "sophia-ai"
6. Copy the token (starts with xoxb-)

## STEP 2: Update Configuration (10 seconds)

Replace "REPLACE_WITH_YOUR_BOT_TOKEN" with your actual token

## STEP 3: Invite to Channels (15 seconds)

/invite @sophia-ai

Add to these channels:
✅ #payments (master payments - 270 views)
✅ #finance (ABS history - 252 views)  
✅ #operations (batch processing - 235 views)
✅ #general (daily summaries)
✅ Any other channels you want Sophia to access

## STEP 4: Test (5 seconds)

Python test:

```python
from scripts.simple_bot_setup import test_bot_access
test_bot_access()
```

# DONE! ✅

Sophia now has complete access to:
• All public channels
• All private channels (when invited)
• Direct messages
• File sharing
• Message history
• User information

## COMPARISON

Custom App Setup: ~10 minutes + webhook maintenance
Bot Token Setup: ~30 seconds, zero maintenance

For Pay Ready's business intelligence needs, bot token gives you:
• Same complete access
• Simpler setup
• More reliable (no webhooks to break)
• Easier deployment
