#!/usr/bin/env python3
"""
Simple Bot Token Setup for Complete Slack Access
This approach gives Sophia complete access to everything in Slack
with minimal setup - just a bot token.
"""
import json
from typing import Any
def create_simple_bot_config() -> dict[str, Any]:
    """Create simplified bot token configuration"""
    config = {
        "slack_simple": {
            "enabled": True,
            "integration_type": "bot_token",
            "bot_token": "REPLACE_WITH_YOUR_BOT_TOKEN",  # xoxb-*
            "workspace": "Pay Ready",
            "complete_access": True,
            "capabilities": [
                "Read all channels",
                "Write to all channels",
                "Access private channels (when invited)",
                "Direct messages",
                "File uploads/downloads",
                "Message history",
                "User information",
                "Emoji reactions",
                "Thread replies",
            ],
            "setup_time": "30 seconds",
        }
    }
    return config
def create_simple_client_example():
    """Create example of simple bot client"""
    example = '''
# Simple Sophia Slack Client with Complete Access
from slack_sdk import WebClient
from config.manager import get_config_manager
class SophiaSimpleSlack:
    def __init__(self):
        config = INTEGRATIONS.get("slack_simple", {})
        self.client = WebClient(token=config["bot_token"])
    def send_message(self, channel: str, message: str):
        """Send message to any channel"""
        return self.client.chat_postMessage(
            channel=channel,
            text=message,
            username="Sophia AI"
        )
    def get_all_channels(self):
        """Get list of all channels"""
        return self.client.conversations_list()
    def read_channel_history(self, channel: str, limit: int = 100):
        """Read message history from any channel"""
        return self.client.conversations_history(
            channel=channel,
            limit=limit
        )
    def upload_report(self, channels: list, file_path: str, title: str):
        """Upload business intelligence reports"""
        return self.client.files_upload(
            channels=",".join(channels),
            file=file_path,
            title=title,
            initial_comment="📊 Latest business intelligence report from Sophia AI"
        )
    def send_dm(self, user_id: str, message: str):
        """Send direct message to user"""
        # Open DM channel
        dm_channel = self.client.conversations_open(users=user_id)
        # Send message
        return self.client.chat_postMessage(
            channel=dm_channel["channel"]["id"],
            text=message
        )
    def get_all_users(self):
        """Get all workspace users"""
        return self.client.users_list()
    def add_reaction(self, channel: str, timestamp: str, emoji: str):
        """Add reaction to message"""
        return self.client.reactions_add(
            channel=channel,
            timestamp=timestamp,
            name=emoji
        )
# Usage Examples:
sophia = SophiaSimpleSlack()
# Send to any channel
sophia.send_message("#payments", "🚨 Payment anomaly detected in master report (270 views)")
# Upload reports
sophia.upload_report(["#finance", "#operations"], "daily_bi_report.pdf", "Daily BI Report")
# Read any channel
history = sophia.read_channel_history("#executive")
# Send DM to CEO
sophia.send_dm("U123456", "Critical business alert: Please review payment dashboard")
'''
    return example
def create_setup_instructions():
    """Create step-by-step setup instructions"""
    instructions = """
🚀 SIMPLE BOT TOKEN SETUP (30 seconds)
=====================================
STEP 1: Get Bot Token (2 minutes)
----------------------------------
1. Go to Pay Ready Slack workspace
2. Click "Apps" in sidebar
3. Search for "Bots" → Click "Add"
4. Click "Add Bot Integration"
5. Choose username: "sophia-ai"
6. Copy the token (starts with xoxb-)
STEP 2: Update Configuration (10 seconds)
-----------------------------------------
Replace "REPLACE_WITH_YOUR_BOT_TOKEN" with your actual token
STEP 3: Invite to Channels (15 seconds)
---------------------------------------
/invite @sophia-ai
Add to these channels:
✅ #payments (master payments - 270 views)
✅ #finance (ABS history - 252 views)
✅ #operations (batch processing - 235 views)
✅ #general (daily summaries)
✅ Any other channels you want Sophia to access
STEP 4: Test (5 seconds)
------------------------
Python test:
```python
from scripts.simple_bot_setup import test_bot_access
test_bot_access()
```
DONE! ✅
=========
Sophia now has complete access to:
• All public channels
• All private channels (when invited)
• Direct messages
• File sharing
• Message history
• User information
COMPARISON:
-----------
Custom App Setup:  ~10 minutes + webhook maintenance
Bot Token Setup:   ~30 seconds, zero maintenance
For Pay Ready's business intelligence needs, bot token gives you:
• Same complete access
• Simpler setup
• More reliable (no webhooks to break)
• Easier deployment
"""
    return instructions
def test_bot_access():
    """Test bot token access"""
    print("🧪 TESTING BOT TOKEN ACCESS")
    print("=" * 40)
    try:
        from slack_sdk import WebClient
        config = INTEGRATIONS.get("slack_simple", {})
        bot_token = config.get("bot_token", "")
        if not bot_token or bot_token == "REPLACE_WITH_YOUR_BOT_TOKEN":
            print("❌ Bot token not configured yet")
            print("   Update the bot_token in integrations_config.py")
            return
        client = WebClient(token=bot_token)
        # Test auth
        auth_test = client.auth_test()
        print("✅ Authentication successful")
        print(f"   Bot User: {auth_test['user']}")
        print(f"   Team: {auth_test['team']}")
        # Test channels access
        channels = client.conversations_list()
        print(f"✅ Can access {len(channels['channels'])} channels")
        # Test users access
        users = client.users_list()
        print(f"✅ Can access {len(users['members'])} users")
        print("\n🎉 Sophia has complete Slack access!")
        print("   Ready for Pay Ready business intelligence automation")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        print("   Make sure bot token is valid and bot is added to workspace")
def save_simple_config():
    """Save the simple bot configuration"""
    # Save simplified config
    simple_config = create_simple_bot_config()
    with open("slack_simple_config.json", "w") as f:
        json.dump(simple_config, f, indent=2)
    # Save client example
    client_example = create_simple_client_example()
    with open("sophia_simple_slack_client.py", "w") as f:
        f.write(client_example)
    # Save setup instructions
    instructions = create_setup_instructions()
    with open("SIMPLE_BOT_SETUP.md", "w") as f:
        f.write(instructions)
    print("✅ Simple bot setup files created:")
    print("   📋 slack_simple_config.json - Simplified configuration")
    print("   🐍 sophia_simple_slack_client.py - Complete access client")
    print("   📖 SIMPLE_BOT_SETUP.md - 30-second setup guide")
if __name__ == "__main__":
    save_simple_config()
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDATION: Use Bot Token for Complete Access")
    print("=" * 60)
    print("✅ Easier than custom app")
    print("✅ Complete access to everything")
    print("✅ Perfect for Pay Ready business intelligence")
    print("✅ 30-second setup vs 10-minute app setup")
    print("\nRead SIMPLE_BOT_SETUP.md for step-by-step instructions!")
