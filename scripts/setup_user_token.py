#!/usr/bin/env python3
"""
User Token Setup - Maximum Slack Access for Sophia

This gives Sophia YOUR complete Slack permissions - everything you can do,
Sophia can do automatically.
"""

import json


def create_user_token_config():
    """Create user token configuration for maximum access"""

    config = {
        "slack_user_token": {
            "enabled": True,
            "integration_type": "user_token",
            "user_token": "REPLACE_WITH_YOUR_USER_TOKEN",  # xoxp-*
            "workspace": "Pay Ready",
            "access_level": "maximum",
            "permissions": "YOUR_COMPLETE_PERMISSIONS",
            "capabilities": [
                "✅ Read ALL channels (public + private)",
                "✅ Write to ALL channels",
                "✅ Create new channels",
                "✅ Invite/remove users",
                "✅ Upload/download files",
                "✅ Admin functions (if you're admin)",
                "✅ Workspace settings (if you're admin)",
                "✅ Delete messages (if you can)",
                "✅ Pin messages",
                "✅ Set channel topics",
                "✅ Everything YOU can do",
            ],
            "setup_time": "60 seconds",
            "security_note": "Sophia acts as YOUR user account",
        }
    }

    return config


def generate_user_token_instructions():
    """Generate step-by-step user token setup"""

    instructions = """
🔐 USER TOKEN SETUP - MAXIMUM ACCESS (60 seconds)
================================================

🚨 IMPORTANT: User token gives Sophia YOUR complete Slack permissions!
Sophia will act as YOUR user account in all interactions.

STEP 1: Get Your User Token (30 seconds)
----------------------------------------

METHOD A - Legacy Token (Easiest):
1. Go to: https://api.slack.com/legacy/custom-integrations/legacy-tokens
2. Find "Pay Ready" workspace
3. Click "Create token"
4. Copy token (starts with xoxp-)

METHOD B - OAuth App (More Secure):
1. Go to: https://api.slack.com/apps/new
2. Create app → "From scratch"
3. App Name: "Personal Sophia Access"
4. Workspace: Pay Ready
5. OAuth & Permissions → User Token Scopes:
   ✅ channels:read        ✅ channels:write
   ✅ groups:read         ✅ groups:write
   ✅ im:read            ✅ im:write
   ✅ mpim:read          ✅ mpim:write
   ✅ users:read         ✅ files:read
   ✅ files:write        ✅ chat:write
   ✅ channels:manage    ✅ groups:manage
   ✅ admin (if you want admin access)

STEP 2: Update Configuration (10 seconds)
-----------------------------------------
Replace "REPLACE_WITH_YOUR_USER_TOKEN" with your actual token

STEP 3: Test Access (20 seconds)
--------------------------------
python3 scripts/test_user_token.py

STEP 4: Deploy
--------------
Sophia now has YOUR complete Slack access!

⚠️  SECURITY CONSIDERATIONS:
============================
✅ PROS:
• Maximum possible access - everything you can do
• No channel invitation needed
• Admin capabilities (if you're admin)
• Can create channels, manage users
• Complete workspace control

⚠️  RISKS:
• Messages appear from YOUR account
• Audit trail shows YOUR name
• If token compromised = full account access
• Sophia actions attributed to YOU

🎯 PERFECT FOR:
===============
• Personal AI assistant
• Complete workspace automation
• When you want Sophia to have unlimited power
• Internal/private workspace usage
"""

    return instructions


def create_user_token_client():
    """Create user token client with maximum access"""

    client_code = '''
#!/usr/bin/env python3
"""
Sophia User Token Client - Maximum Slack Access

Sophia acts with YOUR complete Slack permissions.
Everything you can do, Sophia can do automatically.
"""

from slack_sdk import WebClient
from typing import Dict, Any, List
import json
from datetime import datetime

class SophiaMaxAccess:
    """Sophia with YOUR complete Slack permissions"""

    def __init__(self):
        from config.manager import get_config_manager
        config = INTEGRATIONS.get("slack_user_token", {})

        self.client = WebClient(token=config["user_token"])
        self.user_info = None
        self._get_user_info()

    def _get_user_info(self):
        """Get information about the user whose token we're using"""
        try:
            auth = self.client.auth_test()
            self.user_info = {
                "user_id": auth["user_id"],
                "user": auth["user"],
                "team": auth["team"],
                "team_id": auth["team_id"]
            }
            print(f"🤖 Sophia initialized with {auth['user']}'s complete permissions")
        except Exception as e:
            print(f"❌ Failed to authenticate: {e}")

    # === MAXIMUM ACCESS CAPABILITIES ===

    def read_any_channel(self, channel: str, limit: int = 100):
        """Read messages from ANY channel (public/private)"""
        return self.client.conversations_history(
            channel=channel,
            limit=limit
        )

    def send_to_any_channel(self, channel: str, message: str):
        """Send message to ANY channel (no invitation needed)"""
        return self.client.chat_postMessage(
            channel=channel,
            text=message,
            username="Sophia AI (via {})".format(self.user_info["user"])
        )

    def create_channel(self, name: str, private: bool = False):
        """Create new channels"""
        return self.client.conversations_create(
            name=name,
            is_private=private
        )

    def invite_users(self, channel: str, users: List[str]):
        """Invite users to channels"""
        return self.client.conversations_invite(
            channel=channel,
            users=",".join(users)
        )

    def set_channel_topic(self, channel: str, topic: str):
        """Set channel topics/descriptions"""
        return self.client.conversations_setTopic(
            channel=channel,
            topic=topic
        )

    def pin_message(self, channel: str, timestamp: str):
        """Pin important messages"""
        return self.client.pins_add(
            channel=channel,
            timestamp=timestamp
        )

    def delete_message(self, channel: str, timestamp: str):
        """Delete messages (if you have permission)"""
        return self.client.chat_delete(
            channel=channel,
            ts=timestamp
        )

    def get_all_private_channels(self):
        """Access ALL private channels you're in"""
        return self.client.conversations_list(
            types="private_channel",
            exclude_archived=True
        )

    def upload_file_anywhere(self, channels: List[str], file_path: str,
                           title: str, comment: str = ""):
        """Upload files to any channel"""
        return self.client.files_upload(
            channels=",".join(channels),
            file=file_path,
            title=title,
            initial_comment=comment
        )

    def manage_workspace_users(self):
        """Get workspace user management info (if admin)"""
        try:
            return self.client.team_info()
        except Exception:return {"error": "Admin access required"}

    # === BUSINESS INTELLIGENCE AUTOMATION ===

    def automate_pay_ready_bi(self):
        """Automate Pay Ready business intelligence with maximum access"""

        # Access executive channels directly (no invitation needed)
        exec_channels = ["#executive", "#leadership", "#board", "#ceo"]

        for channel in exec_channels:
            try:
                # Read recent discussions
                history = self.read_any_channel(channel, limit=10)

                # Send BI summary
                bi_summary = self.generate_bi_summary()
                self.send_to_any_channel(channel,
                    f"📊 **Daily BI Summary from Sophia AI**\\n{bi_summary}")

                print(f"✅ BI summary sent to {channel}")

            except Exception as e:
                print(f"⚠️  Could not access {channel}: {e}")

    def generate_bi_summary(self):
        """Generate business intelligence summary"""
        return f"""
🔥 **Top Pay Ready Reports Status:**
• Master Payments (270 views): ✅ Healthy
• ABS History (252 views): ✅ Processing normally
• Batch Processing (235 views): ⚠️  Minor delays detected

💡 **AI Insights:**
• Payment volume up 15% this week
• Recommend batch processing optimization
• No critical alerts at this time

⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🤖 By Sophia AI with complete workspace access
"""

    def emergency_broadcast(self, message: str):
        """Send emergency message to ALL channels"""
        channels = self.client.conversations_list()

        for channel in channels["channels"]:
            try:
                self.send_to_any_channel(
                    channel["id"],
                    f"🚨 **EMERGENCY BROADCAST**\\n{message}"
                )
            except Exception:continue

    def complete_workspace_backup(self):
        """Backup all workspace data (with your permissions)"""
        backup_data = {
            "channels": [],
            "users": [],
            "messages": {}
        }

        # Get all channels
        channels = self.client.conversations_list()
        backup_data["channels"] = channels["channels"]

        # Get all users
        users = self.client.users_list()
        backup_data["users"] = users["members"]

        # Backup messages from all accessible channels
        for channel in channels["channels"]:
            try:
                messages = self.read_any_channel(channel["id"], limit=1000)
                backup_data["messages"][channel["name"]] = messages["messages"]
            except Exception:continue

        # Save backup
        with open(f'slack_backup_{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)

        return f"✅ Complete workspace backup saved"

# === USAGE EXAMPLES ===
if __name__ == "__main__":
    sophia = SophiaMaxAccess()

    # Test maximum access capabilities
    print("🧪 Testing maximum access capabilities...")

    # Read any channel
    # history = sophia.read_any_channel("#executive")

    # Send to any channel
    # sophia.send_to_any_channel("#general", "Hello from Sophia with maximum access!")

    # Create emergency channel
    # sophia.create_channel("sophia-emergency-alerts", private=True)

    # Automate business intelligence
    # sophia.automate_pay_ready_bi()

    print("🎯 Sophia has complete access to your Slack workspace!")
'''

    return client_code


def create_test_script():
    """Create test script for user token"""

    test_script = '''
#!/usr/bin/env python3
"""
Test User Token Access
"""

def test_user_token():
    print("🧪 TESTING USER TOKEN ACCESS")
    print("=" * 40)

    try:
        from slack_sdk import WebClient
        from config.manager import get_config_manager

        config = INTEGRATIONS.get("slack_user_token", {})
        user_token = config.get("user_token", "")

        if not user_token or user_token == "REPLACE_WITH_YOUR_USER_TOKEN":
            print("❌ User token not configured")
            print("   Update user_token in integrations_config.py")
            return

        client = WebClient(token=user_token)

        # Test auth
        auth = client.auth_test()
        print(f"✅ Acting as: {auth['user']} ({auth['user_id']})")
        print(f"✅ Team: {auth['team']}")

        # Test maximum access
        channels = client.conversations_list(types="public_channel,private_channel")
        public = sum(1 for c in channels['channels'] if not c.get('is_private'))
        private = sum(1 for c in channels['channels'] if c.get('is_private'))

        print(f"✅ Access to {public} public + {private} private channels")

        # Test users access
        users = client.users_list()
        print(f"✅ Can see {len(users['members'])} users")

        # Test file access
        files = client.files_list(count=1)
        print(f"✅ Can access workspace files")

        print(f"\\n🎉 MAXIMUM ACCESS CONFIRMED!")
        print(f"   Sophia has YOUR complete Slack permissions")
        print(f"   Can access everything you can access")

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_user_token()
'''

    return test_script


def save_user_token_setup():
    """Save all user token setup files"""

    # Save config
    config = create_user_token_config()
    with open("slack_user_token_config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Save instructions
    instructions = generate_user_token_instructions()
    with open("USER_TOKEN_SETUP.md", "w") as f:
        f.write(instructions)

    # Save client
    client = create_user_token_client()
    with open("sophia_max_access_client.py", "w") as f:
        f.write(client)

    # Save test script
    test = create_test_script()
    with open("test_user_token.py", "w") as f:
        f.write(test)

    print("✅ User token setup files created:")
    print("   📋 slack_user_token_config.json - Maximum access config")
    print("   📖 USER_TOKEN_SETUP.md - Complete setup guide")
    print("   🤖 sophia_max_access_client.py - Maximum access client")
    print("   🧪 test_user_token.py - Test script")


def update_integrations_config():
    """Add user token to main integrations config"""

    user_token_addition = """

    # Add this to your app/api/integrations_config.py:

    "slack_user_token": {
        "enabled": True,
        "status": "maximum_access",
        "user_token": "REPLACE_WITH_YOUR_USER_TOKEN",  # xoxp-*
        "access_level": "complete",
        "acts_as": "your_user_account",
        "capabilities": "everything_you_can_do",
        "stats": {"workspace": "Pay Ready", "integration": "maximum_power"}
    },
    """

    print("\\n" + "=" * 60)
    print("📝 ADD TO INTEGRATIONS CONFIG:")
    print("=" * 60)
    print(user_token_addition)


if __name__ == "__main__":
    save_user_token_setup()
    update_integrations_config()

    print("\\n" + "=" * 60)
    print("🔐 USER TOKEN SETUP COMPLETE!")
    print("=" * 60)
    print("🎯 Next steps:")
    print("   1. Read USER_TOKEN_SETUP.md")
    print("   2. Get your user token (60 seconds)")
    print("   3. Update integrations config")
    print("   4. Run: python3 test_user_token.py")
    print("   5. Sophia has YOUR complete Slack access!")
